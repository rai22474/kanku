# Run report

[README](../../README.md) · [Docs](../index.md) · [Artifacts](index.md)

What one run did, for someone who didn't watch it. One file per run at
`docs.runs/<date>.md`, summarized in the chat.

```markdown
# Model review — 2026-11-01

Scope: all services (or: `PLANNER_MODEL`, by request).

## Changed

| Variable | Before | After | Evidence | Why |
|---|---|---|---|---|
| `PLANNER_MODEL` | `vendor/model-b` | `vendor/model-a` | benchmark | same pass rate, −35 % effective cost, p95 −2 s |

## Unchanged

| Variable | Model | Why it stays |
|---|---|---|

## Grouping

Changes to the grouping, and wiring changed in the code — or "none".

## Fixes

Each fix applied during the run, linking its protocol-log entry.

## Pending

What was left open, and why: no candidate meets the hard requirements, a
service without an acceptance suite, a decision by analogy to confirm.

## Full acceptance

Per affected service: pass rate, p50/p95, cost of the full run; failures
outside the datasets and how each was judged.

## Watch in production

What could still go wrong, and the signal that would show it.
```
