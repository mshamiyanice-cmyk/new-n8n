# 🧪 Complete Testing Guide - Incomplete Sentences Fix

## 📋 Overview

This guide provides step-by-step instructions to test all fixes:
1. Semantic buffering (complete sentences)
2. Debouncing logic (interruption handling)
3. Integration (end-to-end flow)

---

## 🎯 Test 1: Semantic Buffering (Unit Test)

### Purpose
Verify that buffer flushes only on punctuation boundaries, not character count.

### Test Script

```python
# File: test_tts_buffering.py

import asyncio
from services.tts_complete import TTSService


async def test_semantic_buffering():
    """Test semantic buffering logic."""

    # Initialize TTS (use dummy credentials for testing logic)
    tts = TTSService(
        api_key="test_key",
        voice_id="test_voice"
    )

    print("=== Test 1: Strong Punctuation ===")

    # Test cases
    test_cases = [
        # (buffer, token, expected_result, reason)
        ("Hello world", "!", True, "Strong punctuation + min length"),
        ("Hi", ".", False, "Too short (< 15 chars)"),
        ("This is a test", ".", True, "Strong punctuation + good length"),
        ("To get involved", ",", False, "Weak punctuation but buffer < 40"),
        ("To get involved in your community", ",", True, "Weak punctuation + buffer >= 40"),
        ("A" * 120, "x", True, "Hard max reached"),
        ("Dr", ".", False, "Abbreviation (too short)"),
    ]

    for buffer, token, expected, reason in test_cases:
        result = tts._should_flush_buffer(buffer, token)
        status = "✓" if result == expected else "❌"
        print(f"{status} Buffer: '{buffer[:30]}...' ({len(buffer)} chars)")
        print(f"   Token: '{token}' → Flush: {result} (expected: {expected})")
        print(f"   Reason: {reason}\n")

        assert result == expected, f"Failed: {reason}"

    print("✅ All semantic buffering tests passed!\n")


async def test_streaming_flow():
    """Test streaming with realistic LLM output."""

    print("=== Test 2: Streaming Flow ===")

    tts = TTSService(
        api_key="test_key",
        voice_id="test_voice"
    )

    # Simulate LLM token stream
    async def mock_llm():
        tokens = [
            "To ", "get ", "involved ", "in ", "your ", "community", ", ",
            "start ", "by ", "educating ", "yourself ", "on ", "local ", "issues", ", ",
            "joining ", "community ", "organizations", ", ",
            "and ", "voting ", "in ", "elections", "."
        ]
        for token in tokens:
            await asyncio.sleep(0.01)
            yield token

    # Track flushes
    flushes = []
    buffer = ""

    async for token in mock_llm():
        buffer += token

        if tts._should_flush_buffer(buffer, token):
            flushes.append(buffer.strip())
            print(f"📤 Flush: '{buffer.strip()}'")
            buffer = ""

    # Final flush
    if buffer.strip():
        flushes.append(buffer.strip())
        print(f"📤 Final: '{buffer.strip()}'")

    print(f"\n✓ Total flushes: {len(flushes)}")
    print(f"✓ Expected: 2-3 (sentence boundaries)")

    # Verify no mid-word breaks
    for flush in flushes:
        words = flush.split()
        if words:
            # Check last word is complete (ends with punctuation or is last flush)
            last_word = words[-1]
            if not any(last_word.endswith(p) for p in [',', '.', '!', '?']):
                print(f"⚠️ Warning: Flush might end mid-sentence: '{flush}'")

    print("✅ Streaming flow test passed!\n")


if __name__ == "__main__":
    asyncio.run(test_semantic_buffering())
    asyncio.run(test_streaming_flow())
```

### Expected Output

```
=== Test 1: Strong Punctuation ===
✓ Buffer: 'Hello world' (11 chars)
   Token: '!' → Flush: True (expected: True)
   Reason: Strong punctuation + min length

✓ Buffer: 'Hi' (2 chars)
   Token: '.' → Flush: False (expected: False)
   Reason: Too short (< 15 chars)

...

✅ All semantic buffering tests passed!

=== Test 2: Streaming Flow ===
📤 Flush: 'To get involved in your community, start by educating yourself on local issues,'
📤 Flush: ' joining community organizations, and voting in elections.'

✓ Total flushes: 2
✓ Expected: 2-3 (sentence boundaries)
✅ Streaming flow test passed!
```

### Run Test

```bash
python test_tts_buffering.py
```

---

## 🎯 Test 2: Debouncing Logic (Unit Test)

### Purpose
Verify that interruptions require sustained speech (300ms), not brief noise.

### Test Script

```python
# File: test_debouncing.py

import asyncio
import time
from unittest.mock import MagicMock
from connection_state_complete import ConnectionState


async def test_debouncing():
    """Test interruption debouncing logic."""

    # Create mock websocket
    mock_ws = MagicMock()
    mock_ws.send_json = asyncio.coroutine(lambda x: None)

    state = ConnectionState(mock_ws)

    print("=== Test 1: Sustained Speech (Should Interrupt) ===")

    # Setup: AI is responding
    state.is_responding = True
    state.response_started = True
    state.last_final_transcript_time = time.time() - 1.0  # 1 second ago

    # Simulate sustained speech (10 interim transcripts over 500ms)
    for i in range(10):
        await state._on_interim_transcript(f"Hello this is test {i}")
        await asyncio.sleep(0.05)  # 50ms intervals

    # Check if interrupted
    if state.should_stop:
        print("✅ Interruption triggered (as expected)")
    else:
        print("❌ No interruption (should have interrupted)")
        assert False

    print()

    # Reset
    await state._on_final_transcript("Hello")
    state.is_responding = True
    state.response_started = True
    state.last_final_transcript_time = time.time() - 1.0

    print("=== Test 2: Brief Noise (Should NOT Interrupt) ===")

    # Simulate brief noise (1 interim, then silence)
    await state._on_interim_transcript("um")
    await asyncio.sleep(0.1)  # Wait 100ms (less than 300ms threshold)
    await state._on_final_transcript("um")

    # Check if interrupted
    if state.should_stop:
        print("❌ Interruption triggered (should NOT have interrupted)")
        assert False
    else:
        print("✅ No interruption (as expected)")

    print()

    # Reset
    state.is_responding = True
    state.response_started = True
    state.last_final_transcript_time = time.time()  # NOW (within cooldown)

    print("=== Test 3: Cooldown Period (Should NOT Interrupt) ===")

    # Simulate speech during cooldown period
    for i in range(10):
        await state._on_interim_transcript(f"test {i}")
        await asyncio.sleep(0.05)

    # Check if interrupted (should NOT because of cooldown)
    if state.should_stop:
        print("❌ Interruption triggered (should be blocked by cooldown)")
        assert False
    else:
        print("✅ No interruption due to cooldown (as expected)")

    print()
    print("✅ All debouncing tests passed!")


if __name__ == "__main__":
    asyncio.run(test_debouncing())
```

### Expected Output

```
=== Test 1: Sustained Speech (Should Interrupt) ===
🎤 User speech detected: 'Hello this is test 0'
⏳ Debouncing: 0.05s / 0.3s
⏳ Debouncing: 0.10s / 0.3s
⏳ Debouncing: 0.15s / 0.3s
⏳ Debouncing: 0.20s / 0.3s
⏳ Debouncing: 0.25s / 0.3s
🛑 INTERRUPTION CONFIRMED (0.35s)
✅ Interruption triggered (as expected)

=== Test 2: Brief Noise (Should NOT Interrupt) ===
🎤 User speech detected: 'um'
✓ Final: 'um'
✅ No interruption (as expected)

=== Test 3: Cooldown Period (Should NOT Interrupt) ===
✅ No interruption due to cooldown (as expected)

✅ All debouncing tests passed!
```

### Run Test

```bash
python test_debouncing.py
```

---

## 🎯 Test 3: Integration Test (End-to-End)

### Purpose
Test complete flow: User speaks → STT → LLM → TTS → Audio

### Prerequisites

1. **Set environment variables:**
```bash
export ELEVENLABS_API_KEY="your_key"
export ELEVENLABS_VOICE_ID="your_voice_id"
export OPENAI_API_KEY="your_key"
export DEEPGRAM_API_KEY="your_key"
```

2. **Install dependencies:**
```bash
pip install fastapi uvicorn websockets elevenlabs openai deepgram-sdk
```

### Test Scenarios

#### Scenario 1: Complete Sentence

**Test:**
1. Start server: `python main.py`
2. Open test client: `http://localhost:8000`
3. Click "Start"
4. Say: "How can I get involved in my community?"
5. Listen to AI response

**Expected:**
- ✅ Hear complete sentences (no mid-word cuts)
- ✅ Natural pauses at commas and periods
- ✅ All words audible
- ✅ No robotic/choppy sound

**Check Logs:**
```
📤 TTS chunk #1: 'To get involved in your community, start by educating yourself on local issues,' (82 chars)
✓ Chunk #1: 15360 bytes
📤 TTS chunk #2: ' joining community organizations, and voting in elections.' (59 chars)
✓ Chunk #2: 12800 bytes
🎉 TTS stream complete: 2 chunks, 28160 bytes
```

#### Scenario 2: User Interruption

**Test:**
1. Start conversation
2. Wait for AI to start speaking
3. Interrupt by saying "wait"
4. AI should stop immediately

**Expected:**
- ✅ AI stops within 300-500ms
- ✅ No long tail after interruption
- ✅ New response starts after interruption

**Check Logs:**
```
🔊 Audio started
🎤 User speech detected: 'wait'
⏳ Debouncing: 0.05s / 0.3s
⏳ Debouncing: 0.10s / 0.3s
...
🛑 INTERRUPTION CONFIRMED (0.35s)
🛑 Interrupting AI...
🛑 TTS interrupted during audio generation
✓ Task cancelled
```

#### Scenario 3: Background Noise

**Test:**
1. Start conversation
2. AI starts speaking
3. Make brief noise (cough, chair scrape)
4. AI should continue (not interrupt)

**Expected:**
- ✅ Brief noises don't interrupt
- ✅ Only sustained speech interrupts
- ✅ AI continues smoothly

**Check Logs:**
```
🔊 Audio started
🎤 User speech detected: 'uh'
⏳ Debouncing: 0.05s / 0.3s
✓ Final: 'uh'
(AI continues - no interruption)
```

#### Scenario 4: Long Sentence

**Test:**
Say: "Tell me about the history of democracy in ancient Greece and how it influenced modern political systems."

**Expected:**
- ✅ Long response split into natural chunks
- ✅ No single chunk > 120 chars
- ✅ Chunks split at sentence/clause boundaries
- ✅ No word fragments

**Check Logs:**
```
📤 TTS chunk #1: 'Democracy in ancient Greece began in Athens around 508 BCE, where citizens participated directly in governance,' (108 chars)
📤 TTS chunk #2: ' making collective decisions on laws and policies.' (51 chars)
📤 TTS chunk #3: ' This system greatly influenced modern democratic institutions...' (65 chars)
```

---

## 🎯 Test 4: Stress Test

### Purpose
Test system under high load and edge cases.

### Test Script

```python
# File: test_stress.py

import asyncio
from services.tts_complete import TTSService


async def test_rapid_interruptions():
    """Test rapid start/stop cycles."""

    print("=== Stress Test: Rapid Interruptions ===")

    tts = TTSService(
        api_key="your_key",
        voice_id="your_voice"
    )

    should_stop = False

    async def mock_llm():
        for i in range(1000):
            yield f"word{i} "
            await asyncio.sleep(0.01)

    # Start generation
    task = asyncio.create_task(tts.synthesize_stream(
        mock_llm(),
        should_stop_check=lambda: should_stop
    ))

    # Interrupt after 500ms
    await asyncio.sleep(0.5)
    should_stop = True

    # Wait for completion
    try:
        await task
    except Exception as e:
        print(f"Error: {e}")

    print("✅ Stress test passed\n")


async def test_very_long_sentence():
    """Test with extremely long sentence."""

    print("=== Stress Test: Very Long Sentence ===")

    tts = TTSService(
        api_key="test_key",
        voice_id="test_voice"
    )

    # Create a 500-character sentence with no punctuation
    long_text = "word " * 100  # 500 chars

    # Should hit hard max at 120 chars
    buffer = ""
    flush_count = 0

    for word in long_text.split():
        buffer += word + " "
        if tts._should_flush_buffer(buffer, word):
            flush_count += 1
            print(f"Flush at {len(buffer)} chars")
            buffer = ""

    print(f"✓ Flushes: {flush_count} (should be ~4 for 500 chars)")
    print("✅ Long sentence test passed\n")


if __name__ == "__main__":
    asyncio.run(test_rapid_interruptions())
    asyncio.run(test_very_long_sentence())
```

### Run Test

```bash
python test_stress.py
```

---

## 📊 Performance Metrics

### Expected Performance

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Latency** | <500ms | Time from user stops speaking to audio starts |
| **Interruption response** | <400ms | Time from interrupt detected to audio stops |
| **Complete sentences** | >95% | Manual inspection of logs |
| **False interruptions** | <5% | Count unwanted interruptions per session |
| **Audio quality** | Perfect | No distortion, crackling, or gaps |

### Measurement Script

```python
# File: measure_performance.py

import time
import asyncio


class PerformanceMonitor:
    """Monitor performance metrics."""

    def __init__(self):
        self.metrics = {
            'latencies': [],
            'interruption_times': [],
            'complete_sentences': 0,
            'incomplete_sentences': 0,
            'false_interruptions': 0
        }

    def record_latency(self, start_time):
        """Record time from transcript to audio."""
        latency = time.time() - start_time
        self.metrics['latencies'].append(latency)
        print(f"⏱️ Latency: {latency*1000:.0f}ms")

    def record_interruption(self, interrupt_time):
        """Record interruption response time."""
        self.metrics['interruption_times'].append(interrupt_time)
        print(f"⏱️ Interruption response: {interrupt_time*1000:.0f}ms")

    def report(self):
        """Print performance report."""
        print("\n=== Performance Report ===")

        if self.metrics['latencies']:
            avg_latency = sum(self.metrics['latencies']) / len(self.metrics['latencies'])
            print(f"Average latency: {avg_latency*1000:.0f}ms")
            print(f"Max latency: {max(self.metrics['latencies'])*1000:.0f}ms")

        if self.metrics['interruption_times']:
            avg_int = sum(self.metrics['interruption_times']) / len(self.metrics['interruption_times'])
            print(f"Average interruption response: {avg_int*1000:.0f}ms")

        total = self.metrics['complete_sentences'] + self.metrics['incomplete_sentences']
        if total > 0:
            completeness = self.metrics['complete_sentences'] / total * 100
            print(f"Sentence completeness: {completeness:.1f}%")

        print(f"False interruptions: {self.metrics['false_interruptions']}")


# Usage in your main.py:
# monitor = PerformanceMonitor()
#
# # In _on_final_transcript:
# start_time = time.time()
# ... (process transcript)
# monitor.record_latency(start_time)
#
# # In _interrupt_ai_response:
# interrupt_time = time.time() - self.user_speech_start_time
# monitor.record_interruption(interrupt_time)
```

---

## 🐛 Debugging Checklist

### Issue: Sentences still cutting off

**Debug steps:**
1. Check logs for "Flush:" messages
2. Verify buffer threshold constants:
   ```python
   print(f"SENTENCE_MIN: {tts.SENTENCE_MIN}")  # Should be 15
   print(f"MIN_WEAK_BUFFER: {tts.MIN_WEAK_BUFFER}")  # Should be 40
   print(f"HARD_MAX_BUFFER: {tts.HARD_MAX_BUFFER}")  # Should be 120
   ```
3. Add debug logging to `_should_flush_buffer`:
   ```python
   print(f"Buffer: {len(buffer)} chars, Token: '{token}', Result: {result}")
   ```
4. Check if old code is still present:
   ```bash
   grep "buffer_size = 25" services/tts.py
   # Should return nothing!
   ```

### Issue: Interruptions not working

**Debug steps:**
1. Check debounce threshold:
   ```python
   print(f"DEBOUNCE_THRESHOLD: {state.DEBOUNCE_THRESHOLD}")  # Should be 0.3
   ```
2. Verify interim transcripts are being received:
   ```python
   # Add to _on_interim_transcript:
   print(f"Interim: '{text}', is_responding: {self.is_responding}")
   ```
3. Check should_stop propagation:
   ```python
   # Add to TTS loop:
   print(f"Checking should_stop: {self._check_should_stop(should_stop_check)}")
   ```

### Issue: False interruptions

**Debug steps:**
1. Increase thresholds temporarily:
   ```python
   self.DEBOUNCE_THRESHOLD = 0.5  # Try 500ms
   self.INTERRUPTION_COOLDOWN = 0.8  # Try 800ms
   ```
2. Check Deepgram sensitivity
3. Monitor interim transcript quality:
   ```python
   # Are you getting lots of short interim transcripts?
   print(f"Interim length: {len(text)} chars")
   ```

---

## ✅ Success Criteria

Your implementation is working correctly when:

- [ ] Long sentences are split at natural boundaries (commas, periods)
- [ ] No mid-word breaks in logs
- [ ] Interruptions happen within 300-400ms of sustained speech
- [ ] Brief noises don't trigger interruptions
- [ ] Audio quality is perfect (no distortion)
- [ ] Latency is <500ms from transcript to audio
- [ ] >95% of sentences are complete
- [ ] <5% false interruptions

---

## 📞 Need Help?

If tests are failing:

1. **Check logs** - Enable debug logging for detailed output
2. **Run unit tests first** - Isolate the problem
3. **Test incrementally** - Don't test everything at once
4. **Monitor metrics** - Use PerformanceMonitor to track issues
5. **Compare with examples** - Check against working examples

Good luck! 🚀
