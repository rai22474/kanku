# 0006 — kanku ships the runner and the report, with an escape hatch

[README](../../README.md) · [Decisions](index.md)

**Status:** accepted (2026-11-01)

## Decision
kanku ships the benchmark runner (swap the variable in the environment file
and restore it on exit; bring the compose stack up; wait for health; capture
timestamped logs; run the dataset's scenarios; repeat) and the report
(aggregate, classify failures, compute effective cost, append the result
row). Written in Python, run with `uv`; pytest is the supported runner in
0.x. `benchmark.command` replaces the runner with the project's own.

## Why
The loop and the report are the same in every service; leaving them to each
project is how they got copied and drifted. The escape hatch covers projects
that don't run on docker compose or pytest.

## Alternatives
- **Only an input/output contract** — every project writes the same runner.
