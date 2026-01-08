"""
Complete Integration Guide - How to Use Everything Together
============================================================

This file shows EXACTLY how to integrate:
1. TTSService (from tts_complete.py)
2. ConnectionState (from connection_state_complete.py)
3. FastAPI WebSocket handler
4. Deepgram integration
5. OpenAI/LLM integration

Copy-paste the relevant sections into your main.py

Author: Claude
Date: 2026-01-08
"""

# ===== FILE STRUCTURE =====
#
# Your project should have:
# /services/
#   tts.py          ← Copy TTSService from tts_complete.py
#   transcription.py ← Your existing Deepgram service
#   llm.py          ← Your LLM service
#
# main.py           ← WebSocket handler (shown below)
# config.py         ← Configuration
#

# ===== STEP 1: Update config.py =====

# Add these to your config.py:
"""
# TTS Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "default_voice_id")

# Buffer thresholds (optional - using defaults if not specified)
TTS_SENTENCE_MIN = int(os.getenv("TTS_SENTENCE_MIN", "15"))
TTS_MIN_WEAK_BUFFER = int(os.getenv("TTS_MIN_WEAK_BUFFER", "40"))
TTS_HARD_MAX_BUFFER = int(os.getenv("TTS_HARD_MAX_BUFFER", "120"))

# Interruption configuration
DEBOUNCE_THRESHOLD = float(os.getenv("DEBOUNCE_THRESHOLD", "0.3"))
INTERRUPTION_COOLDOWN = float(os.getenv("INTERRUPTION_COOLDOWN", "0.5"))
"""


# ===== STEP 2: Complete main.py Implementation =====

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import time
from typing import Optional, AsyncGenerator

# Import your services
from services.tts import TTSService
from services.transcription import DeepgramService
from services.llm import OpenAIService
import config

app = FastAPI()


class ConnectionState:
    """
    Complete ConnectionState implementation.

    COPY THIS CLASS from connection_state_complete.py
    OR import it if you prefer.
    """

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

        # Response state
        self.should_stop = False
        self.is_responding = False
        self.response_started = False
        self.current_response_task: Optional[asyncio.Task] = None

        # Timing state
        self.last_final_transcript_time = 0.0

        # Debouncing state
        self.user_speech_start_time = 0.0
        self.is_user_speaking = False

        # Configuration
        self.DEBOUNCE_THRESHOLD = config.DEBOUNCE_THRESHOLD
        self.INTERRUPTION_COOLDOWN = config.INTERRUPTION_COOLDOWN

    async def _on_interim_transcript(self, text: str):
        """Handle interim transcripts with debouncing."""
        if not text.strip():
            return

        if not self.is_responding or not self.response_started:
            return

        current_time = time.time()

        # Check cooldown
        time_since_last_transcript = current_time - self.last_final_transcript_time
        if time_since_last_transcript < self.INTERRUPTION_COOLDOWN:
            return

        # Debouncing logic
        if self.user_speech_start_time == 0:
            self.user_speech_start_time = current_time
            self.is_user_speaking = True
            print(f"🎤 User speech detected: '{text[:30]}...'")
            return

        speech_duration = current_time - self.user_speech_start_time

        if speech_duration >= self.DEBOUNCE_THRESHOLD:
            if not self.should_stop:
                print(f"🛑 INTERRUPTION CONFIRMED ({speech_duration:.2f}s)")
                await self._interrupt_ai_response()
        else:
            print(f"⏳ Debouncing: {speech_duration:.2f}s / {self.DEBOUNCE_THRESHOLD}s")

    async def _on_final_transcript(self, text: str):
        """Handle final transcripts."""
        if not text.strip():
            return

        current_time = time.time()
        self.last_final_transcript_time = current_time

        # Reset debouncing
        self.user_speech_start_time = 0.0
        self.is_user_speaking = False

        print(f"✓ Final: '{text}'")

        # Process transcript if not responding
        if not self.is_responding:
            await self.start_ai_response(text)

    async def _interrupt_ai_response(self):
        """Interrupt current AI response."""
        if not self.is_responding:
            return

        print("🛑 Interrupting AI...")
        self.should_stop = True

        if self.current_response_task and not self.current_response_task.done():
            self.current_response_task.cancel()
            try:
                await self.current_response_task
            except asyncio.CancelledError:
                print("✓ Task cancelled")

        self.is_responding = False
        self.response_started = False
        self.user_speech_start_time = 0.0
        self.is_user_speaking = False

        try:
            await self.websocket.send_json({"type": "interrupted"})
        except:
            pass

    async def start_ai_response(self, user_text: str):
        """Start AI response to user input."""
        self.should_stop = False
        self.is_responding = True
        self.response_started = False

        print(f"🤖 Responding to: '{user_text[:50]}...'")

        self.current_response_task = asyncio.create_task(
            self._generate_response(user_text)
        )

        try:
            await self.current_response_task
        except asyncio.CancelledError:
            print("✓ Response cancelled")
        except Exception as e:
            print(f"❌ Response error: {e}")
        finally:
            self.is_responding = False
            self.current_response_task = None

    async def _generate_response(self, user_text: str):
        """Generate response by piping LLM → TTS."""
        # Get services from app state
        tts_service = self.websocket.app.state.tts
        llm_service = self.websocket.app.state.llm

        try:
            # Get streaming LLM response
            llm_stream = llm_service.stream_response(user_text)

            # Stream through TTS
            async for audio_chunk in tts_service.synthesize_stream(
                llm_stream,
                should_stop_check=lambda: self.should_stop
            ):
                if self.should_stop:
                    break

                await self.websocket.send_bytes(audio_chunk)

                if not self.response_started:
                    self.response_started = True
                    print("🔊 Audio started")

        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"❌ Generation error: {e}")
            raise


# ===== STEP 3: Initialize Services on Startup =====

@app.on_event("startup")
async def startup_event():
    """Initialize services when app starts."""
    print("🚀 Initializing services...")

    # Initialize TTS service
    app.state.tts = TTSService(
        api_key=config.ELEVENLABS_API_KEY,
        voice_id=config.ELEVENLABS_VOICE_ID,
        model_id="eleven_turbo_v2_5",
        output_format="pcm_24000"
    )
    print("✓ TTS service initialized")

    # Initialize LLM service
    app.state.llm = OpenAIService(
        api_key=config.OPENAI_API_KEY,
        model="gpt-4o-mini"
    )
    print("✓ LLM service initialized")

    # Initialize Deepgram service
    app.state.deepgram = DeepgramService(
        api_key=config.DEEPGRAM_API_KEY
    )
    print("✓ Deepgram service initialized")

    print("🎉 All services ready!")


# ===== STEP 4: WebSocket Handler =====

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket handler for audio streaming.

    Flow:
    1. Client connects
    2. Client sends audio → Deepgram (STT)
    3. Deepgram sends transcripts → LLM
    4. LLM streams tokens → TTS
    5. TTS sends audio → Client
    """
    await websocket.accept()
    print("✓ Client connected")

    # Create connection state
    state = ConnectionState(websocket)

    # Get Deepgram service
    deepgram = app.state.deepgram

    # Setup Deepgram connection with callbacks
    try:
        # Connect to Deepgram
        deepgram_ws = await deepgram.connect(
            on_interim=state._on_interim_transcript,
            on_final=state._on_final_transcript
        )

        print("✓ Deepgram connected")

        # Main message loop
        while True:
            try:
                # Receive data from client
                data = await websocket.receive()

                if "bytes" in data:
                    # Audio data from microphone → send to Deepgram
                    audio_bytes = data["bytes"]
                    await deepgram_ws.send(audio_bytes)

                elif "text" in data:
                    # Text message from client (for debugging/control)
                    message = data["text"]
                    print(f"📨 Client message: {message}")

                    # Handle control messages
                    if message == "stop":
                        await state._interrupt_ai_response()

            except WebSocketDisconnect:
                print("✓ Client disconnected")
                break

            except Exception as e:
                print(f"❌ Error in message loop: {e}")
                break

    except Exception as e:
        print(f"❌ WebSocket error: {e}")

    finally:
        # Cleanup
        print("🧹 Cleaning up...")

        # Cancel any running tasks
        if state.current_response_task and not state.current_response_task.done():
            state.current_response_task.cancel()
            try:
                await state.current_response_task
            except asyncio.CancelledError:
                pass

        # Close Deepgram connection
        if deepgram_ws:
            await deepgram_ws.close()

        print("✓ Cleanup complete")


# ===== STEP 5: LLM Service Example =====

class OpenAIService:
    """
    LLM service with streaming support.

    This is an example - adapt to your existing LLM integration.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    async def stream_response(self, user_text: str) -> AsyncGenerator[str, None]:
        """
        Stream response from OpenAI.

        Args:
            user_text: User's input

        Yields:
            Token strings as they arrive
        """
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            # Create streaming completion
            stream = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful voice assistant."},
                    {"role": "user", "content": user_text}
                ],
                stream=True,
                temperature=0.7
            )

            # Yield tokens as they arrive
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            print(f"❌ OpenAI error: {e}")
            raise


# ===== STEP 6: Deepgram Service Example =====

class DeepgramService:
    """
    Deepgram transcription service.

    This is an example - adapt to your existing Deepgram integration.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def connect(self, on_interim, on_final):
        """
        Connect to Deepgram with callbacks.

        Args:
            on_interim: Async function to call with interim transcripts
            on_final: Async function to call with final transcripts

        Returns:
            WebSocket connection to Deepgram
        """
        from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

        client = DeepgramClient(self.api_key)

        # Configure options
        options = LiveOptions(
            model="nova-2",
            language="en-US",
            encoding="linear16",
            sample_rate=16000,
            channels=1,
            interim_results=True,
            endpointing=300
        )

        # Connect
        dg_connection = client.listen.websocket.v("1")

        # Setup event handlers
        def handle_transcript(self, result, **kwargs):
            """Handle transcript events."""
            sentence = result.channel.alternatives[0].transcript

            if not sentence:
                return

            if result.is_final:
                # Final transcript
                asyncio.create_task(on_final(sentence))
            else:
                # Interim transcript
                asyncio.create_task(on_interim(sentence))

        def handle_error(self, error, **kwargs):
            print(f"❌ Deepgram error: {error}")

        # Register handlers
        dg_connection.on(LiveTranscriptionEvents.Transcript, handle_transcript)
        dg_connection.on(LiveTranscriptionEvents.Error, handle_error)

        # Start connection
        if not dg_connection.start(options):
            raise Exception("Failed to connect to Deepgram")

        return dg_connection


# ===== STEP 7: Testing Endpoint =====

@app.get("/")
async def get():
    """Serve test client HTML."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Voice AI Test Client</title>
    </head>
    <body>
        <h1>Voice AI Test Client</h1>
        <button id="start">Start</button>
        <button id="stop" disabled>Stop</button>
        <div id="log"></div>

        <script>
            let ws, audioContext, processor, stream;

            document.getElementById('start').onclick = async () => {
                // Get microphone
                stream = await navigator.mediaDevices.getUserMedia({audio: true});

                // Connect WebSocket
                ws = new WebSocket('ws://localhost:8000/ws/audio');
                ws.binaryType = 'arraybuffer';

                ws.onopen = () => {
                    log('Connected');
                    document.getElementById('start').disabled = true;
                    document.getElementById('stop').disabled = false;
                };

                ws.onmessage = async (event) => {
                    if (event.data instanceof ArrayBuffer) {
                        // Audio from TTS - play it
                        // (Use your existing audio playback code)
                        log('Received audio: ' + event.data.byteLength + ' bytes');
                    }
                };

                // Send microphone audio to server
                audioContext = new AudioContext({sampleRate: 16000});
                const source = audioContext.createMediaStreamSource(stream);
                processor = audioContext.createScriptProcessor(4096, 1, 1);

                processor.onaudioprocess = (e) => {
                    if (ws.readyState === WebSocket.OPEN) {
                        const float32 = e.inputBuffer.getChannelData(0);
                        const int16 = new Int16Array(float32.length);
                        for (let i = 0; i < float32.length; i++) {
                            int16[i] = Math.max(-32768, Math.min(32767, float32[i] * 32768));
                        }
                        ws.send(int16.buffer);
                    }
                };

                source.connect(processor);
                processor.connect(audioContext.destination);
            };

            document.getElementById('stop').onclick = () => {
                if (ws) ws.close();
                if (stream) stream.getTracks().forEach(t => t.stop());
                if (audioContext) audioContext.close();
                document.getElementById('start').disabled = false;
                document.getElementById('stop').disabled = true;
                log('Stopped');
            };

            function log(msg) {
                document.getElementById('log').innerHTML += '<div>' + msg + '</div>';
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ===== STEP 8: Run the Server =====

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


# ===== QUICK CHECKLIST =====
"""
✓ Copy TTSService from tts_complete.py → services/tts.py
✓ Copy ConnectionState class above → main.py
✓ Update config.py with buffer thresholds and interruption settings
✓ Add startup_event() to initialize services
✓ Update websocket_endpoint() with ConnectionState integration
✓ Ensure LLM service has stream_response() method
✓ Ensure Deepgram service calls on_interim and on_final callbacks
✓ Test with /ws/audio endpoint
✓ Monitor logs for buffer decisions and interruptions
"""


# ===== TROUBLESHOOTING =====
"""
Issue: Sentences still cutting off
- Check logs for "Flush:" messages
- Verify HARD_MAX_BUFFER is 120 (not 25!)
- Confirm _should_flush_buffer is being used

Issue: Interruptions not working
- Check that on_interim is calling _on_interim_transcript
- Verify DEBOUNCE_THRESHOLD is 0.3 seconds
- Check logs for "User speech detected" messages

Issue: False interruptions
- Increase DEBOUNCE_THRESHOLD to 0.4
- Increase INTERRUPTION_COOLDOWN to 0.7
- Check Deepgram sensitivity settings

Issue: Audio quality issues
- Verify output_format is "pcm_24000"
- Check frontend resampling (see previous fixes)
- Monitor network latency
"""
