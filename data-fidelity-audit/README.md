# Data fidelity audit

Two checks for the question that matters most in evaluation: does the output
stay faithful to its source data?

## Claims check

Extracts every number from a generated report and verifies it appears in the
source CSV (individual values and recomputed column totals). Anything else is
flagged — it may be fabricated, miscomputed, or a legitimate estimate that
needs labeling.

```bash
python fidelity_audit.py claims --source examples/source_data.csv --claims examples/claims.md
```

The bundled example flags one invented figure: a "Riverside district" number
that appears nowhere in the source data.

Note: numbers are compared at face value against the source's units. If your
source stores spend in millions, write claims the same way.

## Workbook check

Compares an input workbook against the model's output workbook and reports
the silent mutations a value-only validation misses:

- columns or rows hidden in the output that were visible in the input
- changed sheet dimensions (dropped rows/columns)
- changed cell values and changed number formats

```bash
python fidelity_audit.py workbook --input examples/input_workbook.xlsx --output examples/output_workbook.xlsx
```

The bundled example catches a hidden column D — the output is numerically
identical, but the layout was changed without being asked.

The example workbooks are binary files, so they aren't stored in git.
Generate them first:

```bash
python examples/generate_examples.py
```

## Requirements

- Python 3.9+
- `openpyxl` (for the workbook check only): `pip install openpyxl`
