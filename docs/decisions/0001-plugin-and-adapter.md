# 0001 — A plugin for the process, an adapter per project

[README](../../README.md) · [Decisions](index.md)

**Status:** accepted (2026-11-01)

## Context
The model-selection process grew inside one project: its skill named that
project's services, variables and incidents, and its benchmark scripts were
copied from one service to the next, each copy drifting.

## Decision
The generic process lives in a versioned Claude Code plugin. Each project
describes itself in `.claude/kanku.yaml`. Skills, runner and validator read
the adapter and know nothing else about the project.

## Why
A process meant to be re-run every month, in more than one project, needs
one seam between what is the same everywhere and what differs. A copied
skill can't receive improvements; a pinned plugin can.

## Alternatives
- **Keep it in the project** — the next project starts from a copy.
- **Template repository** — each project ends with its own copy.
