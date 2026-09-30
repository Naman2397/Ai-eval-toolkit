# AI Output Evaluation Toolkit

A practical toolkit for evaluating AI-generated outputs — mostly documents,
spreadsheets, and slide decks. It covers the full review loop: define what
"good" means, test the model run, check the output against its source data,
review the visuals, and write up structured feedback.

Everything here runs on synthetic demo data. The techniques are the same ones
used in real evaluation work; none of the example content is from any client
or employer.

## What's inside

| Folder | What it does |
|---|---|
| `rubrics/` | Evaluation rubrics as YAML: what to score, how much each dimension weighs, and how scores map to a final verdict. |
| `feedback-reports/` | A structured feedback template plus worked examples showing how a review is written up. |
| `data-fidelity-audit/` | A Python tool that checks a generated output against its source data and flags unsupported numbers or silent layout changes. |
| `visual-qa/` | A PowerPoint QA script and checklist: slide counts, fonts, overflow, placeholders, contrast. |
| `prompt-test-harness/` | A run-log template for disciplined prompt testing: attempts, settings, fresh-folder discipline, validation steps. |
| `reviewer-agent/` | An agentic loop that reviews AI-generated outputs: picks verification tools, runs them, and writes a structured feedback report. Runs offline with a mock backend or live via any OpenAI-compatible API. |
| `edge-cases/` | Protocol for handling corrupted or unassessable outputs. |

## Quick start

```bash
# Check numeric claims in a generated report against source data
python data-fidelity-audit/fidelity_audit.py claims \
  --source data-fidelity-audit/examples/source_data.csv \
  --claims data-fidelity-audit/examples/claims.md

# Compare an input workbook against the model's output workbook
python data-fidelity-audit/fidelity_audit.py workbook \
  --input data-fidelity-audit/examples/input_workbook.xlsx \
  --output data-fidelity-audit/examples/output_workbook.xlsx

# QA a generated slide deck
python visual-qa/pptx_qa.py --deck your_deck.pptx --expected-slides 10

# Run the reviewer agent (offline demo — no API key needed)
python reviewer-agent/agent.py --task-type claims \
  --source data-fidelity-audit/examples/source_data.csv \
  --claims data-fidelity-audit/examples/claims.md --mock
```

## Tests

```bash
python -m unittest discover tests
```

No test dependencies — stdlib `unittest` only. Covers the claims check,
the workbook diff, the deck QA logic (via a stubbed `pptx` module), rubric
validity, the agent's tool contract, and an end-to-end mock agent run.

## The review loop

1. **Rubric** — pick or write a rubric for the task type (`rubrics/`).
2. **Test** — run the prompt under controlled conditions and log the run
   (`prompt-test-harness/run-log-template.md`).
3. **Verify data** — every number in the output must trace back to the source
   (`data-fidelity-audit/`). Anything else gets flagged or labeled as an estimate.
4. **Check visuals** — layout, typography, overflow, template match
   (`visual-qa/`).
5. **Write it up** — Testing / Model Run / Output / Final outcome
   (`feedback-reports/feedback-template.md`).

## Verdicts

- **Successful** — met the requirements; no blocking issues.
- **Successful, with minor limitations** — delivered, with small issues noted.
- **Partially successful** — delivered but with material gaps or errors.
- **Not successful** — no usable output, or requirements not met.
- **Not assessable** — not enough information to judge (missing trace, corrupted file).
