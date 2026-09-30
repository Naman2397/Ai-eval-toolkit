"""Tests for the eval rubrics and the reviewer agent's tool contract."""

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
EXAMPLES = REPO / "data-fidelity-audit" / "examples"

sys.path.insert(0, str(REPO / "reviewer-agent"))
import tools  # noqa: E402
import agent as agent_mod  # noqa: E402
from llm import MockClient  # noqa: E402


class TestRubrics(unittest.TestCase):
    def test_all_rubrics_parse_as_yaml(self):
        rubrics = sorted((REPO / "rubrics").glob("*.yaml"))
        self.assertGreaterEqual(len(rubrics), 3)
        for path in rubrics:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self.assertIsInstance(data, dict, f"{path.name} did not parse to a mapping")
            self.assertTrue(data, f"{path.name} parsed empty")


class TestToolContract(unittest.TestCase):
    def test_unknown_tool_is_reported_not_raised(self):
        result = tools.execute("does_not_exist", {})
        self.assertIsNone(result["passed"])
        self.assertIn("Unknown tool", result["detail"])

    def test_check_claims_catches_fabricated_number(self):
        result = tools.execute(
            "check_claims",
            {"source": str(EXAMPLES / "source_data.csv"),
             "claims": str(EXAMPLES / "claims.md")},
        )
        self.assertFalse(result["passed"])
        self.assertIn("96,400", result["detail"])

    def test_qa_deck_degrades_gracefully_without_pptx(self):
        saved = {k: sys.modules.pop(k)
                 for k in list(sys.modules) if k == "pptx" or k.startswith("pptx.")}
        try:
            result = tools.execute("qa_deck", {"deck": "whatever.pptx"})
        finally:
            sys.modules.update(saved)
        self.assertIsNone(result["passed"])
        self.assertIn("python-pptx", result["detail"])


class TestAgentLoop(unittest.TestCase):
    def test_mock_run_writes_a_verdict_report(self):
        task = {
            "type": "claims",
            "paths": {
                "source": str(EXAMPLES / "source_data.csv"),
                "claims": str(EXAMPLES / "claims.md"),
            },
        }
        with tempfile.TemporaryDirectory() as d:
            report_path = agent_mod.run(task, MockClient(task), Path(d))
            text = report_path.read_text(encoding="utf-8")
        for section in ("## Testing", "## Model Run", "## Output", "## Final outcome"):
            self.assertIn(section, text)
        self.assertIn("Partially successful", text)


if __name__ == "__main__":
    unittest.main()
