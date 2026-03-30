#!/usr/bin/env python3
"""
Mock OpenAI-compatible LLM server for testing llmtest-perf.

Simulates realistic latency and streaming responses.
"""

import json
import random
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread


class MockLLMHandler(BaseHTTPRequestHandler):
    """Handler for OpenAI-compatible Chat Completions API."""

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def do_POST(self):
        """Handle POST requests to /v1/chat/completions."""
        if self.path != "/v1/chat/completions":
            self.send_error(404, "Not Found")
            return

        # Read request
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            request_data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        # Extract parameters
        stream = request_data.get("stream", False)
        max_tokens = request_data.get("max_tokens", 256)
        prompt = request_data.get("messages", [{}])[0].get("content", "")

        # Simulate realistic latency (50-150ms base + per-token time)
        base_latency = random.uniform(0.05, 0.15)
        time.sleep(base_latency)

        if stream:
            self._handle_streaming(prompt, max_tokens)
        else:
            self._handle_non_streaming(prompt, max_tokens)

    def _handle_streaming(self, prompt: str, max_tokens: int):
        """Handle streaming response."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        # Simulate token generation (approximately 40 tokens/sec)
        token_delay = 0.025  # 25ms per token
        output_tokens = min(random.randint(50, 150), max_tokens)

        for i in range(output_tokens):
            chunk = {
                "id": "chatcmpl-mock",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "mock-model",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": "word " if i > 0 else ""},
                        "finish_reason": None if i < output_tokens - 1 else "stop",
                    }
                ],
            }

            # Send usage on last chunk
            if i == output_tokens - 1:
                chunk["usage"] = {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": output_tokens,
                    "total_tokens": len(prompt.split()) + output_tokens,
                }

            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
            self.wfile.flush()
            time.sleep(token_delay)

        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def _handle_non_streaming(self, prompt: str, max_tokens: int):
        """Handle non-streaming response."""
        output_tokens = min(random.randint(50, 150), max_tokens)

        # Simulate generation time
        generation_time = output_tokens * 0.025
        time.sleep(generation_time)

        response = {
            "id": "chatcmpl-mock",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "mock-model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a mock response. " * (output_tokens // 5),
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": output_tokens,
                "total_tokens": len(prompt.split()) + output_tokens,
            },
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())


def run_server(port: int = 8000):
    """Run the mock LLM server."""
    server = HTTPServer(("localhost", port), MockLLMHandler)
    print(f"Mock LLM server running on http://localhost:{port}")
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


def run_server_background(port: int = 8000):
    """Run server in background thread."""
    server = HTTPServer(("localhost", port), MockLLMHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


if __name__ == "__main__":
    run_server(8000)
