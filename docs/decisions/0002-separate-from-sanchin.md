# 0002 — A plugin of its own, using sanchin's records when present

[README](../../README.md) · [Decisions](index.md)

**Status:** accepted (2026-11-01)

## Decision
kanku is a plugin separate from sanchin and doesn't require it. When a
project has `.claude/sanchin.yaml`, kanku writes model decisions as
revisions of sanchin's decision records; otherwise it keeps its own.

## Why
sanchin runs the development process; kanku runs the models in production —
another cadence (monthly, not per story), another dependency (a model
catalog). Where they meet is the decision register, and one project should
keep one.

## Alternatives
- **A sanchin role** — every kanku user would install a development process
  they may not want.
- **Always its own register** — a sanchin project would hold decisions in
  two places.
