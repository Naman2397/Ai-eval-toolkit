# MCP Server

Exposes the toolkit's verification tools over the **Model Context Protocol (MCP)**,
so any MCP-compatible AI client can call them — Claude Desktop, IDE agents, and
more.

## Why this exists

The `reviewer-agent/` module shows one agent using these tools through hand-written
glue. An MCP server goes one step further: the tools become available to *any*
agent, with zero per-client integration code. The client discovers them via
`tools/list` and invokes them via `tools/call` — both plain JSON-RPC messages
over stdio.

## Tools exposed

| Tool | What it does |
|---|---|
| `check_claims` | Verify numeric claims in a report against a source CSV |
| `diff_workbooks` | Diff an input workbook against a model's output workbook |
| `qa_deck` | Mechanical QA checks on a PowerPoint deck |

## Run it

```bash
pip install "mcp<2"   # server SDK (v1 API)
python server.py       # speaks MCP over stdio
```

## Connect from Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ai-eval-toolkit": {
      "command": "python",
      "args": ["/absolute/path/to/ai-eval-toolkit/mcp-server/server.py"]
    }
  }
}
```

Restart Claude Desktop and ask it to verify a report against a CSV — it will
discover `check_claims` on its own and call it. Paths passed to the tools are
resolved by the server process, so absolute paths are safest.

## Tests

`tests/test_mcp.py` spins up this server as a subprocess and performs a real
MCP round-trip: `initialize` → `tools/list` → `tools/call`, asserting the
fabricated `96,400` figure is caught through the protocol, not just the
underlying function.
