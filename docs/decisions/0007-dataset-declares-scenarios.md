# 0007 — The dataset declares the scenarios and the controls

[README](../../README.md) · [Decisions](index.md)

**Status:** accepted (2026-11-01)

## Decision
The runner builds the test selection and the control list from the
dataset's scenario table. Neither is written anywhere else.

## Why
A scenario list kept in a script and again in the dataset drifts, and then
result rows claim scenarios they didn't run. One source lets the validator
check every row against it.
