# Dataset

[README](../../README.md) · [Docs](../index.md) · [Artifacts](index.md)

A curated list of acceptance scenarios for one variable, dated, and every
comparison run against it. One file per dataset under `docs.benchmarks`,
named `<service>_<VARIABLE>_<date>.md`; `index.md` in that directory lists
them. The date is the date the list was fixed; each result row carries the
date it was run.

```markdown
# Dataset — app / `PLANNER_MODEL` — curated 2026-11-01

Why these scenarios: one per risk category in the variable's requirements.

## Scenarios

| Category | Scenario | Control | Reason |
|---|---|---|---|
| tool-calling | tests/acceptance/test_plan.py::test_creates_plan | | sequenced tools, writes without review |
| structured output | tests/acceptance/test_plan.py::test_plan_schema | | parsed against a schema |
| disambiguation | tests/acceptance/test_chat.py::test_ambiguous_species | | intent from ambiguous text |
| control | tests/acceptance/test_health.py::test_static_reply | yes | no model involved |

## Fixed conditions

Other variables pinned: `APP_MODEL=vendor/model-x`, `VISION_MODEL=vendor/model-v`.
Coupling: none.

## Results — `PLANNER_MODEL`

| Run date | Candidate | Other variables | Commit | Catalog read | Passed | Fail: model | Fail: environment | Latency mean | p50 | p90 | p95 | min | max | Cost/scenario | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-01 | `vendor/model-a` | APP_MODEL=…, VISION_MODEL=… | a1b2c3d | 2026-11-01 | 100 % | 0 % | 0 % | 2.1 s | 1.8 s | 3.9 s | 4.6 s | 0.4 s | 7.2 s | $0.0031 | — |

## History (not comparable)

Rows measured before a change that invalidates them, each block with the
reason.
```

- **Scenarios** is the single source of what the runner runs: it builds the
  test selection from the *Scenario* column, and marks rows with *Control*
  as controls. Nothing else declares them.
- A file may hold several `## Results — <VARIABLE>` sections when another
  variable is compared on the same suite.
- **Failure columns** are shares of the failed scenarios. A failure the
  classifier can't place goes to *Notes* by name.

The validator checks: the scenario table is non-empty and each scenario is
a test node id; each result row's commit is shared by the rows of its
comparison; the *Catalog read* date is present; result and history rows are
only appended — a row that changes or disappears fails.
