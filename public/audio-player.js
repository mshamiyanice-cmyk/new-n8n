/**
 * Audio Player Manager for Gemini Live API
 *
 * CRITICAL FIX for Question #4: Sample Rate Handling
 * - Gemini outputs 24kHz PCM16
 * - We MUST initialize AudioContext at exactly 24kHz
 * - No resampling to avoid pitch/speed issues
 */

class AudioPlayer {
    constructor() {
        this.audioContext = null;
        this.workletNode = null;
        this.isInitialized = false;

        // Audio configuration (CRITICAL: Must match Gemini output)
        this.SAMPLE_RATE = 24000; // Question #4: Gemini outputs at 24kHz
        this.CHANNELS = 1; // Mono

        // Statistics callback
        this.onStats = null;
    }

    /**
     * Initialize Web Audio API
     *
     * CRITICAL: Force 24kHz sample rate to match Gemini output (Question #4)
     */
    async initialize() {
        if (this.isInitialized) {
            console.warn('Audio player already initialized');
            return;
        }

        try {
            console.log('Initializing audio player...');

            // CRITICAL: Create AudioContext with exact sample rate
            // This prevents browser resampling that can cause pitch issues
            this.audioContext = new AudioContext({
                sampleRate: this.SAMPLE_RATE, // Force 24kHz
                latencyHint: 'interactive' // Low latency for real-time
            });

            console.log(`AudioContext created: ${this.audioContext.sampleRate}Hz`);

            // Verify sample rate (some browsers may not honor the request)
            if (this.audioContext.sampleRate !== this.SAMPLE_RATE) {
                console.warn(
                    `⚠️ AudioContext sample rate mismatch!
                    Requested: ${this.SAMPLE_RATE}Hz
                    Got: ${this.audioContext.sampleRate}Hz

                    This may cause pitch/speed issues (Question #4).
                    The browser may be resampling.`
                );
            }

            // Load AudioWorklet
            await this.audioContext.audioWorklet.addModule('playback.worklet.js');
            console.log('AudioWorklet module loaded');

            // Create worklet node
            this.workletNode = new AudioWorkletNode(
                this.audioContext,
                'playback-processor',
                {
                    numberOfInputs: 0,
                    numberOfOutputs: 1,
                    outputChannelCount: [2], // Output stereo (will duplicate mono)
                }
            );

            // Handle messages from worklet
            this.workletNode.port.onmessage = (event) => {
                this.handleWorkletMessage(event.data);
            };

            // Connect to speakers
            this.workletNode.connect(this.audioContext.destination);

            console.log('AudioWorklet connected to output');

            this.isInitialized = true;

            console.log('✅ Audio player initialized successfully');
            console.log(`   Sample Rate: ${this.audioContext.sampleRate}Hz`);
            console.log(`   State: ${this.audioContext.state}`);

        } catch (error) {
            console.error('Failed to initialize audio player:', error);
            throw error;
        }
    }

    /**
     * Handle messages from AudioWorklet
     */
    handleWorkletMessage(data) {
        switch (data.type) {
            case 'playback_started':
                console.log(`🔊 Playback started (latency: ${data.latency_ms.toFixed(1)}ms)`);
                break;

            case 'underflow':
                console.warn(`⚠️ Audio underflow: ${data.missing} samples missing (count: ${data.count})`);
                break;

            case 'overflow':
                console.warn(`⚠️ Audio overflow: ${data.dropped} samples dropped (count: ${data.count})`);
                break;

            case 'drift_compensation':
                console.log(`🎵 Drift compensation: ${data.compensation.toFixed(4)}x (deviation: ${data.deviation})`);
                break;

            case 'stats':
                this.handleStats(data);
                break;

            case 'reset_complete':
                console.log('🔄 Buffer reset complete');
                break;

            default:
                console.log('Worklet message:', data);
        }
    }

    /**
     * Handle statistics from worklet
     */
    handleStats(stats) {
        console.log(`
📊 Audio Stats:
   Buffer: ${stats.available} samples (${stats.latency_ms.toFixed(1)}ms, ${stats.buffer_fill.toFixed(1)}% full)
   Underflows: ${stats.underflows}
   Overflows: ${stats.overflows}
   Drift: ${stats.drift_compensation.toFixed(4)}x
   Received: ${stats.total_received} samples
   Played: ${stats.total_played} samples
        `);

        if (this.onStats) {
            this.onStats(stats);
        }
    }

    /**
     * Resume audio context (needed after user interaction)
     */
    async resume() {
        if (this.audioContext && this.audioContext.state === 'suspended') {
            console.log('Resuming audio context...');
            await this.audioContext.resume();
            console.log('Audio context resumed');
        }
    }

    /**
     * Reset audio buffer
     */
    reset() {
        if (this.workletNode) {
            this.workletNode.port.postMessage({ command: 'reset' });
        }
    }

    /**
     * Get statistics
     */
    getStats() {
        if (this.workletNode) {
            this.workletNode.port.postMessage({ command: 'getStats' });
        }
    }

    /**
     * Cleanup
     */
    async cleanup() {
        console.log('Cleaning up audio player...');

        if (this.workletNode) {
            this.workletNode.disconnect();
            this.workletNode = null;
        }

        if (this.audioContext) {
            await this.audioContext.close();
            this.audioContext = null;
        }

        this.isInitialized = false;
        console.log('Audio player cleaned up');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AudioPlayer;
}
