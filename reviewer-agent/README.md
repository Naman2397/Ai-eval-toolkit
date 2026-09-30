# Reviewer agent

An agentic loop that reviews AI-generated outputs the way a human reviewer
would: pick verification tools for the artifact, run them, read the findings,
and write a structured feedback report.

## How it works

```
task -> agent reasons -> calls tools -> observes results -> writes report
```

- `agent.py` — the loop and CLI. Hand-rolled on purpose: it shows the
  underlying agentic pattern (reason, act, observe, report) without framework
  magic.
- `tools.py` — tool definitions with JSON schemas: `check_claims`,
  `diff_workbooks`, `qa_deck`. The agent decides which to call.
- `llm.py` — model backends. `OpenAICompatibleClient` talks to any
  OpenAI-compatible chat endpoint with only the stdlib. `MockClient` is a
  scripted offline demo so the loop runs with no API key.
- `prompts/system.md` — the reviewer instructions: verify data before style,
  keep observations brief, use the Testing / Model Run / Output / Final
  outcome structure.
- `examples/` — sample reports produced by the mock backend.

## Run it

```bash
# Offline demo — no API key needed
python agent.py --task-type claims \
  --source ../data-fidelity-audit/examples/source_data.csv \
  --claims ../data-fidelity-audit/examples/claims.md --mock

python agent.py --task-type workbook \
  --input ../data-fidelity-audit/examples/input_workbook.xlsx \
  --output ../data-fidelity-audit/examples/output_workbook.xlsx --mock

# Live reasoning against any OpenAI-compatible endpoint
python agent.py --task-type claims --source ... --claims ... \
  --api-key "$OPENAI_API_KEY" --model gpt-4o-mini
```

(The example workbooks aren't stored in git — generate them first with
`python ../data-fidelity-audit/examples/generate_examples.py`.)

Reports land in `reports/` (or `--out-dir`). The mock reports in `examples/`
show the shape: the agent ran the fidelity check, found the fabricated
number / hidden column, and wrote it up as Partially successful.

## Design notes

- Tools, not prompts, do the verifying. The model's job is judgment and
  write-up; the checks are deterministic code. That's what keeps the reviews
  honest.
- The mock backend is labeled as a demo everywhere it appears. It shows the
  loop, not model quality.
