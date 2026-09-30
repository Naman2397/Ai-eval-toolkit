"""Tests for the MCP server: real protocol round-trip over stdio.

Spins up mcp-server/server.py as a subprocess, performs the MCP
initialize handshake, lists tools, and calls check_claims — the same
messages any MCP client would send.
"""

import asyncio
import sys
import unittest
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = Path(__file__).resolve().parent.parent
SERVER = REPO / "mcp-server" / "server.py"
EXAMPLES = REPO / "data-fidelity-audit" / "examples"


async def _session_call(tool_name: str, arguments: dict):
    params = StdioServerParameters(
        command=sys.executable, args=[str(SERVER)]
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool(tool_name, arguments)
            return [t.name for t in tools.tools], result.content[0].text


def _run(coro):
    return asyncio.run(coro)


class TestMCPServer(unittest.TestCase):
    def test_server_lists_three_tools(self):
        names, _ = _run(_session_call(
            "check_claims",
            {"source": str(EXAMPLES / "source_data.csv"),
             "claims": str(EXAMPLES / "claims.md")},
        ))
        self.assertEqual(sorted(names), ["check_claims", "diff_workbooks", "qa_deck"])

    def test_check_claims_catches_fabricated_number(self):
        _, text = _run(_session_call(
            "check_claims",
            {"source": str(EXAMPLES / "source_data.csv"),
             "claims": str(EXAMPLES / "claims.md")},
        ))
        self.assertIn("passed=False", text)
        self.assertIn("96,400", text)


if __name__ == "__main__":
    unittest.main()
