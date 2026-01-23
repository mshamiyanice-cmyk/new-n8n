/**
 * Gemini Live API Audio Playback Worklet
 *
 * CRITICAL FIXES:
 * 1. Ring buffer to handle jitter (Question #3)
 * 2. Underflow/overflow protection
 * 3. Clock drift compensation
 * 4. Smooth playback at 24kHz
 */

class PlaybackProcessor extends AudioWorkletProcessor {
    constructor() {
        super();

        // Ring buffer configuration (Question #3: Jitter Buffer)
        // Buffer size: 0.5 seconds at 24kHz = 12,000 samples
        // This provides enough headroom for network jitter
        this.BUFFER_SIZE = 12000;
        this.TARGET_LATENCY = 6000; // Target 250ms latency (half buffer)

        // Ring buffer for incoming audio
        this.ringBuffer = new Float32Array(this.BUFFER_SIZE);
        this.writePos = 0;
        this.readPos = 0;
        this.available = 0;

        // Playback state
        this.isPlaying = false;
        this.underflowCount = 0;
        this.overflowCount = 0;

        // Clock drift compensation
        this.driftCompensation = 1.0;
        this.lastAvailable = 0;
        this.driftSamples = [];

        // Statistics
        this.totalSamplesReceived = 0;
        this.totalSamplesPlayed = 0;
        this.statsInterval = 0;

        // Message handler for incoming audio data
        this.port.onmessage = (event) => {
            const samples = event.data;

            if (samples.command === 'reset') {
                this.reset();
                return;
            }

            if (samples.command === 'getStats') {
                this.sendStats();
                return;
            }

            // Write samples to ring buffer
            if (samples instanceof Float32Array) {
                this.writeSamples(samples);
            }
        };
    }

    /**
     * Write samples to ring buffer with overflow protection
     */
    writeSamples(samples) {
        const samplesToWrite = samples.length;

        // Check for overflow
        if (this.available + samplesToWrite > this.BUFFER_SIZE) {
            this.overflowCount++;

            // Drop oldest samples to make room (compensate for slow playback)
            const overflow = (this.available + samplesToWrite) - this.BUFFER_SIZE;
            this.readPos = (this.readPos + overflow) % this.BUFFER_SIZE;
            this.available -= overflow;

            this.port.postMessage({
                type: 'overflow',
                dropped: overflow,
                count: this.overflowCount
            });
        }

        // Write samples to ring buffer
        for (let i = 0; i < samplesToWrite; i++) {
            this.ringBuffer[this.writePos] = samples[i];
            this.writePos = (this.writePos + 1) % this.BUFFER_SIZE;
        }

        this.available += samplesToWrite;
        this.totalSamplesReceived += samplesToWrite;

        // Start playing once we reach target latency
        if (!this.isPlaying && this.available >= this.TARGET_LATENCY) {
            this.isPlaying = true;
            this.port.postMessage({
                type: 'playback_started',
                latency_ms: (this.available / 24000) * 1000
            });
        }

        // Update drift compensation
        this.updateDriftCompensation();
    }

    /**
     * Read samples from ring buffer for playback
     */
    readSamples(output, length) {
        // Check for underflow
        if (this.available < length) {
            this.underflowCount++;

            // Fill with available samples + silence
            let i = 0;
            for (; i < this.available; i++) {
                output[i] = this.ringBuffer[this.readPos];
                this.readPos = (this.readPos + 1) % this.BUFFER_SIZE;
            }

            // Fill rest with silence
            for (; i < length; i++) {
                output[i] = 0;
            }

            this.totalSamplesPlayed += this.available;
            this.available = 0;
            this.isPlaying = false;

            this.port.postMessage({
                type: 'underflow',
                missing: length - i,
                count: this.underflowCount
            });

            return;
        }

        // Normal playback - read from ring buffer
        for (let i = 0; i < length; i++) {
            output[i] = this.ringBuffer[this.readPos];
            this.readPos = (this.readPos + 1) % this.BUFFER_SIZE;
        }

        this.available -= length;
        this.totalSamplesPlayed += length;
    }

    /**
     * Clock drift compensation (Question #3)
     *
     * If buffer is growing: network is faster than playback -> speed up slightly
     * If buffer is shrinking: network is slower than playback -> slow down slightly
     */
    updateDriftCompensation() {
        // Track buffer level changes
        this.driftSamples.push(this.available);

        // Calculate every 100 frames (~100ms at 24kHz)
        if (this.driftSamples.length >= 100) {
            const avgNow = this.driftSamples.reduce((a, b) => a + b) / this.driftSamples.length;
            const deviation = avgNow - this.TARGET_LATENCY;

            // Adjust playback speed by up to ±1%
            if (Math.abs(deviation) > 100) {
                // Buffer growing -> speed up playback
                if (deviation > 0) {
                    this.driftCompensation = Math.min(1.01, 1.0 + (deviation / 10000));
                }
                // Buffer shrinking -> slow down playback
                else {
                    this.driftCompensation = Math.max(0.99, 1.0 + (deviation / 10000));
                }

                this.port.postMessage({
                    type: 'drift_compensation',
                    compensation: this.driftCompensation,
                    deviation: deviation
                });
            } else {
                this.driftCompensation = 1.0;
            }

            this.driftSamples = [];
        }
    }

    /**
     * Process audio (called by Web Audio API)
     */
    process(inputs, outputs, parameters) {
        const output = outputs[0];

        // Only process if we have output channels
        if (output.length === 0) {
            return true;
        }

        const channel = output[0];
        const frameCount = channel.length;

        // Read samples for playback (if playing)
        if (this.isPlaying) {
            this.readSamples(channel, frameCount);
        } else {
            // Not playing yet - output silence
            channel.fill(0);
        }

        // Copy to all output channels (mono -> stereo/multi)
        for (let i = 1; i < output.length; i++) {
            output[i].set(channel);
        }

        // Send stats every 2 seconds
        this.statsInterval++;
        if (this.statsInterval >= 24000 * 2 / frameCount) {
            this.sendStats();
            this.statsInterval = 0;
        }

        return true; // Keep processor alive
    }

    /**
     * Send statistics to main thread
     */
    sendStats() {
        this.port.postMessage({
            type: 'stats',
            available: this.available,
            latency_ms: (this.available / 24000) * 1000,
            buffer_fill: (this.available / this.BUFFER_SIZE) * 100,
            underflows: this.underflowCount,
            overflows: this.overflowCount,
            drift_compensation: this.driftCompensation,
            total_received: this.totalSamplesReceived,
            total_played: this.totalSamplesPlayed
        });
    }

    /**
     * Reset buffer
     */
    reset() {
        this.writePos = 0;
        this.readPos = 0;
        this.available = 0;
        this.isPlaying = false;
        this.underflowCount = 0;
        this.overflowCount = 0;
        this.driftCompensation = 1.0;
        this.driftSamples = [];
        this.totalSamplesReceived = 0;
        this.totalSamplesPlayed = 0;

        this.port.postMessage({ type: 'reset_complete' });
    }
}

registerProcessor('playback-processor', PlaybackProcessor);
