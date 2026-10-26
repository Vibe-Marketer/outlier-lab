"""Small stdlib client for TokScript's authenticated streamable HTTP MCP."""
import json
import os
import urllib.request
from pathlib import Path

ENDPOINT = "https://api.tokscript.com/mcp"


def load_key(root=None):
    if os.environ.get("TOKSCRIPT_API_KEY"):
        return os.environ["TOKSCRIPT_API_KEY"]
    path = (root or Path(__file__).resolve().parent) / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith("TOKSCRIPT_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


class TokScript:
    def __init__(self, key=None):
        key = key or load_key()
        if not key:
            raise ValueError("TOKSCRIPT_API_KEY is not configured")
        self.headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"}
        self.sequence = 0
        initialized = self.rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                          "clientInfo": {"name": "outlier-lab", "version": "1.0"}})
        self.headers["MCP-Protocol-Version"] = initialized["protocolVersion"]
        self.rpc("notifications/initialized", notify=True)

    def rpc(self, method, params=None, notify=False):
        self.sequence += 1
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        if not notify:
            payload["id"] = self.sequence
        request = urllib.request.Request(ENDPOINT, json.dumps(payload).encode(), self.headers, method="POST")
        # Never blindly retry POST: bulk submissions can have side effects.
        with urllib.request.urlopen(request, timeout=120) as response:
            if response.headers.get("Mcp-Session-Id"):
                self.headers["Mcp-Session-Id"] = response.headers["Mcp-Session-Id"]
            raw = response.read().decode()
        if notify:
            return None
        if raw.lstrip().startswith("{"):
            answer = json.loads(raw)
        else:
            answer = next((json.loads(line[5:]) for line in raw.splitlines()
                           if line.startswith("data:") and json.loads(line[5:]).get("id") == self.sequence), None)
        if not answer:
            raise RuntimeError("TokScript returned no MCP result")
        if answer.get("error"):
            raise RuntimeError("TokScript MCP request failed: " + str(answer["error"].get("message", "Unknown error")))
        return answer["result"]

    def call(self, name, **arguments):
        result = self.rpc("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            raise RuntimeError("TokScript tool failed: " + " ".join(c.get("text", "") for c in result.get("content", [])))
        if result.get("structuredContent") is not None:
            return result["structuredContent"]
        texts = [c["text"] for c in result.get("content", []) if c.get("type") == "text"]
        for text in texts:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        raise RuntimeError("TokScript tool returned no structured JSON")
