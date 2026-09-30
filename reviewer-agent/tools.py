#!/usr/bin/env python3
"""Tool definitions for the reviewer agent.

Each tool wraps a check from the evaluation toolkit and exposes it with a
name, description, and JSON parameter schema — the standard tool-calling
contract. The agent decides which tools to call; this module executes them.
"""

import contextlib
import io
import sys
from pathlib import Path

# Import the fidelity audit from the sibling module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "data-fidelity-audit"))
import fidelity_audit  # noqa: E402


def _capture(func, *args) -> dict:
    """Run an audit function, capturing its printed report."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = func(*args)
    return {
        "passed": code == 0,
        "detail": buf.getvalue().strip(),
    }


def check_claims(source: str, claims: str) -> dict:
    """Verify numeric claims in a generated report against a source CSV."""
    return _capture(
        fidelity_audit.audit_claims, Path(source), Path(claims)
    )


def diff_workbooks(input: str, output: str) -> dict:
    """Diff an input workbook against the model's output workbook."""
    return _capture(
        fidelity_audit.audit_workbook, Path(input), Path(output)
    )


def qa_deck(deck: str, expected_slides: int | None = None) -> dict:
    """Run mechanical QA checks on a PowerPoint deck."""
    try:
        import pptx  # noqa: F401
    except ImportError:
        return {
            "passed": None,
            "detail": "python-pptx is not installed; deck QA unavailable in this environment.",
        }
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "visual-qa"))
    import pptx_qa

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = pptx_qa.audit(Path(deck), expected_slides)
    return {"passed": code == 0, "detail": buf.getvalue().strip()}


TOOLS = {
    "check_claims": check_claims,
    "diff_workbooks": diff_workbooks,
    "qa_deck": qa_deck,
}

# JSON schemas handed to the model so it knows how to call each tool.
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "check_claims",
            "description": (
                "Verify every numeric claim in a generated report against the "
                "source CSV. Use when the artifact makes factual or numeric claims."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Path to the source CSV."},
                    "claims": {"type": "string", "description": "Path to the generated report (markdown/text)."},
                },
                "required": ["source", "claims"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "diff_workbooks",
            "description": (
                "Compare an input workbook against the model's output workbook. "
                "Reports hidden columns/rows, changed values, and changed formats. "
                "Use when the task produced a spreadsheet."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Path to the original workbook."},
                    "output": {"type": "string", "description": "Path to the model's output workbook."},
                },
                "required": ["input", "output"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "qa_deck",
            "description": (
                "Run mechanical QA on a PowerPoint deck: slide count, fonts, "
                "text overflow, placeholders. Use when the artifact is a slide deck."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "deck": {"type": "string", "description": "Path to the .pptx file."},
                    "expected_slides": {"type": "integer", "description": "Slide count the prompt requested."},
                },
                "required": ["deck"],
            },
        },
    },
]


def execute(name: str, arguments: dict) -> dict:
    """Execute a tool call requested by the model."""
    func = TOOLS.get(name)
    if func is None:
        return {"passed": None, "detail": f"Unknown tool: {name}"}
    try:
        return func(**arguments)
    except Exception as exc:  # noqa: BLE001 — surface tool errors as observations
        return {"passed": False, "detail": f"Tool {name} raised: {exc}"}
