# Decisions

[README](../../README.md) · [Docs](../index.md)

**When to consult:** when you wonder why kanku works the way it does, or
before proposing to change it. A decision in force is changed by a new
record that supersedes it, never by editing it.

| Record | Decision |
|---|---|
| [0001](0001-plugin-and-adapter.md) | A plugin for the process, an adapter per project |
| [0002](0002-separate-from-sanchin.md) | A plugin of its own, using sanchin's records when present |
| [0003](0003-english.md) | kanku is written in English; the project's documents, in its language |
| [0004](0004-openrouter-only-catalog.md) | OpenRouter is the only catalog in 0.x |
| [0005](0005-log-line-measurement.md) | Measurement is a log line the project emits |
| [0006](0006-plugin-ships-runner.md) | kanku ships the runner and the report, with an escape hatch |
| [0007](0007-dataset-declares-scenarios.md) | The dataset declares the scenarios and the controls |
| [0008](0008-deterministic-gates.md) | Deterministic gates: at launch and in the validator |
| [0009](0009-trust-by-hash.md) | The user approves the adapter, by hash |
| [0010](0010-three-skills-unattended.md) | Three skills; the run goes unattended |
| [0011](0011-append-only-history.md) | Results and decisions are only appended to |
| [0012](0012-general-whys.md) | Every rule carries a general why, never an anecdote |
| [0013](0013-run-report-in-repo.md) | Every run leaves a report in the repository |
