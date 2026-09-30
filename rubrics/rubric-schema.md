# Rubric schema

Each rubric is a YAML file with three sections: `dimensions`, `verdicts`,
and `rules`. Keep rubrics short — if a dimension can't be scored from the
output and the run trace, it doesn't belong here.

```yaml
name: "example-rubric"
version: 1

dimensions:
  - id: task_completion
    weight: 30
    description: "Did the run deliver the requested artifact?"
    checks:
      - "Artifact exists and opens without errors"
      - "Artifact type matches what was asked (pptx, xlsx, docx)"

  - id: instruction_adherence
    weight: 25
    description: "Did the output follow the prompt's explicit requirements?"
    checks:
      - "Slide/page count matches the requested count"
      - "Requested sections or outline items are all present"
      - "Explicit constraints respected (tone, audience, 'do not ask questions')"

verdicts:
  successful: "All must-pass checks green; minor issues only."
  partially_successful: "Artifact delivered but a must-pass check failed."
  not_successful: "No usable artifact, or most must-pass checks failed."
  not_assessable: "Missing trace or corrupted file; cannot score."

rules:
  - "Score each dimension pass / fail / partial from evidence, not impression."
  - "One fabricated data point fails data fidelity outright."
  - "A silent layout change (hidden column, moved content) is a defect, even if values are right."
  - "Estimates are fine only when labeled as estimates."
```

## Scoring

Weights are a guide for where to spend review time, not a formula to average
blindly. A single critical failure (fabricated data, corrupted file) decides
the verdict regardless of the other dimensions.
