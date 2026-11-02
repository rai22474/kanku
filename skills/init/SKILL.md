---
name: init
description: Sets a project up for kanku, or checks an existing setup — finds the services, model variables, acceptance suites, compose files and model documents the project already has, writes .claude/kanku.yaml with the project's own names and paths, and reports what the validator finds. Use when adopting kanku, when /kanku:run finds no adapter, or after upgrading kanku.
---

Read `${CLAUDE_PLUGIN_ROOT}/docs/adapter.md` and
`${CLAUDE_PLUGIN_ROOT}/docs/artifacts/index.md` first.

## With no adapter yet

1. **Detect** what exists — never assume a layout:
   - **Services and variables:** where the code builds each LLM client and
     which environment variable names its model (`*_MODEL`, settings
     classes, compose `environment:` blocks). Group the variables by the
     service that reads them.
   - **Acceptance suites:** per service, the compose file that brings it up
     for tests, the container whose log carries the model calls, its health
     URL, the pytest command that runs the suite, and the extra environment
     that command needs.
   - **The environment file** the containers read (`env_file:` in the
     compose files). Find its path; **never read or print its content**
     ([working-rules](${CLAUDE_PLUGIN_ROOT}/docs/process/working-rules.md#secrets)).
   - **Side-effect keys:** credentials in that compose stack that act in the
     world — messaging bots, webhooks, admin chats, third-party write APIs.
     Find them by name in the code and compose files, never by value.
   - **Instrumentation:** whether the code already emits the `llm_call` line
     ([measurement.md](${CLAUDE_PLUGIN_ROOT}/docs/measurement.md)), or a
     variant of it.
   - **Model documents** the project already keeps: agent inventories,
     requirements, candidates, benchmark datasets, protocol notes, decision
     records — and sanchin's adapter (`.claude/sanchin.yaml`), whose decision
     records kanku then uses.
   - **The documents' language.**
2. **Ask** only what the repository can't answer, as selectable options with
   a recommendation first.
3. **Write** `.claude/kanku.yaml` with the project's own paths. If the write
   is refused, show the adapter in full in a YAML block so the user can save
   it — never only a summary of it. Point `docs.*` at the documents that
   exist; never move or rename them.
4. **Report the gaps**, each with what closes it, without fixing them here:
   - documents that don't match kanku's formats
     ([artifacts](${CLAUDE_PLUGIN_ROOT}/docs/artifacts/index.md)) — results
     tables without the 16 columns, scenario tables without a *Control*
     column, candidates headings in another shape. Bringing them to the
     format is a change to documents others rely on: offer it, as options;
   - a service whose code doesn't emit the `llm_call` line: its benchmarks
     would have no latency or cost, so offer the recipe in
     [measurement.md](${CLAUDE_PLUGIN_ROOT}/docs/measurement.md);
   - variables with no acceptance suite: they are decided from the catalog.
5. **Run** `"${CLAUDE_PLUGIN_ROOT}/scripts/kanku" --project "$CLAUDE_PROJECT_DIR" check`
   and report.
6. **Trust:** a benchmark runs only once the user approves the adapter. Tell
   the user to run `/kanku:trust` themselves — never run it for them.

## With an adapter (doctor)

Run the validator; compare the adapter with the current format (new or
renamed fields after an upgrade, see `${CLAUDE_PLUGIN_ROOT}/CHANGELOG.md`);
check that every path it names still exists and that every model variable
the code reads is in it, and none it lists has left the code; run
`scripts/kanku trust` to say whether the current adapter is approved.
Report what to change, as options.
