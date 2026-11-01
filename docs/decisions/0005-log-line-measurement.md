# 0005 — Measurement is a log line the project emits

[README](../../README.md) · [Decisions](index.md)

**Status:** accepted (2026-11-01)

## Decision
The contract between a project and kanku's report is the `llm_call` log
line and the test-start marker ([measurement.md](../measurement.md)). kanku
documents a recipe per framework; it ships no instrumentation.

## Why
Instrumentation lives in the project's code, in whatever framework it
uses. A log line is the narrowest seam every framework can meet, and it
gives exact per-call latency and token counts — cache and reasoning
included — that a histogram can't.

## Alternatives
- **Instrumenters per framework in the plugin** — kanku would chase every
  framework's internals.
- **The provider's billed cost per call** — gives cost but not the per-call
  breakdown that explains it.
