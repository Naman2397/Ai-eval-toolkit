#!/usr/bin/env python3
"""Raw MCP client — no SDK. Proves MCP is just JSON-RPC 2.0 over stdio.

Speaks to mcp-server/server.py with hand-built messages:
  1. initialize          -> handshake, server announces itself
  2. tools/list          -> discover what the server offers
  3. tools/call          -> invoke check_claims
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SERVER = REPO / "mcp-server" / "server.py"
EXAMPLES = REPO / "data-fidelity-audit" / "examples"
PYTHON = "/tmp/mcpenv/bin/python"  # has the mcp SDK (server side needs it)

proc = subprocess.Popen(
    [PYTHON, str(SERVER)],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
)

def send(obj):
    line = json.dumps(obj)
    print(f">>> {obj['method']}")
    proc.stdin.write(line + "\n")
    proc.stdin.flush()

def recv():
    line = proc.stdout.readline()
    obj = json.loads(line)
    if "result" in obj:
        return obj["result"]
    return obj

# 1. Handshake
send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
      "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                 "clientInfo": {"name": "raw-demo", "version": "0.1"}}})
hello = recv()
print(f"    server: {hello['serverInfo']['name']} v{hello['serverInfo']['version']}")
send({"jsonrpc": "2.0", "method": "notifications/initialized"})

# 2. Discover tools
send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
tools = recv()["tools"]
print(f"    tools: {[t['name'] for t in tools]}")

# 3. Call check_claims on the example with the fabricated 96,400 figure
send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
      "params": {"name": "check_claims",
                 "arguments": {"source": str(EXAMPLES / "source_data.csv"),
                               "claims": str(EXAMPLES / "claims.md")}}})
result = recv()["content"][0]["text"]
print("    result:")
print("    " + result.replace("\n", "\n    ")[:600])

proc.terminate()
