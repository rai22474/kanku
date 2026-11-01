# 0004 — OpenRouter is the only catalog in 0.x

[README](../../README.md) · [Decisions](index.md)

**Status:** accepted (2026-11-01)

## Decision
Candidates, prices (cache included), `tool_success_rate`, model age and the
benchmark indexes come from the OpenRouter MCP. It is a declared
dependency; there is no catalog abstraction.

## Why
The process depends on fields only that catalog exposes together, with
server-side filters. An abstraction designed with one implementation is a
guess; it is designed when a second catalog is needed.

## Alternatives
- **A catalog interface from the start** — cost now, for a need not yet seen.
