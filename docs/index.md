# Docs

[README](../README.md)

Everything kanku does, one document per reader.

| Document | What it contains | When to read it |
|---|---|---|
| [process/](process/index.md) | The process: four phases — inventory, catalog, benchmark, decision — and the working rules for an unattended run. | Read its index first, then only the phase you are in. |
| [artifacts/](artifacts/index.md) | The formats of the documents a run reads and writes, one document each, and what the validator checks in them. | Only the format you are about to write or review. |
| [measurement.md](measurement.md) | The `llm_call` log line and the test-start marker: the contract between the project's code and kanku's report. | When instrumenting a project, or when a report shows no latency. |
| [runner.md](runner.md) | `scripts/kanku`: the launch gates, the benchmark, the report, trust — commands and what each checks. | When a run stops at a gate, or to run a benchmark by hand. |
| [adapter.md](adapter.md) | Every field of `.claude/kanku.yaml`. | When setting up a project, or when a run reads a value you didn't expect. |
| [decisions/](decisions/index.md) | kanku's own decision records. | When you wonder why kanku works the way it does. |
