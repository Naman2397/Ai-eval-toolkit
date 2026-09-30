#!/usr/bin/env python3
"""
reviewer-agent — an agentic loop that reviews AI-generated outputs.

The agent picks verification tools for the artifact, runs them, and writes a
structured feedback report (Testing / Model Run / Output / Final outcome).

Usage:
  # Offline demo (scripted reasoning, no API key needed)
  python agent.py --task-type claims \\
      --source ../data-fidelity-audit/examples/source_data.csv \\
      --claims ../data-fidelity-audit/examples/claims.md --mock

  python agent.py --task-type workbook \\
      --input ../data-fidelity-audit/examples/input_workbook.xlsx \\
      --output ../data-fidelity-audit/examples/output_workbook.xlsx --mock

  # Live reasoning against any OpenAI-compatible endpoint
  python agent.py --task-type claims --source ... --claims ... \\
      --api-key "$OPENAI_API_KEY" --model gpt-4o-mini

The loop is hand-rolled on purpose: it shows the underlying agentic pattern
(reason -> act with tools -> observe -> report) without framework magic.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools
from llm import MockClient, OpenAICompatibleClient

MAX_STEPS = 6


def load_system_prompt() -> str:
    return (Path(__file__).resolve().parent / "prompts" / "system.md").read_text()


def describe_task(task: dict) -> str:
    lines = [f"Task type: {task['type']}"]
    for key, value in task["paths"].items():
        lines.append(f"{key}: {value}")
    return "Review the following generated artifact.\n" + "\n".join(lines)


def run(task: dict, llm, out_dir: Path) -> Path:
    system = load_system_prompt()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": describe_task(task)},
    ]

    final_text = ""
    for step in range(1, MAX_STEPS + 1):
        resp = llm.complete(messages, tools.TOOL_SCHEMAS)
        if resp.text:
            messages.append({"role": "assistant", "content": resp.text})
        if not resp.tool_calls:
            final_text = resp.text
            break
        for call in resp.tool_calls:
            result = tools.execute(call.name, call.arguments)
            print(f"[step {step}] tool {call.name}({json.dumps(call.arguments)}) "
                  f"-> passed={result.get('passed')}")
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": f"call_{step}_{call.name}",
                    "type": "function",
                    "function": {"name": call.name,
                                 "arguments": json.dumps(call.arguments)},
                }],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": f"call_{step}_{call.name}",
                "name": call.name,
                "content": json.dumps(result),
                "result": result,  # kept for the mock backend
            })
    else:
        final_text = "(agent hit max steps without a final report)"

    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    report_path = out_dir / f"review-{task['type']}-{stamp}.md"
    report_path.write_text(f"# Agent review — {task['type']}\n\n{final_text}\n")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Reviewer agent for AI-generated outputs.")
    parser.add_argument("--task-type", required=True, choices=["claims", "workbook", "deck"])
    parser.add_argument("--source", help="source CSV (claims task)")
    parser.add_argument("--claims", help="generated report (claims task)")
    parser.add_argument("--input", help="input workbook (workbook task)")
    parser.add_argument("--output", help="model output workbook (workbook task)")
    parser.add_argument("--deck", help="generated deck (deck task)")
    parser.add_argument("--expected-slides", type=int, default=None)
    parser.add_argument("--mock", action="store_true", help="offline scripted demo backend")
    parser.add_argument("--api-key", default=None, help="API key for OpenAI-compatible endpoint")
    parser.add_argument("--base-url", default="https://api.openai.com/v1")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--out-dir", default="reports")
    args = parser.parse_args()

    paths = {k: v for k, v in vars(args).items()
             if k in ("source", "claims", "input", "output", "deck", "expected_slides") and v is not None}
    task = {"type": args.task_type, "paths": paths}

    if args.mock:
        llm = MockClient(task)
        print("Backend: mock (offline demo)")
    elif args.api_key:
        llm = OpenAICompatibleClient(api_key=args.api_key,
                                     base_url=args.base_url, model=args.model)
        print(f"Backend: {args.base_url} ({args.model})")
    else:
        print("Provide --mock for the offline demo or --api-key for live reasoning.",
              file=sys.stderr)
        return 2

    report_path = run(task, llm, Path(args.out_dir))
    print(f"\nReport written to {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
