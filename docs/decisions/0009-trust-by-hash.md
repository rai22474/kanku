# 0009 — The user approves the adapter, by hash

[README](../../README.md) · [Decisions](index.md)

**Status:** accepted (2026-11-01)

## Decision
`/kanku:trust` shows the commands, compose files and services the adapter
makes kanku run, asks for an explicit confirmation, and records the
approval with the adapter's hash. The runner refuses to run an adapter whose
hash isn't approved. Only the user can invoke it
(`disable-model-invocation`).

## Why
The runner executes commands from a file in the repository, unattended,
with the real environment file mounted. A changed adapter is new code to
run; a person approves it, not the agent that might have changed it.
