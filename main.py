"""
GANZA AI - Main Server (Updated)
Fixed: Async Generator 'strip' error & Graceful Interruption Handling.
GROK FIX: Added state machine, local VAD, transcript queue, and time-based interruption.
INTERRUPT FIX: Added flush signal to frontend when interruption occurs.
"""

import asyncio
import json
import time
from enum import Enum
from typing import Optional, List, Tuple
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import GanzaConfig
from services.transcription import TranscriptionService
from services.llm import LLMService
from services.tts import TTSService
from services.local_vad import LocalVADService

app = FastAPI(
    title=GanzaConfig.APP_NAME,
    version=GanzaConfig.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class State(Enum):
    """GROK FIX: Explicit state machine for turn-taking"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"

class ConnectionState:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.transcription_service: Optional[TranscriptionService] = None
        self.llm_service: Optional[LLMService] = None
        self.tts_service: Optional[TTSService] = None
        self.local_vad: Optional[LocalVADService] = None  # GROK FIX: Local VAD

        # GROK FIX: State machine
        self.state = State.IDLE

        self.conversation_history = []
        self.current_response_task: Optional[asyncio.Task] = None
        self.is_responding = False  # Legacy - kept for compatibility
        self.should_stop = False
        self.interrupted = False
        self.ai_speech_start_time = 0.0
        self.response_start_time = 0.0  # GROK FIX: Track when AI started responding
        self.last_final_transcript_time = 0.0
        self.response_started = False

        # GROK FIX: Transcript queue - NEVER discard transcripts during response
        self.transcript_queue: List[Tuple[str, float]] = []  # (text, timestamp)

        # GROK FIX: Local VAD state
        self.local_vad_speaking = False

        # CLAUDE FIX: Debouncing state for interruption detection
        self.user_speech_start_time = 0.0         # When user started speaking (0 = not speaking)
        self.is_user_speaking = False             # True if user is currently speaking

        # CLAUDE FIX: Interruption state machine (VAD Fix)
        self.is_interrupting = False              # True when interruption is in progress
        self.interruption_triggered_time = 0.0    # When interruption was triggered
        self.interruption_cooldown_duration = 1.0  # How long to ignore transcripts after interruption
        self.POST_INTERRUPTION_SILENCE = 0.8      # Require silence after interruption before responding

        # GROK FIX: Configuration
        self.DEBOUNCE_THRESHOLD = 0.2             # 200ms - require sustained speech to interrupt
        self.INTERRUPTION_COOLDOWN = 0.5          # 500ms - time after user's last speech before allowing interrupts
        self.CONTINUATION_WINDOW = 3.0            # GROK FIX: 3 seconds - if transcript arrives within this, likely continuation

        # CLAUDE FIX: Response delay (prevents AI from cutting off user mid-sentence)
        self.response_delay_duration = 0.8        # Wait 800ms after final transcript before responding
        self.response_delay_task: Optional[asyncio.Task] = None
        self.pending_user_text = ""               # Accumulate text from multiple transcripts during delay

    async def initialize_services(self):
        try:
            event_loop = asyncio.get_event_loop()

            # GROK FIX: Initialize local VAD with VADIterator
            # LLM Analysis Fix: VADIterator handles variable chunks, no forced buffering
            try:
                self.local_vad = LocalVADService(
                    sample_rate=16000,
                    threshold=0.5,
                    min_silence_duration_ms=500  # Recommended: 500ms (not 200ms)
                )
                self.local_vad.set_callbacks(
                    on_speech_start=self._on_local_vad_speech_start,
                    on_speech_end=self._on_local_vad_speech_end
                )
                print("✅ Local VAD initialized")
            except Exception as e:
                print(f"⚠️ Local VAD initialization failed: {e}")
                print("⚠️ Continuing with Deepgram-only VAD")
                self.local_vad = None

            self.transcription_service = TranscriptionService(event_loop=event_loop)
            self.llm_service = LLMService(
                provider=GanzaConfig.LLM_PROVIDER,
                model=GanzaConfig.get_llm_model(),
            )
            self.tts_service = TTSService(
                provider=GanzaConfig.TTS_PROVIDER,
                voice_id=GanzaConfig.VOICE_ID,
            )

            self.transcription_service.set_callbacks(
                on_final=self._on_final_transcript,
                on_interim=self._on_interim_transcript,
                on_vad_start=self._on_user_speaking,
                on_vad_end=self._on_user_stopped,
            )

            if not await self.transcription_service.start():
                raise Exception("Failed to start transcription service")

            # GROK FIX: Start in LISTENING state
            self.state = State.LISTENING

            print("✅ All services initialized")
            return True
        except Exception as e:
            print(f"❌ Initialization error: {e}")
            return False

    async def _on_local_vad_speech_start(self):
        """GROK FIX: Local VAD detected speech start"""
        self.local_vad_speaking = True
        print("🎤 Local VAD: Speech detected")

        # If AI is speaking, interrupt immediately
        if self.state == State.SPEAKING:
            print("🛑 Local VAD: Interrupting AI response")
            await self._interrupt_ai_response()

    async def _on_local_vad_speech_end(self):
        """GROK FIX: Local VAD detected speech end"""
        self.local_vad_speaking = False
        print("🔇 Local VAD: Speech ended")

    async def _on_user_speaking(self):
        """VAD callback: User started speaking (legacy - kept for compatibility)."""
        # This is called by VAD events, but debouncing is now handled in _on_interim_transcript
        # Keep for backward compatibility but actual logic is in _on_interim_transcript
        pass

    async def _on_user_stopped(self):
        """VAD callback: User stopped speaking."""
        # Reset debouncing state when user stops
        self.user_speech_start_time = 0.0
        self.is_user_speaking = False

    async def _on_interim_transcript(self, text: str):
        """
        CLAUDE FIX: Handle interim transcripts with proper debouncing.
        Checks timer on EVERY interim transcript (not just first call).
        """
        # Ignore empty transcripts (might be noise or silence)
        if not text.strip():
            return

        current_time = time.time()

        # CLAUDE FIX: Ignore transcripts during interruption window
        if self.is_interrupting:
            time_since_interrupt = current_time - self.interruption_triggered_time
            if time_since_interrupt < self.interruption_cooldown_duration:
                print(f"⏸️ Ignoring interim during interruption cooldown ({time_since_interrupt:.2f}s / {self.interruption_cooldown_duration}s): '{text[:30]}...'")
                return
            else:
                # Cooldown expired - clear interruption state
                print(f"✓ Interruption cooldown expired ({time_since_interrupt:.2f}s)")
                self.is_interrupting = False

        # Only consider interrupting if AI is actively responding
        if not self.is_responding or not self.response_started:
            return

        # CLAUDE FIX: Check cooldown period (prevent interrupting too soon after user's last speech)
        time_since_last_transcript = current_time - self.last_final_transcript_time
        if time_since_last_transcript < self.INTERRUPTION_COOLDOWN:
            # Too soon after user's last speech - ignore
            return

        # CLAUDE FIX: DEBOUNCING LOGIC - Start timer if this is the first detection
        if self.user_speech_start_time == 0:
            self.user_speech_start_time = current_time
            self.is_user_speaking = True
            print(f"🎤 User speech detected (interim: '{text[:30]}...'), starting debounce timer")
            return  # Don't interrupt yet - wait for sustained speech

        # CLAUDE FIX: Check if user has been speaking long enough (on EVERY interim)
        speech_duration = current_time - self.user_speech_start_time

        if speech_duration >= self.DEBOUNCE_THRESHOLD:
            # User has been speaking for ≥200ms - this is a real interruption!
            if not self.should_stop and not self.is_interrupting:  # Only log once
                print(f"🛑 USER INTERRUPTION CONFIRMED (sustained {speech_duration:.2f}s, interim: '{text[:30]}...')")
                await self._interrupt_ai_response()
        else:
            # Still building up - not enough time yet
            print(f"⏳ User speaking for {speech_duration:.2f}s (need {self.DEBOUNCE_THRESHOLD}s, interim: '{text[:20]}...')")

    async def _on_final_transcript(self, text: str):
        """GROK FIX: Handle final transcripts with queue system and time-based interruption."""
        if not text.strip():
            return

        current_time = time.time()

        # GROK FIX: Check if transcript arrived too soon after interruption
        ignore_window = max(self.interruption_cooldown_duration, self.POST_INTERRUPTION_SILENCE)

        if self.interruption_triggered_time > 0:
            time_since_interrupt = current_time - self.interruption_triggered_time

            if time_since_interrupt < ignore_window:
                print(f"⏸️ Ignoring FINAL transcript ({time_since_interrupt:.2f}s < {ignore_window:.2f}s after interruption): '{text[:50]}...'")
                self.last_final_transcript_time = current_time
                self.user_speech_start_time = 0.0
                self.is_user_speaking = False
                return

            # Enough time has passed - clear interruption state
            print(f"✓ Ignore window expired ({time_since_interrupt:.2f}s), clearing interruption state")
            self.is_interrupting = False
            self.interruption_triggered_time = 0.0

        # Update timing
        self.last_final_transcript_time = current_time

        # GROK FIX: Check if user was speaking before resetting state
        user_was_speaking = self.user_speech_start_time > 0
        time_since_speech_start = current_time - self.user_speech_start_time if user_was_speaking else 0

        # Reset debouncing state
        self.user_speech_start_time = 0.0
        self.is_user_speaking = False

        print(f"✓ Final transcript: '{text}'")

        # GROK FIX: If AI is speaking, use queue system + time-based interruption
        if self.state == State.SPEAKING or self.is_responding:
            # Calculate time since AI started responding
            time_since_response_start = current_time - self.response_start_time if self.response_start_time > 0 else float('inf')

            # GROK FIX: Time-based interruption - within 3 seconds = likely continuation
            is_continuation = time_since_response_start < self.CONTINUATION_WINDOW
            # CLAUDE FIX: Use is_user_speaking() directly instead of flag (more reliable)
            has_local_vad_speech = self.local_vad.is_user_speaking() if self.local_vad else False
            has_interim_speech = user_was_speaking and time_since_speech_start >= self.DEBOUNCE_THRESHOLD

            # Interrupt if: continuation window OR local VAD detected speech OR interim speech confirmed
            if is_continuation or has_local_vad_speech or has_interim_speech:
                print(f"🛑 Interrupting AI response (continuation={is_continuation}, local_vad={has_local_vad_speech}, interim={has_interim_speech})")
                await self._interrupt_ai_response()
                # Queue this transcript for processing
                self.transcript_queue.append((text, current_time))
                # Process queue immediately after interruption
                await self._process_transcript_queue()
            else:
                # GROK FIX: Queue for processing after response finishes
                self.transcript_queue.append((text, current_time))
                print(f"📥 Queued transcript (AI responding, will process after): '{text[:50]}...'")
            return

        # GROK FIX: If processing, queue it
        if self.state == State.PROCESSING:
            self.transcript_queue.append((text, current_time))
            print(f"📥 Queued transcript (AI processing): '{text[:50]}...'")
            return

        # GROK FIX: Normal flow - cancel existing delay task if any
        if self.response_delay_task and not self.response_delay_task.done():
            print(f"🔄 Transcript arrived during delay, restarting timer")
            self.response_delay_task.cancel()
            try:
                await self.response_delay_task
            except asyncio.CancelledError:
                pass

        # Accumulate text (user might send multiple transcripts)
        if self.pending_user_text:
            self.pending_user_text += " " + text
        else:
            self.pending_user_text = text

        # Start new delay task
        print(f"⏳ Starting response delay ({self.response_delay_duration}s) for: '{text[:50]}...'")
        self.response_delay_task = asyncio.create_task(
            self._delayed_response()
        )

    async def _process_transcript_queue(self):
        """GROK FIX: Process all queued transcripts"""
        if not self.transcript_queue:
            return

        # BUG FIX: Check if already processing/speaking - don't start another response
        if self.state == State.PROCESSING or self.state == State.SPEAKING:
            print(f"⚠️ Already processing or speaking, deferring queue processing. Current State: {self.state.value}")
            return

        # Combine all queued transcripts
        combined_text = " ".join([text for text, _ in self.transcript_queue])
        self.transcript_queue = []

        print(f"📤 Processing queued transcripts: '{combined_text[:50]}...'")

        # Update conversation history
        print(f"👤 User: {combined_text}")
        self.conversation_history.append({"role": "user", "content": combined_text})

        if len(self.conversation_history) > GanzaConfig.MAX_HISTORY_LENGTH:
            self.conversation_history = self.conversation_history[-GanzaConfig.MAX_HISTORY_LENGTH:]

        # Clear interruption state
        self.is_interrupting = False
        self.interruption_triggered_time = 0.0

        # BUG FIX: Don't set state to PROCESSING here - let _generate_and_stream_response() handle it
        # Setting it here causes _generate_and_stream_response() to return immediately (line 428-429)
        # Just ensure we're in LISTENING state
        if self.state != State.LISTENING:
            self.state = State.LISTENING

        # Start AI response
        self.should_stop = False
        self.response_started = False
        self.current_response_task = asyncio.create_task(
            self._generate_and_stream_response(combined_text)
        )

    async def _interrupt_ai_response(self):
        """
        GROK FIX: Interrupt the AI's current response.
        Stops TTS immediately, clears audio queue, maintains context.
        INTERRUPT FIX: Sends flush signal to frontend.
        """
        if self.state != State.SPEAKING and not self.is_responding:
            # Already stopped or not responding
            return

        print("🛑 Interrupting AI response...")

        # GROK FIX: Enter interruption state
        self.is_interrupting = True
        self.interruption_triggered_time = time.time()

        # GROK FIX: Set flag to stop TTS streaming immediately
        self.should_stop = True

        # INTERRUPT FIX: Send interrupt signal to frontend to flush audio queue
        try:
            interrupt_signal = json.dumps({
                "type": "interrupt",
                "action": "flush_audio",
                "timestamp": time.time(),
                "state": self.state.value
            })
            await self.websocket.send_text(interrupt_signal)
            print("📤 Sent interrupt signal to frontend")
        except Exception as e:
            print(f"⚠️ Failed to send interrupt signal: {e}")
            # Non-critical - interruption continues

        # Cancel the response task if it exists and is running
        if self.current_response_task and not self.current_response_task.done():
            self.current_response_task.cancel()
            try:
                await self.current_response_task
            except asyncio.CancelledError:
                print("✓ Response task cancelled successfully")
            except Exception as e:
                print(f"⚠️ Error during task cancellation: {e}")

        # GROK FIX: State transition - SPEAKING -> LISTENING
        self.state = State.LISTENING
        self.is_responding = False
        self.response_started = False

        # Reset debouncing state
        self.user_speech_start_time = 0.0
        self.is_user_speaking = False

        # Cancel response delay task if any
        if self.response_delay_task and not self.response_delay_task.done():
            self.response_delay_task.cancel()
            self.pending_user_text = ""
            try:
                await self.response_delay_task
            except asyncio.CancelledError:
                pass

        print(f"✓ Interruption complete, cooling down for {self.interruption_cooldown_duration}s")

    async def _delayed_response(self):
        """
        CLAUDE FIX: Wait for response_delay_duration, then start response.

        If another transcript arrives during this delay, this task will be cancelled
        and a new one started. This ensures the user is truly done speaking before
        the AI responds.
        """
        try:
            # Wait for the delay
            await asyncio.sleep(self.response_delay_duration)

            # Delay expired - user is truly done!
            if self.pending_user_text and not self.is_responding:
                text_to_respond = self.pending_user_text
                self.pending_user_text = ""

                print(f"✅ Response delay expired, starting response to: '{text_to_respond[:50]}...'")

                # Update conversation history
                print(f"👤 User: {text_to_respond}")
                self.conversation_history.append({"role": "user", "content": text_to_respond})

                if len(self.conversation_history) > GanzaConfig.MAX_HISTORY_LENGTH:
                    self.conversation_history = self.conversation_history[-GanzaConfig.MAX_HISTORY_LENGTH:]

                # Clear interruption state when starting new response
                self.is_interrupting = False
                self.interruption_triggered_time = 0.0

                # Start AI response
                self.should_stop = False
                self.response_started = False
                self.current_response_task = asyncio.create_task(
                    self._generate_and_stream_response(text_to_respond)
                )

        except asyncio.CancelledError:
            # Cancelled because new transcript arrived
            print(f"❌ Response delay cancelled (new transcript arrived)")
            raise

    async def _generate_and_stream_response(self, user_text: str):
        """GROK FIX: Generate and stream response with state machine updates."""
        if self.is_responding or self.state == State.PROCESSING:
            return

        # GROK FIX: State transition - LISTENING -> PROCESSING
        self.state = State.PROCESSING
        self.is_responding = True
        self.response_started = False
        self.interrupted = False
        assistant_response = ""

        try:
            print("🧠 Generating response...")

            async def token_stream():
                nonlocal assistant_response
                async for token in self.llm_service.stream_response(
                    user_text,
                    self.conversation_history[:-1],
                    GanzaConfig.SYSTEM_PROMPT,
                    temperature=GanzaConfig.LLM_TEMPERATURE,
                    max_tokens=GanzaConfig.LLM_MAX_TOKENS,
                ):
                    if self.should_stop: break
                    if token:
                        if not self.response_started: self.response_started = True
                        assistant_response += token
                        yield token

            # GROK FIX: State transition - PROCESSING -> SPEAKING
            self.state = State.SPEAKING
            self.response_start_time = time.time()  # Track when AI started speaking

            await self.process_response_stream(token_stream())

            if assistant_response and not self.interrupted:
                # Strip the full text for history
                full_content = assistant_response.strip()
                self.conversation_history.append({
                    "role": "assistant",
                    "content": full_content
                })
                print(f"🤖 AI: {full_content[:50]}...")

        except asyncio.CancelledError:
            print("🛑 Task Cancelled")
        except Exception as e:
            print(f"❌ Error in response generation: {e}")
        finally:
            # BUG FIX: Always transition to LISTENING first, then process queue
            # This ensures _process_transcript_queue() doesn't return early due to state check
            self.state = State.LISTENING
            self.is_responding = False

            # GROK FIX: Check if we have queued transcripts to process
            if self.transcript_queue:
                print(f"📥 Processing {len(self.transcript_queue)} queued transcript(s) after response")
                await self._process_transcript_queue()

    async def process_response_stream(self, text_generator):
        try:
            await self.run_ai_response_stream(text_generator)
        except Exception as e:
            print(f"❌ Stream processing error: {e}")

    async def run_ai_response_stream(self, text_generator):
        """
        GROK FIX: Gracefully handles the audio flow and interruptions.
        Stops TTS immediately when interrupted.
        """
        self.ai_speech_start_time = time.time()
        try:
            async for audio_chunk in self.tts_service.synthesize_stream(
                text_generator,
                should_stop_check=lambda: self.should_stop
            ):
                if self.should_stop:
                    self.interrupted = True
                    print("🛑 TTS stream stopped (interrupted)")
                    break

                if audio_chunk:
                    await self.websocket.send_bytes(audio_chunk)

        except (asyncio.CancelledError, GeneratorExit):
            print("👋 Stream stopped gracefully.")
        except Exception as e:
            print(f"❌ Unexpected error in audio stream: {e}")
        finally:
            # State will be updated in _generate_and_stream_response finally block
            pass

    def cleanup(self):
        """Clean shutdown of all resources"""
        try:
            if self.transcription_service:
                self.transcription_service.stop()
            if self.current_response_task and not self.current_response_task.done():
                self.current_response_task.cancel()
            # CLAUDE FIX: Cancel response delay task
            if self.response_delay_task and not self.response_delay_task.done():
                self.response_delay_task.cancel()
        except Exception as e:
            print(f"⚠️ Cleanup error (non-critical): {e}")

@app.websocket("/ws/audio")
async def audio_pipeline(websocket: WebSocket):
    await websocket.accept()
    print("🔌 User Connected")
    state = ConnectionState(websocket)
    if not await state.initialize_services():
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_bytes()

            # GROK FIX: Process audio through local VAD first
            if state.local_vad:
                await state.local_vad.process_audio(data)

            # Send to Deepgram for transcription
            if state.transcription_service:
                state.transcription_service.send_audio(data)
    except WebSocketDisconnect:
        print("🔌 Disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        state.cleanup()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=GanzaConfig.HOST, port=GanzaConfig.PORT)
