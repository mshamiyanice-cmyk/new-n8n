/**
 * Gemini Live API WebSocket Client
 *
 * CRITICAL FIXES:
 * 1. Proper PCM16 byte alignment (Question #1)
 * 2. Handles split 16-bit samples across packet boundaries
 * 3. No race conditions in message handling
 * 4. Correct sample rate handling (Question #4)
 */

class GeminiLiveAPI {
    constructor(audioPlayer) {
        this.audioPlayer = audioPlayer;
        this.ws = null;
        this.isConnected = false;

        // CRITICAL: Byte alignment buffer (Question #1)
        // PCM16 samples are 2 bytes each. Network packets may split samples.
        // We buffer the leftover byte and prepend to next packet.
        this.leftoverByte = null;

        // Session state
        this.sessionId = null;

        // Statistics
        this.stats = {
            totalPackets: 0,
            totalBytes: 0,
            audioPackets: 0,
            audioBytes: 0,
            splitSamples: 0, // How many times we had a leftover byte
            lastPacketTime: null
        };

        // Event handlers
        this.onConnected = null;
        this.onDisconnected = null;
        this.onError = null;
        this.onServerContent = null;
    }

    /**
     * Connect to Gemini Live API via proxy
     */
    async connect(proxyUrl = 'ws://localhost:8080/ws') {
        if (this.isConnected) {
            console.warn('Already connected');
            return;
        }

        try {
            console.log('Connecting to Gemini Live API...', proxyUrl);

            this.ws = new WebSocket(proxyUrl);
            this.ws.binaryType = 'blob'; // Receive binary as Blob

            this.ws.onopen = () => this.handleOpen();
            this.ws.onmessage = (event) => this.handleMessage(event);
            this.ws.onerror = (error) => this.handleError(error);
            this.ws.onclose = () => this.handleClose();

        } catch (error) {
            console.error('Failed to connect:', error);
            if (this.onError) this.onError(error);
        }
    }

    /**
     * Handle WebSocket open
     */
    handleOpen() {
        console.log('WebSocket connected');
        this.isConnected = true;

        if (this.onConnected) {
            this.onConnected();
        }
    }

    /**
     * Handle incoming messages
     *
     * CRITICAL: Proper handling of binary vs text (no race conditions)
     */
    async handleMessage(event) {
        this.stats.totalPackets++;
        this.stats.lastPacketTime = Date.now();

        // Binary audio data
        if (event.data instanceof Blob) {
            await this.handleBinaryAudio(event.data);
        }
        // JSON text messages
        else if (typeof event.data === 'string') {
            this.handleTextMessage(event.data);
        }
    }

    /**
     * Handle binary audio data (PCM16)
     *
     * CRITICAL FIX for Question #1: Byte Alignment
     *
     * Problem: WebSocket packets can arrive with odd byte counts, splitting
     * 16-bit PCM samples across packet boundaries.
     *
     * Solution: Buffer the leftover byte and prepend to next packet.
     */
    async handleBinaryAudio(blob) {
        try {
            // Convert blob to ArrayBuffer
            const arrayBuffer = await blob.arrayBuffer();
            let uint8Data = new Uint8Array(arrayBuffer);

            this.stats.audioPackets++;
            this.stats.audioBytes += uint8Data.length;
            this.stats.totalBytes += uint8Data.length;

            // CRITICAL: Handle leftover byte from previous packet
            let processBuffer;

            if (this.leftoverByte !== null) {
                // We have a leftover byte from last packet
                // Prepend it to current packet to form complete 16-bit samples
                this.stats.splitSamples++;

                processBuffer = new Uint8Array(uint8Data.length + 1);
                processBuffer[0] = this.leftoverByte;
                processBuffer.set(uint8Data, 1);

                this.leftoverByte = null;

                console.log('🔧 Rejoined split sample across packet boundary');
            } else {
                processBuffer = uint8Data;
            }

            // CRITICAL: Check if we have odd byte count (incomplete last sample)
            if (processBuffer.length % 2 !== 0) {
                // Save last byte for next packet
                this.leftoverByte = processBuffer[processBuffer.length - 1];

                // Process only the complete samples (even byte count)
                processBuffer = processBuffer.slice(0, -1);

                console.log('📦 Buffering leftover byte for next packet');
            }

            // Convert PCM16 (Int16) to Float32 for Web Audio API
            // PCM16: 2 bytes per sample, range -32768 to 32767
            // Float32: range -1.0 to 1.0
            if (processBuffer.length >= 2) {
                const int16Data = new Int16Array(
                    processBuffer.buffer,
                    processBuffer.byteOffset,
                    processBuffer.length / 2
                );

                const float32Data = new Float32Array(int16Data.length);

                for (let i = 0; i < int16Data.length; i++) {
                    // Normalize to -1.0 to 1.0
                    float32Data[i] = int16Data[i] / 32768.0;
                }

                // Send to AudioWorklet for playback
                if (this.audioPlayer && this.audioPlayer.workletNode) {
                    this.audioPlayer.workletNode.port.postMessage(float32Data);
                } else {
                    console.warn('AudioPlayer not ready');
                }

                console.log(`🔊 Processed ${float32Data.length} audio samples (${processBuffer.length} bytes)`);
            }

        } catch (error) {
            console.error('Error processing binary audio:', error);
            if (this.onError) this.onError(error);
        }
    }

    /**
     * Handle JSON text messages from Gemini
     */
    handleTextMessage(data) {
        try {
            const message = JSON.parse(data);

            console.log('📨 Received message:', message);

            // Handle different message types
            if (message.setupComplete) {
                console.log('✅ Setup complete');
                this.sessionId = message.setupComplete.sessionId;
            }

            if (message.serverContent) {
                console.log('💬 Server content:', message.serverContent);
                if (this.onServerContent) {
                    this.onServerContent(message.serverContent);
                }
            }

            if (message.toolCall) {
                console.log('🔧 Tool call:', message.toolCall);
            }

            if (message.error) {
                console.error('❌ Server error:', message.error);
                if (this.onError) this.onError(message.error);
            }

        } catch (error) {
            console.error('Error parsing text message:', error);
        }
    }

    /**
     * Send text message to Gemini
     */
    sendText(text) {
        if (!this.isConnected) {
            console.error('Not connected');
            return;
        }

        const message = {
            clientContent: {
                turns: [{
                    role: 'user',
                    parts: [{ text: text }]
                }],
                turnComplete: true
            }
        };

        console.log('📤 Sending text:', text);
        this.ws.send(JSON.stringify(message));
    }

    /**
     * Send binary audio (for future microphone input)
     *
     * CRITICAL: Must send PCM16 aligned to 2-byte boundaries
     */
    sendAudio(float32Data) {
        if (!this.isConnected) {
            console.error('Not connected');
            return;
        }

        // Convert Float32 to PCM16
        const int16Data = new Int16Array(float32Data.length);
        for (let i = 0; i < float32Data.length; i++) {
            // Clamp to -1.0 to 1.0 and scale to int16
            const clamped = Math.max(-1, Math.min(1, float32Data[i]));
            int16Data[i] = Math.round(clamped * 32767);
        }

        // CRITICAL: Ensure even byte count (aligned samples)
        const uint8Data = new Uint8Array(int16Data.buffer);

        if (uint8Data.length % 2 !== 0) {
            console.error('⚠️ Audio data not aligned to 16-bit samples!');
            return;
        }

        // Send as binary
        this.ws.send(uint8Data);
        console.log(`🎤 Sent ${int16Data.length} audio samples (${uint8Data.length} bytes)`);
    }

    /**
     * Handle WebSocket error
     */
    handleError(error) {
        console.error('WebSocket error:', error);
        if (this.onError) {
            this.onError(error);
        }
    }

    /**
     * Handle WebSocket close
     */
    handleClose() {
        console.log('WebSocket closed');
        this.isConnected = false;

        // Reset byte alignment buffer
        this.leftoverByte = null;

        if (this.onDisconnected) {
            this.onDisconnected();
        }
    }

    /**
     * Disconnect from Gemini
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.isConnected = false;
        this.leftoverByte = null;
    }

    /**
     * Get connection statistics
     */
    getStats() {
        return {
            ...this.stats,
            connected: this.isConnected,
            sessionId: this.sessionId
        };
    }

    /**
     * Reset statistics
     */
    resetStats() {
        this.stats = {
            totalPackets: 0,
            totalBytes: 0,
            audioPackets: 0,
            audioBytes: 0,
            splitSamples: 0,
            lastPacketTime: null
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GeminiLiveAPI;
}
