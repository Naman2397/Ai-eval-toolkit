# Feedback report template

Copy this for each model run reviewed. Keep observations brief and factual —
what happened, what the output did, what the verdict is.

```markdown
# Feedback — <task name / artifact name>

## Testing
- Attempts:
- Settings changes:
- Fresh output folder:

## Model Run
- Completed:
- Runtime:
- Errors / rebuilds:
- Validation steps:
- Follow-up questions:

## Output
- <assessment of the delivered artifact>

## Final outcome
- <Successful | Successful, with minor limitations | Partially successful | Not successful | Not assessable>
```

## Filling it in

- **Testing** is about the run conditions: how many attempts, whether any
  model settings were changed, whether a fresh output folder was used.
- **Model Run** is what the trace shows: completion, time taken, errors and
  rebuilds, validation or render checks, and whether the model asked
  follow-up questions (and whether it should have).
- **Output** is the artifact on its own merits: structure, data accuracy,
  template match, visual quality.
- **Final outcome** is one verdict, chosen per the rubric. One line of
  justification if it isn't obvious.

See `examples/` for three worked reports.
