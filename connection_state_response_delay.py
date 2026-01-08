"""
Fix for AI Responding Too Quickly
==================================

Problem: AI responds immediately to final transcripts, even when user is just
pausing to breathe/think, not actually done speaking.

Solution: Add a short delay after final transcript before starting response.
During this delay, if another transcript arrives, restart the timer.

This ensures user is truly done before AI responds.

Author: Claude
Date: 2026-01-08
"""

import asyncio
import time
from typing import Optional


class ConnectionState:
    """Enhanced with response delay logic."""

    def __init__(self, websocket):
        # ... existing code ...

        # Response delay settings
        self.response_delay_duration = 0.8  # Wait 800ms after final transcript
        self.response_delay_task: Optional[asyncio.Task] = None
        self.pending_user_text = ""  # Accumulate text during delay

    async def _on_final_transcript(self, text: str):
        """
        Handle final transcripts with response delay.

        Key change: Don't respond immediately. Wait for response_delay_duration
        to ensure user is truly done speaking.
        """
        if not text.strip():
            return

        current_time = time.time()

        # Interruption cooldown check (existing code)
        if self.is_interrupting:
            time_since_interrupt = current_time - self.interruption_triggered_time
            if time_since_interrupt < self.interruption_cooldown_duration:
                print(f"⏸️ Ignoring FINAL during interruption cooldown: '{text[:50]}...'")
                self.last_final_transcript_time = current_time
                self.user_speech_start_time = 0.0
                self.is_user_speaking = False
                return
            else:
                print(f"✓ Interruption cooldown expired")
                self.is_interrupting = False

        # Update timing
        self.last_final_transcript_time = current_time
        self.user_speech_start_time = 0.0
        self.is_user_speaking = False

        print(f"✓ Final transcript: '{text}'")

        # === NEW: Response delay logic ===

        # If AI is already responding, don't start new response
        if self.is_responding:
            print(f"⏭️ AI already responding, ignoring new transcript")
            return

        # Cancel existing response delay task if any
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

    async def _delayed_response(self):
        """
        Wait for response_delay_duration, then start response.

        If another transcript arrives during this delay, this task
        will be cancelled and a new one started.
        """
        try:
            # Wait for the delay
            await asyncio.sleep(self.response_delay_duration)

            # Delay expired - user is truly done!
            if self.pending_user_text and not self.is_responding:
                text_to_respond = self.pending_user_text
                self.pending_user_text = ""

                print(f"✅ Response delay expired, starting response to: '{text_to_respond[:50]}...'")

                # Start AI response
                await self.start_ai_response(text_to_respond)

        except asyncio.CancelledError:
            # Cancelled because new transcript arrived
            print(f"❌ Response delay cancelled (new transcript arrived)")
            raise


# ===== TESTING =====

async def test_response_delay():
    """Test response delay logic."""
    from unittest.mock import MagicMock

    mock_ws = MagicMock()
    state = ConnectionState(mock_ws)

    print("=== Test: Response Delay ===\n")

    # Simulate user speaking in chunks
    await state._on_final_transcript("Before you answer")
    print("Transcript 1 received, timer started\n")

    await asyncio.sleep(0.5)  # Wait 500ms (less than 800ms delay)

    # User continues
    await state._on_final_transcript("any question")
    print("Transcript 2 received, timer restarted\n")

    await asyncio.sleep(0.5)  # Wait another 500ms

    # User continues again
    await state._on_final_transcript("mister Mike")
    print("Transcript 3 received, timer restarted again\n")

    # Wait for delay to expire
    await asyncio.sleep(1.0)

    # Should see accumulated text
    print(f"Expected accumulated: 'Before you answer any question mister Mike'")
    print("✅ Test complete\n")


if __name__ == "__main__":
    # asyncio.run(test_response_delay())
    pass
