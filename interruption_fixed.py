"""
Fixed Interruption Logic with Proper Debouncing
================================================

Key Fixes:
1. Timer-based debouncing that actually works
2. Checks timer on EACH interim transcript (not just once)
3. Resets properly when user stops speaking
4. Prevents false interruptions from background noise

Author: Claude
Date: 2026-01-08
"""

import time
import asyncio
from typing import Optional


class ConnectionState:
    """
    Manages conversation state and interruption logic for a WebSocket connection.
    """

    def __init__(self, websocket):
        self.websocket = websocket

        # Response state
        self.should_stop = False
        self.is_responding = False
        self.response_started = False
        self.current_response_task: Optional[asyncio.Task] = None

        # Timing state
        self.last_final_transcript_time = 0.0

        # DEBOUNCING STATE (NEW)
        self.user_speech_start_time = 0.0
        self.is_user_speaking = False

        # Configuration
        self.DEBOUNCE_THRESHOLD = 0.3  # 300ms - require sustained speech
        self.INTERRUPTION_COOLDOWN = 0.5  # 500ms - time since last final transcript

    async def _on_interim_transcript(self, text: str):
        """
        Called when Deepgram sends interim (partial) transcription.

        This is called MULTIPLE TIMES as the user speaks, making it perfect
        for debouncing logic.

        Args:
            text: Partial transcription text
        """
        if not text.strip():
            # Empty or whitespace - might be noise
            return

        current_time = time.time()

        # Only consider interrupting if AI is actively responding
        if not self.is_responding or not self.response_started:
            return

        # Check cooldown period (prevent interrupting too soon after user's last speech)
        time_since_last_transcript = current_time - self.last_final_transcript_time
        if time_since_last_transcript < self.INTERRUPTION_COOLDOWN:
            # Too soon - might be echo or processing delay
            return

        # DEBOUNCING LOGIC (FIXED)
        # Start the timer if this is the first detection
        if self.user_speech_start_time == 0:
            self.user_speech_start_time = current_time
            self.is_user_speaking = True
            print(f"🎤 User speech detected, starting debounce timer...")
            return  # Don't interrupt yet - wait for sustained speech

        # Check if user has been speaking long enough
        speech_duration = current_time - self.user_speech_start_time

        if speech_duration >= self.DEBOUNCE_THRESHOLD:
            # User has been speaking for >300ms - this is a real interruption
            if not self.should_stop:  # Only log once
                print(f"🛑 USER INTERRUPTION CONFIRMED (sustained {speech_duration:.2f}s)")
                await self._interrupt_ai_response()
        else:
            # Still building up - not enough time yet
            print(f"⏳ User speaking for {speech_duration:.2f}s (need {self.DEBOUNCE_THRESHOLD}s)")

    async def _on_final_transcript(self, text: str):
        """
        Called when Deepgram sends final (confirmed) transcription.

        This marks the end of a user's speech segment.

        Args:
            text: Final transcription text
        """
        if not text.strip():
            return

        current_time = time.time()
        self.last_final_transcript_time = current_time

        # RESET DEBOUNCING STATE (user stopped speaking)
        self.user_speech_start_time = 0.0
        self.is_user_speaking = False
        print(f"✓ Final transcript: '{text}'")

        # Process the transcript (send to LLM, etc.)
        # ... your existing logic ...

    async def _interrupt_ai_response(self):
        """
        Interrupt the AI's current response.

        This is called when we've confirmed the user is actually interrupting
        (not just background noise).
        """
        if not self.is_responding:
            return

        print("🛑 Interrupting AI response...")

        # Set flag to stop TTS streaming
        self.should_stop = True

        # Cancel the response task
        if self.current_response_task and not self.current_response_task.done():
            self.current_response_task.cancel()
            try:
                await self.current_response_task
            except asyncio.CancelledError:
                print("✓ Response task cancelled")

        # Reset state
        self.is_responding = False
        self.response_started = False

        # Optional: Send a "stop" message to the client
        # await self.websocket.send_json({"type": "interrupted"})

    async def start_ai_response(self, text: str):
        """
        Start generating an AI response.

        Args:
            text: User's input text to respond to
        """
        # Reset interruption flag
        self.should_stop = False
        self.is_responding = True
        self.response_started = False

        # Create the response task
        self.current_response_task = asyncio.create_task(
            self._generate_response(text)
        )

        # Wait for completion (or cancellation)
        try:
            await self.current_response_task
        except asyncio.CancelledError:
            print("✓ Response generation cancelled")
        finally:
            self.is_responding = False
            self.current_response_task = None

    async def _generate_response(self, text: str):
        """
        Generate AI response (LLM + TTS pipeline).

        Args:
            text: User's input text
        """
        try:
            # 1. Get LLM response (streaming)
            llm_stream = self._get_llm_stream(text)

            # 2. Stream to TTS
            # Note: TTS service should check self.should_stop flag
            async for audio_chunk in self._stream_to_tts(llm_stream):
                if self.should_stop:
                    print("🛑 Response generation stopped (interrupted)")
                    break

                # Send audio to client
                await self.websocket.send_bytes(audio_chunk)

                # Mark that we've started sending audio
                if not self.response_started:
                    self.response_started = True

        except Exception as e:
            print(f"❌ Error in response generation: {e}")
            raise

    async def _get_llm_stream(self, text: str):
        """
        Get streaming response from LLM.

        This is a placeholder - implement your actual LLM integration.
        """
        # Your OpenAI/LLM streaming logic here
        # Should yield tokens as they arrive
        pass

    async def _stream_to_tts(self, llm_stream):
        """
        Stream LLM tokens to TTS service.

        This is a placeholder - implement your actual TTS integration.
        """
        # Your TTS streaming logic here
        # Should check self.should_stop flag and break if needed
        pass


# ===== INTEGRATION EXAMPLE =====

"""
How to integrate this into your FastAPI WebSocket handler:

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state = ConnectionState(websocket)

    # Setup Deepgram with callbacks
    deepgram_client = setup_deepgram()

    # Connect callbacks
    deepgram_client.on_interim_transcript(state._on_interim_transcript)
    deepgram_client.on_final_transcript(state._on_final_transcript)

    try:
        while True:
            # Receive audio from client
            audio_data = await websocket.receive_bytes()

            # Send to Deepgram for transcription
            await deepgram_client.send(audio_data)

    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        await deepgram_client.close()
"""


# ===== TESTING =====

async def test_debouncing():
    """
    Test the debouncing logic with simulated interim transcripts.
    """

    class MockWebSocket:
        async def send_bytes(self, data):
            pass

    state = ConnectionState(MockWebSocket())
    state.is_responding = True
    state.response_started = True
    state.last_final_transcript_time = time.time() - 1.0  # 1 second ago

    print("=== Testing Debouncing ===\n")

    # Simulate rapid interim transcripts (user speaking)
    print("Test 1: Sustained speech (should interrupt)")
    for i in range(10):
        await state._on_interim_transcript(f"Hello this is test {i}")
        await asyncio.sleep(0.05)  # 50ms intervals
    print()

    # Reset
    await state._on_final_transcript("Hello this is test")
    state.is_responding = True
    state.response_started = True
    state.last_final_transcript_time = time.time() - 1.0

    # Simulate brief noise (should NOT interrupt)
    print("Test 2: Brief noise (should NOT interrupt)")
    await state._on_interim_transcript("um")
    await asyncio.sleep(0.1)
    await state._on_final_transcript("um")
    print()

    print("✅ Debouncing tests complete")


if __name__ == "__main__":
    # Uncomment to run tests
    # asyncio.run(test_debouncing())
    pass
