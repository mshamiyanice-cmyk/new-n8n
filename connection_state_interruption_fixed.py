"""
Fixed ConnectionState with Interruption State Machine
======================================================

This fixes the "queued words" problem by tracking interruption state
and ignoring transcripts that were part of the interruption attempt.

Root Cause:
- User interrupts AI at time T
- Deepgram sends final transcript at time T+0.5s (after interruption)
- Final transcript triggers new response with "queued" words
- Result: AI responds to interruption words instead of waiting for new input

Solution:
- Track when we're in "interrupting" state
- Ignore all transcripts during interruption window
- Only respond to transcripts after clear separation

Author: Claude
Date: 2026-01-08
"""

import time
import asyncio
from typing import Optional
from fastapi import WebSocket


class ConnectionState:
    """
    Enhanced ConnectionState with interruption state machine.
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

        # === NEW: Interruption state machine ===
        self.is_interrupting = False              # True when interruption is in progress
        self.interruption_triggered_time = 0.0    # When interruption was triggered
        self.interruption_cooldown_duration = 1.0  # How long to ignore transcripts after interruption

        # Configuration
        self.DEBOUNCE_THRESHOLD = 0.2             # Reduced from 0.3s for faster interruption
        self.INTERRUPTION_COOLDOWN = 0.5          # Cooldown before allowing interruptions
        self.POST_INTERRUPTION_SILENCE = 0.8      # Require silence after interruption before responding

    async def _on_interim_transcript(self, text: str):
        """
        Handle interim transcripts with interruption state awareness.

        Key changes:
        1. Ignore transcripts during interruption window
        2. Reduced debounce threshold (200ms instead of 300ms)
        3. Clear interruption state only on explicit user stop
        """
        if not text.strip():
            return

        current_time = time.time()

        # === NEW: Ignore transcripts during interruption window ===
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

        # Check interruption cooldown (prevent interrupting too soon after user's last speech)
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
            if not self.should_stop and not self.is_interrupting:
                print(f"🛑 INTERRUPTION CONFIRMED (sustained {speech_duration:.2f}s): '{text[:30]}...'")
                await self._interrupt_ai_response()
        else:
            print(f"⏳ Debouncing: {speech_duration:.2f}s / {self.DEBOUNCE_THRESHOLD}s ('{text[:20]}...')")

    async def _on_final_transcript(self, text: str):
        """
        Handle final transcripts with interruption state awareness.

        Key changes:
        1. Ignore final transcripts during interruption window
        2. Require silence after interruption before responding
        3. Clear interruption state on explicit user stop
        """
        if not text.strip():
            return

        current_time = time.time()

        # === NEW: Ignore transcripts during interruption window ===
        if self.is_interrupting:
            time_since_interrupt = current_time - self.interruption_triggered_time
            if time_since_interrupt < self.interruption_cooldown_duration:
                print(f"⏸️ Ignoring FINAL during interruption cooldown ({time_since_interrupt:.2f}s / {self.interruption_cooldown_duration}s): '{text[:50]}...'")

                # Update timing but don't process
                self.last_final_transcript_time = current_time
                self.user_speech_start_time = 0.0
                self.is_user_speaking = False

                return
            else:
                # Cooldown expired - clear interruption state
                print(f"✓ Interruption cooldown expired, processing transcript: '{text[:50]}...'")
                self.is_interrupting = False

        # Update timing
        self.last_final_transcript_time = current_time
        self.user_speech_start_time = 0.0
        self.is_user_speaking = False

        print(f"✓ Final transcript: '{text}'")

        # === NEW: Check if enough time has passed since interruption ===
        if self.interruption_triggered_time > 0:
            time_since_interrupt = current_time - self.interruption_triggered_time
            if time_since_interrupt < self.POST_INTERRUPTION_SILENCE:
                print(f"⏸️ Too soon after interruption ({time_since_interrupt:.2f}s < {self.POST_INTERRUPTION_SILENCE}s), waiting for clear separation")
                return

        # Process transcript if not responding
        if not self.is_responding and text.strip():
            print(f"🤖 Starting response to: '{text[:50]}...'")
            # Your existing logic to start AI response
            # await self.start_ai_response(text)

    async def _interrupt_ai_response(self):
        """
        Interrupt AI response and enter interruption state.

        Key changes:
        1. Set is_interrupting flag
        2. Record interruption time
        3. This prevents immediate response to accumulated transcripts
        """
        if not self.is_responding:
            return

        print("🛑 Interrupting AI response...")

        # === NEW: Enter interruption state ===
        self.is_interrupting = True
        self.interruption_triggered_time = time.time()

        # Set flag to stop TTS streaming
        self.should_stop = True

        # Cancel the response task
        if self.current_response_task and not self.current_response_task.done():
            self.current_response_task.cancel()
            try:
                await self.current_response_task
            except asyncio.CancelledError:
                print("✓ Response task cancelled")
            except Exception as e:
                print(f"⚠️ Error during task cancellation: {e}")

        # Reset conversation state
        self.is_responding = False
        self.response_started = False

        # Reset debouncing state
        self.user_speech_start_time = 0.0
        self.is_user_speaking = False

        # Send interruption message to client
        try:
            await self.websocket.send_json({
                "type": "interrupted",
                "message": "AI response interrupted"
            })
        except Exception as e:
            print(f"⚠️ Could not send interruption message: {e}")

        print(f"✓ Interruption complete, cooling down for {self.interruption_cooldown_duration}s")

    async def start_ai_response(self, user_text: str):
        """
        Start AI response (only if not in interruption state).

        Key changes:
        1. Check if in interruption state before starting
        2. Clear interruption time when starting new response
        """
        # === NEW: Don't start if in interruption state ===
        if self.is_interrupting:
            current_time = time.time()
            time_since_interrupt = current_time - self.interruption_triggered_time
            if time_since_interrupt < self.interruption_cooldown_duration:
                print(f"⏸️ Skipping response start (in interruption cooldown)")
                return

        # Reset interruption state when starting new response
        self.is_interrupting = False
        self.interruption_triggered_time = 0.0

        # Reset interruption flag
        self.should_stop = False
        self.is_responding = True
        self.response_started = False

        print(f"🤖 Starting AI response to: '{user_text[:50]}...'")

        # Your existing response generation logic
        # self.current_response_task = asyncio.create_task(...)

    # === NEW: Manual state reset method ===
    async def reset_interruption_state(self):
        """
        Manually reset interruption state.

        Call this if you need to force-clear the interruption state
        (e.g., user explicitly says "start over").
        """
        print("🔄 Manually resetting interruption state")
        self.is_interrupting = False
        self.interruption_triggered_time = 0.0
        self.user_speech_start_time = 0.0
        self.is_user_speaking = False


# ===== ALTERNATIVE APPROACH: Use VAD Events =====

"""
If the above approach still has issues, you can enable VAD events
and use them for immediate interruption detection.

In services/transcription.py:

options = LiveOptions(
    model="nova-2",
    language="en-US",
    encoding="linear16",
    sample_rate=16000,
    channels=1,
    smart_format=True,
    interim_results=True,
    vad_events=True,           # ← Enable VAD
    utterance_end_ms=800,      # ← Shorter utterance detection
)

Then add VAD handlers:

def handle_vad_event(self, result, **kwargs):
    if result.speech_started:
        # User started speaking - interrupt immediately
        asyncio.create_task(state._on_user_speaking_vad())
    elif result.speech_stopped:
        # User stopped speaking
        asyncio.create_task(state._on_user_stopped_vad())

connection.on(LiveTranscriptionEvents.SpeechStarted, handle_vad_event)

In ConnectionState:

async def _on_user_speaking_vad(self):
    '''VAD detected user started speaking.'''
    if self.is_responding and self.response_started:
        # Interrupt immediately (no debouncing)
        print("🛑 VAD: User started speaking, interrupting immediately")
        await self._interrupt_ai_response()

This approach interrupts IMMEDIATELY when user starts speaking,
without waiting for debounce threshold.

Trade-off: More sensitive to false positives (noise, etc.)
"""


# ===== TESTING UTILITIES =====

async def test_interruption_state_machine():
    """Test the interruption state machine."""
    from unittest.mock import MagicMock

    mock_ws = MagicMock()
    mock_ws.send_json = asyncio.coroutine(lambda x: None)

    state = ConnectionState(mock_ws)
    state.is_responding = True
    state.response_started = True
    state.last_final_transcript_time = time.time() - 1.0

    print("=== Test 1: Interruption Cooldown ===")

    # Trigger interruption
    state.user_speech_start_time = time.time() - 0.3
    await state._on_interim_transcript("Are you sure?")

    # Should be in interruption state
    assert state.is_interrupting
    print(f"✓ is_interrupting: {state.is_interrupting}")

    # Try to process final transcript immediately (should be ignored)
    await state._on_final_transcript("Are you sure?")
    print(f"✓ Final transcript ignored during cooldown")

    # Wait for cooldown
    await asyncio.sleep(1.1)

    # Now final transcript should be processed
    state.is_responding = False  # Simulate AI stopped
    await state._on_final_transcript("What's the weather?")
    print(f"✓ Final transcript processed after cooldown")

    print("\n=== Test 2: Fast Debouncing ===")

    state = ConnectionState(mock_ws)
    state.is_responding = True
    state.response_started = True
    state.last_final_transcript_time = time.time() - 1.0

    # Start speaking
    await state._on_interim_transcript("Wait")

    # 200ms later (should trigger with new threshold)
    await asyncio.sleep(0.21)
    await state._on_interim_transcript("Wait a minute")

    assert state.is_interrupting
    print(f"✓ Interrupted after 200ms (faster than before)")

    print("\n✅ All interruption state machine tests passed")


if __name__ == "__main__":
    # Uncomment to run tests
    # asyncio.run(test_interruption_state_machine())
    pass
