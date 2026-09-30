"""Tests for the data-fidelity audit (claims check + workbook diff)."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parent.parent
EXAMPLES = REPO / "data-fidelity-audit" / "examples"

sys.path.insert(0, str(REPO / "data-fidelity-audit"))
sys.path.insert(0, str(EXAMPLES))
import fidelity_audit  # noqa: E402
import generate_examples  # noqa: E402


def setUpModule():
    # The example workbooks are binary and not stored in git — regenerate
    # them exactly as generate_examples.py defines them.
    if not (EXAMPLES / "input_workbook.xlsx").exists():
        generate_examples.make_workbook(EXAMPLES / "input_workbook.xlsx")
    if not (EXAMPLES / "output_workbook.xlsx").exists():
        generate_examples.make_workbook(
            EXAMPLES / "output_workbook.xlsx", hide_net_column=True
        )


def run(func, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = func(*args)
    return code, buf.getvalue()


class TestClaimsCheck(unittest.TestCase):
    def test_flags_fabricated_number(self):
        code, out = run(
            fidelity_audit.audit_claims,
            EXAMPLES / "source_data.csv",
            EXAMPLES / "claims.md",
        )
        self.assertEqual(code, 1)
        self.assertIn("96,400", out)  # the invented Riverside district figure

    def test_clean_report_passes(self):
        with tempfile.TemporaryDirectory() as d:
            claims = Path(d) / "clean.md"
            claims.write_text(
                "Harborfront drew 184,500 visitors. "
                "North Beach hotel occupancy hit 82%."
            )
            code, out = run(
                fidelity_audit.audit_claims, EXAMPLES / "source_data.csv", claims
            )
        self.assertEqual(code, 0)
        self.assertIn("PASS", out)


class TestWorkbookDiff(unittest.TestCase):
    def test_flags_hidden_column(self):
        code, out = run(
            fidelity_audit.audit_workbook,
            EXAMPLES / "input_workbook.xlsx",
            EXAMPLES / "output_workbook.xlsx",
        )
        self.assertEqual(code, 1)
        self.assertIn("hidden in output", out)
        self.assertIn("'D'", out)

    def test_identical_workbooks_pass(self):
        with tempfile.TemporaryDirectory() as d:
            paths = []
            for name in ("a.xlsx", "b.xlsx"):
                p = Path(d) / name
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.append(["Branch", "Checkouts"])
                ws.append(["Harborfront", 184500])
                wb.save(p)
                paths.append(p)
            code, out = run(fidelity_audit.audit_workbook, *paths)
        self.assertEqual(code, 0)
        self.assertIn("PASS", out)


if __name__ == "__main__":
    unittest.main()
