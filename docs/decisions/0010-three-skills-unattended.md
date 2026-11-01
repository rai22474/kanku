# 0010 — Three skills; the run goes unattended

[README](../../README.md) · [Decisions](index.md)

**Status:** accepted (2026-11-01)

## Decision
`init` writes the adapter and brings existing documents to the formats;
`trust` approves the adapter; `run` executes the whole process, from
inventory to report, stopping only for the conditions in
[working-rules.md](../process/working-rules.md#when-to-really-stop).

## Why
The process is meant to run once a month. Split into several skills, its
context would have to be handed from one to the next for no gain; run
step by step with a question each, it doesn't get launched.

## Alternatives
- **A skill per phase** — the hand-off costs more than the separation buys.
