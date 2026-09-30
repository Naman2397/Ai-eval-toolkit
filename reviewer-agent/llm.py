#!/usr/bin/env python3
"""Model backends for the reviewer agent.

Two backends, one interface:

- OpenAICompatibleClient: talks to any OpenAI-compatible chat completions
  endpoint (OpenAI, Azure, local servers, etc.) using only the stdlib.
- MockClient: scripted reasoning for offline demos. It picks the right tools
  for the task type, then writes the feedback report from the tool results.
  Clearly labeled as a demo — it shows the agent loop, not model quality.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class OpenAICompatibleClient:
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1",
                 model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def complete(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        msg = data["choices"][0]["message"]
        calls = [
            ToolCall(
                name=c["function"]["name"],
                arguments=json.loads(c["function"].get("arguments") or "{}"),
            )
            for c in msg.get("tool_calls") or []
        ]
        return LLMResponse(text=msg.get("content") or "", tool_calls=calls)


# ------------------------------------------------------------------ mock

_PLAN = {
    # task_type -> tools to call, in order
    "claims": [("check_claims", ("source", "claims"))],
    "workbook": [("diff_workbooks", ("input", "output"))],
    "deck": [("qa_deck", ("deck",))],
}


def _tool_results_from(messages: list[dict]) -> list[dict]:
    return [m for m in messages if m.get("role") == "tool"]


def _verdict_from(results: list[dict]) -> str:
    flags = [r["result"].get("passed") for r in results if "result" in r]
    if any(f is False for f in flags):
        return "Partially successful"
    if any(f is None for f in flags):
        return "Not assessable from the provided information"
    return "Successful"


class MockClient:
    """Scripted demo backend. Picks tools by task type, then writes the report."""

    def __init__(self, task: dict):
        self.task = task

    def complete(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        results = _tool_results_from(messages)
        if not results:
            plan = _PLAN.get(self.task["type"], [])
            paths = self.task["paths"]
            calls = []
            for tool_name, arg_keys in plan:
                args = {k: paths[k] for k in arg_keys if k in paths}
                if tool_name == "qa_deck" and "expected_slides" in paths:
                    args["expected_slides"] = paths["expected_slides"]
                calls.append(ToolCall(name=tool_name, arguments=args))
            return LLMResponse(
                text="I'll verify the artifact before writing the review.",
                tool_calls=calls,
            )

        details = "\n\n".join(
            f"Tool `{r['name']}` (passed={r['result'].get('passed')}):\n{r['result'].get('detail')}"
            for r in results
        )
        verdict = _verdict_from(results)
        report = (
            f"## Testing\n"
            f"- Attempts: 1 (mock demo run)\n"
            f"- Settings changes: none\n"
            f"- Fresh output folder: n/a\n\n"
            f"## Model Run\n"
            f"- Completed: yes\n"
            f"- Runtime: n/a (mock)\n"
            f"- Errors / rebuilds: none\n"
            f"- Validation steps: agent tool checks, see below\n"
            f"- Follow-up questions: none\n\n"
            f"## Output\n"
            f"- Tool findings:\n\n{details}\n\n"
            f"## Final outcome\n"
            f"- {verdict}\n\n"
            f"_Drafted by the reviewer agent (mock backend). "
            f"Swap in a real model via --api-key for live reasoning._"
        )
        return LLMResponse(text=report)
