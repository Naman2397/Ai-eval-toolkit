#!/usr/bin/env python3
"""Regenerate the example workbooks (binary .xlsx files aren't stored in git).

Creates:
  input_workbook.xlsx  — the source table the model was given
  output_workbook.xlsx — the model's output: same data, but column D hidden,
                         the "silent layout mutation" the audit is meant to catch

Run from this directory:
  python generate_examples.py
"""

from pathlib import Path

import openpyxl

ROWS = [
    ("Branch", "Checkouts", "Returns", "Net"),
    ("Harborfront", 184500, 162300, 22200),
    ("Old Town", 96200, 88100, 8100),
    ("North Beach", 141300, 129800, 11500),
]

HERE = Path(__file__).resolve().parent


def make_workbook(path: Path, hide_net_column: bool = False) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Circulation"
    for row in ROWS:
        ws.append(list(row))
    if hide_net_column:
        ws.column_dimensions["D"].hidden = True
    wb.save(path)
    print(f"wrote {path}")


if __name__ == "__main__":
    make_workbook(HERE / "input_workbook.xlsx")
    make_workbook(HERE / "output_workbook.xlsx", hide_net_column=True)
