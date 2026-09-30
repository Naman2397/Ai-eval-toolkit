# Agent review — claims

## Testing
- Attempts: 1 (mock demo run)
- Settings changes: none
- Fresh output folder: n/a

## Model Run
- Completed: yes
- Runtime: n/a (mock)
- Errors / rebuilds: none
- Validation steps: agent tool checks, see below
- Follow-up questions: none

## Output
- Tool findings:

Tool `check_claims` (passed=False):
Source values indexed : 24
Numeric claims checked: 8
Result: FAIL — 1 claim(s) not found in source data:
  line 10: 96,400

These may be fabricated, miscomputed, or legitimate estimates.
Estimates are fine only when labeled as estimates.

## Final outcome
- Partially successful

_Drafted by the reviewer agent (mock backend). Swap in a real model via --api-key for live reasoning._
