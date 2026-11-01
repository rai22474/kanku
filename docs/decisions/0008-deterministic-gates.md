# 0008 — Deterministic gates: at launch and in the validator

[README](../../README.md) · [Decisions](index.md)

**Status:** accepted (2026-11-01)

## Decision
What the process kept learning the hard way is checked by code. **At
launch**, the runner refuses to start unless every other model variable of
the service is set explicitly, no other run holds the compose project or
port, and every side-effect key resolves empty — checked without printing
any value. **In the validator**: candidate states consistent with their
decisions, no pending marker in a decided section, result rows matching the
dataset's scenarios and sharing their commit, results and records only
appended to.

## Why
An unattended run has nobody to catch a skipped check, and each of these
was skipped in practice, more than once, with an agent that knew the rule.
A rule a script enforces holds whether or not the agent remembers it.
