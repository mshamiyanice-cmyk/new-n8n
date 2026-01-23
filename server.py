#!/usr/bin/env python3
"""
Gemini Live API WebSocket Proxy Server
Addresses: Auth management, SSL latency, and binary transparency
"""

import asyncio
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import aiohttp
from aiohttp import web, WSMsgType
import google.auth
from google.auth.transport.requests import Request
import google.oauth2.credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")

# CRITICAL: Token caching to avoid SSL handshake latency on every connection
class TokenCache:
    """Cache access tokens to reduce auth latency (Question #5)"""
    def __init__(self, refresh_margin_seconds: int = 300):
        self.token: Optional[str] = None
        self.expiry: Optional[datetime] = None
        self.refresh_margin = timedelta(seconds=refresh_margin_seconds)
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        """Get cached token or fetch new one"""
        async with self._lock:
            now = datetime.now()

            # Return cached token if still valid
            if self.token and self.expiry and (self.expiry - now) > self.refresh_margin:
                logger.debug("Using cached access token")
                return self.token

            # Fetch new token
            logger.info("Fetching new access token")
            credentials, project = google.auth.default(
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )

            # Refresh if needed
            if not credentials.valid:
                if credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                else:
                    # Force token refresh
                    auth_req = Request()
                    credentials.refresh(auth_req)

            self.token = credentials.token

            # Set expiry with safety margin
            if hasattr(credentials, 'expiry') and credentials.expiry:
                self.expiry = credentials.expiry
            else:
                # Default to 1 hour if no expiry provided
                self.expiry = now + timedelta(hours=1)

            logger.info(f"Token refreshed, expires at {self.expiry}")
            return self.token

# Global token cache
token_cache = TokenCache()


async def proxy_websocket(request: web.Request) -> web.WebSocketResponse:
    """
    WebSocket proxy handler

    CRITICAL FIXES:
    1. Binary transparency - passes through exact chunk sizes (Question #2)
    2. No buffering - immediate send to prevent jitter (Question #3)
    3. Cached auth - reduces SSL handshake latency (Question #5)
    """

    # Initialize client WebSocket
    ws_client = web.WebSocketResponse(
        heartbeat=30,
        max_msg_size=0  # No size limit for binary chunks
    )
    await ws_client.prepare(request)

    logger.info("Client WebSocket connected")

    # Get cached access token (avoids SSL handshake delay)
    try:
        access_token = await token_cache.get_token()
    except Exception as e:
        logger.error(f"Failed to get access token: {e}")
        await ws_client.close(code=1008, message=b"Auth failed")
        return ws_client

    # Build Gemini API WebSocket URL
    gemini_url = (
        f"wss://{LOCATION}-aiplatform.googleapis.com/ws/google.cloud.aiplatform.v1beta1.LlmBidiService/BidiGenerateContent"
        f"?access_token={access_token}"
    )

    # Connect to Gemini API
    session = aiohttp.ClientSession()
    try:
        ws_server = await session.ws_connect(
            gemini_url,
            heartbeat=30,
            max_msg_size=0,  # No size limit
            compress=0  # CRITICAL: Disable compression to preserve chunk boundaries
        )
        logger.info("Connected to Gemini API")

        # Send initial setup message
        setup_msg = {
            "setup": {
                "model": f"models/{GEMINI_MODEL}",
                "generation_config": {
                    "response_modalities": ["AUDIO"],
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {
                                "voice_name": "Aoede"
                            }
                        }
                    }
                }
            }
        }
        await ws_server.send_json(setup_msg)
        logger.info("Setup message sent")

        # Bidirectional relay
        async def client_to_server():
            """Forward client messages to Gemini API"""
            try:
                async for msg in ws_client:
                    if msg.type == WSMsgType.TEXT:
                        logger.debug(f"Client->Server TEXT: {msg.data[:100]}")
                        await ws_server.send_str(msg.data)

                    elif msg.type == WSMsgType.BINARY:
                        # Binary audio from client (microphone input)
                        logger.debug(f"Client->Server BINARY: {len(msg.data)} bytes")
                        await ws_server.send_bytes(msg.data)

                    elif msg.type == WSMsgType.CLOSE:
                        logger.info("Client closed connection")
                        await ws_server.close()
                        break

                    elif msg.type == WSMsgType.ERROR:
                        logger.error(f"Client error: {ws_client.exception()}")
                        break
            except Exception as e:
                logger.error(f"Client->Server error: {e}")
            finally:
                if not ws_server.closed:
                    await ws_server.close()

        async def server_to_client():
            """
            Forward Gemini API responses to client

            CRITICAL: This preserves exact chunk sizes from Gemini (Question #2)
            No buffering or merging - each binary message is sent immediately
            """
            try:
                async for msg in ws_server:
                    if msg.type == WSMsgType.TEXT:
                        logger.debug(f"Server->Client TEXT: {msg.data[:100]}")
                        await ws_client.send_str(msg.data)

                    elif msg.type == WSMsgType.BINARY:
                        # CRITICAL: Send binary data immediately without buffering
                        # This preserves the exact chunk boundaries from Gemini
                        chunk_size = len(msg.data)
                        logger.debug(f"Server->Client BINARY: {chunk_size} bytes")

                        # Send raw bytes directly - no transformation
                        await ws_client.send_bytes(msg.data)

                    elif msg.type == WSMsgType.CLOSE:
                        logger.info("Server closed connection")
                        await ws_client.close()
                        break

                    elif msg.type == WSMsgType.ERROR:
                        logger.error(f"Server error: {ws_server.exception()}")
                        break
            except Exception as e:
                logger.error(f"Server->Client error: {e}")
            finally:
                if not ws_client.closed:
                    await ws_client.close()

        # Run both directions concurrently
        await asyncio.gather(
            client_to_server(),
            server_to_client()
        )

    except Exception as e:
        logger.error(f"WebSocket proxy error: {e}")
        if not ws_client.closed:
            await ws_client.close(code=1011, message=str(e).encode())

    finally:
        await session.close()
        logger.info("WebSocket proxy closed")

    return ws_client


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "project_id": PROJECT_ID,
        "location": LOCATION,
        "model": GEMINI_MODEL
    })


def create_app() -> web.Application:
    """Create and configure the aiohttp application"""
    app = web.Application()

    # Add CORS middleware
    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            # Handle preflight requests
            if request.method == "OPTIONS":
                response = web.Response()
            else:
                response = await handler(request)

            # Add CORS headers
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'

            return response
        return middleware_handler

    app.middlewares.append(cors_middleware)

    # Routes
    app.router.add_get('/ws', proxy_websocket)
    app.router.add_get('/health', health_check)

    return app


def main():
    """Run the server"""
    if not PROJECT_ID:
        logger.error("GOOGLE_PROJECT_ID environment variable not set")
        return

    logger.info(f"Starting Gemini Live API Proxy")
    logger.info(f"Project: {PROJECT_ID}")
    logger.info(f"Location: {LOCATION}")
    logger.info(f"Model: {GEMINI_MODEL}")

    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()
