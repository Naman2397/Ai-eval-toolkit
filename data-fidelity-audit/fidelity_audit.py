#!/usr/bin/env python3
"""
fidelity_audit.py — check an AI-generated output against its source data.

Two checks:

  claims    Extract numbers from a generated report (markdown/text) and verify
            each one appears in the source CSV. Flags numbers the model may
            have invented.

  workbook  Compare an input workbook against the model's output workbook.
            Reports hidden columns/rows, changed values, and changed number
            formats — the silent mutations a value-only validation misses.

Usage:
  python fidelity_audit.py claims --source examples/source_data.csv --claims examples/claims.md
  python fidelity_audit.py workbook --input examples/input_workbook.xlsx --output examples/output_workbook.xlsx
"""

import argparse
import csv
import re
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:
    openpyxl = None


# ---------------------------------------------------------------- claims mode

NUMBER_RE = re.compile(
    r"""
    (?<![\w.])                 # not part of a longer token
    (?:\$|€|£)?                # optional currency
    \d{1,3}(?:,\d{3})+         # 1,234 style
    (?:\.\d+)?                 # optional decimals
    %?                         # optional percent
    |
    (?<![\w.])
    (?:\$|€|£)?
    \d+(?:\.\d+)?%             # 45% / 12.5%
    |
    (?<![\w.])
    (?:\$|€|£)
    \d+(?:\.\d+)?              # $12 / $12.5
    (?![\w.])
    |
    (?<![\w.])
    \d+(?:\.\d+)?              # plain 184500 / 42.5
    (?![\w.])
    """,
    re.VERBOSE,
)


def normalize_number(token: str) -> float | None:
    t = token.strip().replace("$", "").replace("€", "").replace("£", "")
    is_percent = t.endswith("%")
    t = t.rstrip("%").replace(",", "")
    try:
        value = float(t)
    except ValueError:
        return None
    # Store percents as their face value (45, not 0.45) so "45%" matches a
    # source column holding 45. Document the convention in the report.
    return round(value, 6)


def load_source_numbers(source_path: Path) -> set[float]:
    numbers: set[float] = set()
    column_totals: dict[str, float] = {}
    with open(source_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key, value in row.items():
                if value is None:
                    continue
                for token in NUMBER_RE.findall(value):
                    n = normalize_number(token)
                    if n is not None:
                        numbers.add(n)
                        column_totals[key] = column_totals.get(key, 0.0) + n
    # Index column totals too, so recomputed aggregations verify.
    for total in column_totals.values():
        numbers.add(round(total, 6))
    return numbers


def audit_claims(source: Path, claims: Path) -> int:
    source_numbers = load_source_numbers(source)
    text = claims.read_text(encoding="utf-8")

    # Skip code blocks — they may contain the source data itself.
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    unsupported: list[tuple[int, str]] = []
    checked = 0
    for lineno, line in enumerate(text.splitlines(), start=1):
        for token in NUMBER_RE.findall(line):
            n = normalize_number(token)
            if n is None:
                continue
            checked += 1
            if n not in source_numbers:
                unsupported.append((lineno, token.strip()))

    print(f"Source values indexed : {len(source_numbers)}")
    print(f"Numeric claims checked: {checked}")
    if not unsupported:
        print("Result: PASS — every numeric claim traces back to the source data.")
        return 0
    print(f"Result: FAIL — {len(unsupported)} claim(s) not found in source data:")
    for lineno, token in unsupported:
        print(f"  line {lineno}: {token}")
    print("\nThese may be fabricated, miscomputed, or legitimate estimates.")
    print("Estimates are fine only when labeled as estimates.")
    return 1


# -------------------------------------------------------------- workbook mode

def sheet_signature(ws) -> dict:
    """Capture the structural facts a value-only diff would miss."""
    hidden_cols = [c for c, dim in ws.column_dimensions.items() if dim.hidden]
    hidden_rows = [r for r, dim in ws.row_dimensions.items() if dim.hidden]
    return {
        "hidden_cols": sorted(hidden_cols),
        "hidden_rows": sorted(hidden_rows),
        "max_row": ws.max_row,
        "max_col": ws.max_column,
    }


def audit_workbook(input_path: Path, output_path: Path) -> int:
    if openpyxl is None:
        print("openpyxl is required: pip install openpyxl", file=sys.stderr)
        return 2

    wb_in = openpyxl.load_workbook(input_path, data_only=False)
    wb_out = openpyxl.load_workbook(output_path, data_only=False)

    issues: list[str] = []

    if set(wb_in.sheetnames) != set(wb_out.sheetnames):
        issues.append(
            f"Sheet names differ: input {wb_in.sheetnames} vs output {wb_out.sheetnames}"
        )

    for name in wb_in.sheetnames:
        if name not in wb_out.sheetnames:
            continue
        ws_in, ws_out = wb_in[name], wb_out[name]
        sig_in, sig_out = sheet_signature(ws_in), sheet_signature(ws_out)

        new_hidden_cols = set(sig_out["hidden_cols"]) - set(sig_in["hidden_cols"])
        if new_hidden_cols:
            issues.append(
                f"Sheet '{name}': columns hidden in output that were visible in input: "
                f"{sorted(new_hidden_cols)}"
            )
        new_hidden_rows = set(sig_out["hidden_rows"]) - set(sig_in["hidden_rows"])
        if new_hidden_rows:
            issues.append(
                f"Sheet '{name}': rows hidden in output that were visible in input: "
                f"{sorted(new_hidden_rows)}"
            )
        if sig_out["max_row"] != sig_in["max_row"] or sig_out["max_col"] != sig_in["max_col"]:
            issues.append(
                f"Sheet '{name}': used range changed "
                f"({sig_in['max_row']}x{sig_in['max_col']} -> {sig_out['max_row']}x{sig_out['max_col']})"
            )

        # Value and number-format diff over the input's used range.
        changed_values = 0
        changed_formats = 0
        for row in ws_in.iter_rows(min_row=1, max_row=sig_in["max_row"],
                                   max_col=sig_in["max_col"]):
            for cell_in in row:
                cell_out = ws_out.cell(row=cell_in.row, column=cell_in.column)
                if cell_in.value != cell_out.value:
                    changed_values += 1
                elif cell_in.number_format != cell_out.number_format:
                    changed_formats += 1
        if changed_values:
            issues.append(
                f"Sheet '{name}': {changed_values} cell value(s) differ from input"
            )
        if changed_formats:
            issues.append(
                f"Sheet '{name}': {changed_formats} cell(s) changed number format "
                f"(verify this was requested)"
            )

    if not issues:
        print("Result: PASS — output workbook matches input structure and values.")
        return 0
    print(f"Result: FAIL — {len(issues)} issue(s) found:")
    for issue in issues:
        print(f"  - {issue}")
    return 1


# --------------------------------------------------------------------- main

def main() -> int:
    parser = argparse.ArgumentParser(description="Audit AI-generated outputs against source data.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_claims = sub.add_parser("claims", help="verify numeric claims against a source CSV")
    p_claims.add_argument("--source", required=True, type=Path)
    p_claims.add_argument("--claims", required=True, type=Path)

    p_wb = sub.add_parser("workbook", help="compare input and output workbooks")
    p_wb.add_argument("--input", required=True, type=Path)
    p_wb.add_argument("--output", required=True, type=Path)

    args = parser.parse_args()
    if args.command == "claims":
        return audit_claims(args.source, args.claims)
    return audit_workbook(args.input, args.output)


if __name__ == "__main__":
    sys.exit(main())
