---
name: run
description: Runs kanku's model-selection process on this project, unattended from the inventory of agents to the run report — catalog filtered live from OpenRouter, benchmarks against the project's own acceptance scenarios behind launch gates, decisions documented and validated. Use when the user wants to review, choose or re-check the models of the project's LLM agents, or one model variable. Benchmarks run only on an adapter the user approved themselves with /kanku:trust — never approve it for them.
---

Read `${CLAUDE_PLUGIN_ROOT}/docs/process/index.md` and
`${CLAUDE_PLUGIN_ROOT}/docs/process/working-rules.md` first; then each
phase's page as you reach it, and each artifact's format before writing it
(`${CLAUDE_PLUGIN_ROOT}/docs/artifacts/`). The process lives there; this
skill only says how to drive it here.

## Before step 1

- **Adapter.** With no `.claude/kanku.yaml`, stop and offer `/kanku:init`.
  Don't guess a layout.
- **Catalog.** The OpenRouter MCP server must answer. If its tools are
  missing or need authorization, stop and tell the user to authorize it
  (`/mcp` in an interactive session). *Why:* without the live catalog every
  later step works from stale prices and indexes.
- **Trust.** Run `"${CLAUDE_PLUGIN_ROOT}/scripts/kanku" --project "$CLAUDE_PROJECT_DIR" trust`.
  When it says *NOT approved*, the inventory, catalog and catalog-only
  decisions still go ahead, but no benchmark launches: tell the user that
  `/kanku:trust` approves the adapter — never run the approval yourself —
  and list the comparisons left pending for it in the run report.
- **Scope.** Every service by default; a variable when the user names one.
  The inventory covers every service either way
  ([scope](${CLAUDE_PLUGIN_ROOT}/docs/process/index.md#scope-of-a-run)).

## Driving the benchmark

`scripts/kanku` is `${CLAUDE_PLUGIN_ROOT}/scripts/kanku --project "$CLAUDE_PROJECT_DIR"`
([runner.md](${CLAUDE_PLUGIN_ROOT}/docs/runner.md)).

- Run `scripts/kanku gates …` first; a gate problem is fixed at its cause
  (pin the variable, blank the key, wait for the other run), never worked
  around. A variable whose decision is the default is passed with
  `--allow-unset`.
- Launch `scripts/kanku benchmark …` in the background, with the prices
  read from the catalog today (`--catalog-date`), and go on with other
  variables. Never state, interpret or write anything about a comparison
  until its process has finished and you have read its output.
- The runner appends the rows and writes the per-scenario breakdown; read
  the breakdown before interpreting
  ([step 12](${CLAUDE_PLUGIN_ROOT}/docs/process/benchmark.md#step-12--interpret-without-assuming-log-every-fix-at-once)).

## Writing the documents

After every document you write, the hook validates it; fix what it reports
before moving on. Before the run report, run `scripts/kanku check` over
everything and do the consistency sweep of step 16 on the prose it can't
read. Commit locally when the run ends; never push.

## Stop only for

What [working-rules.md](${CLAUDE_PLUGIN_ROOT}/docs/process/working-rules.md#when-to-really-stop)
lists. Everything else proceeds without asking.
