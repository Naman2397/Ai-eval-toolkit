# Prompt test harness

Disciplined prompt testing means the run conditions are recorded, not
remembered. Fill in `run-log-template.md` for every test run — it's the raw
material for the Testing and Model Run sections of the feedback report.

## Rules

1. **One variable at a time.** A test changes the prompt or the settings,
   never both in the same run.
2. **Fresh output folder per attempt.** Never let a rebuild read or overwrite
   a previous attempt's files.
3. **Log settings changes.** If you touched temperature, tools, or skills,
   write it down.
4. **No silent retries.** Every attempt gets a run log, including the failed ones.
5. **Validate before judging.** Format check, render check, then verdict.

## Run log

See `run-log-template.md`.
