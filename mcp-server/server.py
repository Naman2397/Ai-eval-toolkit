#!/usr/bin/env python3
"""
MCP server for the AI eval toolkit.

Exposes the verification tools as a Model Context Protocol server over
stdio, so any MCP-compatible AI client (Claude Desktop, IDE agents, …)
can call them:

  check_claims   — verify numeric claims in a report against a source CSV
  diff_workbooks — diff an input workbook against a model's output workbook
  qa_deck        — mechanical QA checks on a PowerPoint deck

Run:
  pip install mcp
  python server.py

Then point your MCP client at this script (see README.md for a
Claude Desktop config snippet).
"""

import sys
from pathlib import Path

# Reuse the tool implementations from the reviewer agent.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "reviewer-agent"))

from mcp.server.fastmcp import FastMCP  # noqa: E402

import tools  # noqa: E402

mcp = FastMCP("ai-eval-toolkit")


def _format(result: dict) -> str:
    return f"passed={result['passed']}\n\n{result['detail']}"


@mcp.tool()
def check_claims(source: str, claims: str) -> str:
    """Verify every numeric claim in a generated report against the source CSV.

    Use when an AI-generated artifact makes factual or numeric claims.
    Flags numbers that appear nowhere in the source data — they may be
    fabricated, miscomputed, or unlabeled estimates.
    """
    return _format(tools.check_claims(source, claims))


@mcp.tool()
def diff_workbooks(input: str, output: str) -> str:
    """Compare an input workbook against the model's output workbook.

    Use when the task produced a spreadsheet. Reports hidden columns/rows,
    changed values, and changed number formats — the silent mutations a
    value-only validation misses.
    """
    return _format(tools.diff_workbooks(input, output))


@mcp.tool()
def qa_deck(deck: str, expected_slides: int = 0) -> str:
    """Run mechanical QA checks on a PowerPoint deck.

    Use when the artifact is a slide deck. Checks slide count, fonts in use,
    text overflow, placeholder text, and empty slides. Pass expected_slides=0
    to skip the slide-count check.
    """
    return _format(
        tools.qa_deck(deck, expected_slides if expected_slides else None)
    )


if __name__ == "__main__":
    mcp.run()
