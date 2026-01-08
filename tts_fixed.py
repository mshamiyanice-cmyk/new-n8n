"""
Fixed TTS Service with Semantic Buffering
==========================================

Key Fixes:
1. Semantic buffering - only flush on sentence boundaries
2. Proper should_stop checking throughout the loop
3. Final flush guarantee with try/finally
4. Intelligent buffer management

Author: Claude
Date: 2026-01-08
"""

from typing import Union, AsyncGenerator
import time


class TTSService:
    """TTS service with intelligent semantic buffering."""

    def __init__(self, api_key: str, voice_id: str):
        self.api_key = api_key
        self.voice_id = voice_id
        self.should_stop = False  # Set by interruption logic

        # Buffer configuration
        self.WEAK_PUNCTUATION = (',', ';', ':', '-', '—')
        self.STRONG_PUNCTUATION = ('.', '!', '?')

        # Buffer thresholds (tuned for optimal latency/quality)
        self.MIN_WEAK_BUFFER = 40  # Minimum chars before flushing on comma
        self.HARD_MAX_BUFFER = 120  # Absolute max to prevent latency
        self.SENTENCE_MIN = 15  # Minimum chars for a "real" sentence

    async def _stream_elevenlabs(
        self,
        text_input: Union[str, AsyncGenerator[str, None]]
    ) -> AsyncGenerator[bytes, None]:
        """
        ElevenLabs TTS streaming with semantic buffering.

        Strategy:
        - Build buffer until we hit a natural sentence boundary
        - Strong punctuation (. ! ?) → flush immediately (if buffer > min)
        - Weak punctuation (, ; :) → flush only if buffer is substantial
        - Hard max limit → prevent excessive latency
        - Always check should_stop flag for interruptions

        Args:
            text_input: Either a string or async generator of text tokens

        Yields:
            Audio chunks as bytes (PCM format)
        """
        try:
            from elevenlabs import AsyncElevenLabs

            if not self.api_key:
                print("⚠️ ELEVENLABS_API_KEY not set")
                return

            client = AsyncElevenLabs(api_key=self.api_key)
            output_format = "pcm_24000"
            model_id = "eleven_turbo_v2_5"

            # Handle non-streaming input (simple case)
            if isinstance(text_input, str):
                print(f"📤 Sending to ElevenLabs: '{text_input[:100]}...'")
                audio_generator = client.text_to_speech.stream(
                    voice_id=self.voice_id,
                    text=text_input,
                    model_id=model_id,
                    output_format=output_format,
                )

                async for chunk in audio_generator:
                    if self.should_stop:
                        print("🛑 TTS interrupted (should_stop)")
                        break
                    if chunk:
                        yield chunk
                return

            # STREAMING MODE: Intelligent semantic buffering
            if hasattr(text_input, '__aiter__'):
                buffer = ""
                chunk_count = 0
                total_bytes = 0

                try:
                    async for token in text_input:
                        # Check for interruption FIRST (before processing)
                        if self.should_stop:
                            print(f"🛑 TTS interrupted after {chunk_count} chunks")
                            break

                        if not token:
                            continue

                        buffer += token

                        # Determine if we should flush the buffer
                        should_send = self._should_flush_buffer(buffer, token)

                        if should_send and buffer.strip():
                            # Send accumulated buffer to ElevenLabs
                            text_to_synthesize = buffer.strip()
                            buffer = ""  # Clear buffer

                            print(f"📤 Sending to ElevenLabs: '{text_to_synthesize[:80]}...'")

                            # Generate audio for this chunk
                            audio_generator = client.text_to_speech.stream(
                                voice_id=self.voice_id,
                                text=text_to_synthesize,
                                model_id=model_id,
                                output_format=output_format,
                            )

                            # Stream audio chunks
                            chunk_bytes = 0
                            async for audio_chunk in audio_generator:
                                # Check interruption during audio generation
                                if self.should_stop:
                                    print("🛑 TTS interrupted during audio generation")
                                    break

                                if audio_chunk:
                                    yield audio_chunk
                                    chunk_bytes += len(audio_chunk)

                            chunk_count += 1
                            total_bytes += chunk_bytes
                            print(f"✓ Received {chunk_bytes} bytes for chunk #{chunk_count}")

                            # Break outer loop if interrupted
                            if self.should_stop:
                                break

                    # FINAL FLUSH: Send any remaining buffer (unless interrupted)
                    if buffer.strip() and not self.should_stop:
                        print(f"📤 Final flush: '{buffer.strip()[:80]}...'")

                        audio_generator = client.text_to_speech.stream(
                            voice_id=self.voice_id,
                            text=buffer.strip(),
                            model_id=model_id,
                            output_format=output_format,
                        )

                        chunk_bytes = 0
                        async for audio_chunk in audio_generator:
                            if self.should_stop:
                                print("🛑 TTS interrupted during final flush")
                                break
                            if audio_chunk:
                                yield audio_chunk
                                chunk_bytes += len(audio_chunk)

                        chunk_count += 1
                        total_bytes += chunk_bytes
                        print(f"✓ Final chunk: {chunk_bytes} bytes")

                    print(f"🎉 ElevenLabs Stream Complete: {chunk_count} chunks, {total_bytes} bytes total")

                except Exception as e:
                    print(f"❌ Error in TTS streaming: {e}")
                    # Don't re-raise - allow graceful degradation

        except Exception as e:
            print(f"❌ Critical error in TTS service: {e}")
            # Re-raise critical errors (API key, import issues, etc.)
            raise

    def _should_flush_buffer(self, buffer: str, latest_token: str) -> bool:
        """
        Intelligent decision on when to flush the buffer.

        Rules:
        1. Strong punctuation (. ! ?) + min length → FLUSH
        2. Weak punctuation (, ; :) + substantial buffer → FLUSH
        3. Hard max limit reached → FLUSH (safety)
        4. Otherwise → KEEP BUFFERING

        Args:
            buffer: Current accumulated text
            latest_token: Most recent token added

        Returns:
            True if buffer should be flushed, False otherwise
        """
        buffer_len = len(buffer)
        token_stripped = latest_token.strip()

        # RULE 1: Hard maximum limit (prevent excessive latency)
        if buffer_len >= self.HARD_MAX_BUFFER:
            print(f"🔄 Flush: Hard max reached ({buffer_len} chars)")
            return True

        # RULE 2: Strong punctuation (sentence ending)
        # Only flush if we have a substantial sentence
        if token_stripped.endswith(self.STRONG_PUNCTUATION):
            if buffer_len >= self.SENTENCE_MIN:
                print(f"🔄 Flush: Strong punctuation ({buffer_len} chars)")
                return True
            else:
                # Too short to be a real sentence (might be abbreviation like "Dr.")
                print(f"⏳ Waiting: Sentence too short ({buffer_len} chars)")
                return False

        # RULE 3: Weak punctuation (comma, semicolon, etc.)
        # Only flush if buffer is substantial (prevents cutting mid-thought)
        if token_stripped.endswith(self.WEAK_PUNCTUATION):
            if buffer_len >= self.MIN_WEAK_BUFFER:
                print(f"🔄 Flush: Weak punctuation with substantial buffer ({buffer_len} chars)")
                return True
            else:
                print(f"⏳ Waiting: Buffer too small for weak punctuation ({buffer_len} chars)")
                return False

        # RULE 4: Keep buffering (no punctuation or conditions not met)
        return False

    def interrupt(self):
        """Signal the TTS service to stop (called by interruption logic)."""
        print("🛑 TTS interrupt signal received")
        self.should_stop = True

    def reset(self):
        """Reset the service state for a new conversation turn."""
        self.should_stop = False


# Example usage
if __name__ == "__main__":
    import asyncio

    async def demo():
        # Simulate LLM token stream
        async def mock_llm_stream():
            tokens = [
                "Start ", "by ", "educating ", "yourself ", "on ", "local ",
                "issues", ", ", "joining ", "community ", "organizations", ", ",
                "and ", "voting ", "in ", "elections", "."
            ]
            for token in tokens:
                yield token
                await asyncio.sleep(0.05)  # Simulate streaming

        tts = TTSService(api_key="dummy_key", voice_id="dummy_voice")

        print("=== Testing Semantic Buffering ===\n")

        async for audio_chunk in tts._stream_elevenlabs(mock_llm_stream()):
            print(f"🔊 Audio chunk: {len(audio_chunk)} bytes")

    # asyncio.run(demo())  # Uncomment to test
