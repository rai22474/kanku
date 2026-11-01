# 0011 — Results and decisions are only appended to

[README](../../README.md) · [Decisions](index.md)

**Status:** accepted (2026-11-01)

## Decision
Result rows, history sections, protocol-log entries and decision records
are appended to, never rewritten. Rows invalidated by a code change move to
the dataset's history with the reason.

## Why
The next review needs to know what was tried and why it lost. A rewritten
row or record erases exactly that, and looks no different from one that
was always so.
