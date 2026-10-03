"""OpenAI-shaped upstream, reachable only on the disposable internal network."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


response_content = Path("/fixture/response.json").read_text()
state = {"status": 200, "requests": []}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.reply(200, state)

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/control":
            state.update(status=payload["status"], requests=[])
            return self.reply(200, state)
        state["requests"].append({
            "path": self.path, "model": payload.get("model"),
            "provider": payload.get("provider"), "reasoning": payload.get("reasoning"),
            "response_format_type": payload.get("response_format", {}).get("type"),
            "strict": payload.get("response_format", {}).get("json_schema", {}).get("strict"),
            "response_format": payload.get("response_format"),
            "dimensions": payload.get("dimensions"), "max_tokens": payload.get("max_tokens"),
            "upstream_key_only": self.headers.get("Authorization") == "Bearer " + os.environ["EXPECTED_KEY"],
        })
        if state["status"] != 200:
            return self.reply(state["status"], {"error": {
                "message": "SYNTHETIC_UPSTREAM_ERROR", "type": "upstream_error",
                "code": str(state["status"]),
                "details": {"nested": [{"diagnostic": "SYNTHETIC_NESTED_ERROR"}]},
            }})
        if self.path.endswith("/embeddings"):
            return self.reply(200, {"object": "list", "model": payload["model"],
                "data": [{"object": "embedding", "index": 0, "embedding": [0.25] * 1536}],
                "usage": {"prompt_tokens": 12, "total_tokens": 12}})
        self.reply(200, {
            "id": "chatcmpl-jup023-synthetic", "object": "chat.completion", "created": 1,
            "model": payload["model"], "choices": [{"index": 0, "finish_reason": "stop",
                "message": {"role": "assistant", "content": response_content}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        })


HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
