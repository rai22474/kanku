# The runner

[README](../README.md) · [Docs](index.md)

`scripts/kanku` runs the launch gates, the benchmark and the report. It
needs `uv` (or a `python3` ≥ 3.11 with PyYAML), `docker compose` and `git`.
The `run` skill calls it; you can too.

```text
scripts/kanku gates     --service S --variable V --dataset D [--allow-unset X]...
scripts/kanku benchmark --service S --variable V --dataset D [--allow-unset X]... \
                        [--catalog-date YYYY-MM-DD] [--repetitions N] [--notes TEXT] \
                        model:prompt:completion[:cache_read]...
scripts/kanku report    --service S --variable V --dataset D --run-dir DIR \
                        --candidate model:prompt:completion[:cache_read] \
                        --catalog-date K --other-variables O --commit C --run-date R
scripts/kanku trust     [--approve]
```

Prices are USD per million tokens, read from the catalog the same day
(`--catalog-date`). Model ids may contain colons (`vendor/model:free`); the
prices are read from the right.

## Launch gates

`gates` runs them alone; `benchmark` runs them first and stops on any
problem. Exit code 1 with one line per problem, naming keys, never values.

| Gate | Checks | Step |
|---|---|---|
| `trust` | The adapter's exact content was approved with `/kanku:trust`. Checked first; nothing else runs without it. | — |
| `adapter` | The variable belongs to the service; the service has an acceptance suite. | — |
| `dataset` | The variable's results table exists and has kanku's 16 columns. | 9 |
| `pinned` | Every other model variable of the service is set in the env file, unless named with `--allow-unset` (its decision is the default). | 8 |
| `reaches` | The variable under test reaches the stack's `container` from the env file: with a marker value swapped in, the resolved config shows that marker. A value set under `environment:`, or a variable never passed, would make every candidate run the same model. | 10 |
| `side-effects` | Every `side_effect_keys` entry resolves empty in every service of the compose stack. | 10 |
| `nothing-running` | No compose project with the stack's name is running, and no port it publishes (or the health port) is in use. | 10 |

Every `docker compose` call gets `--env-file <env_file>`, so `${VAR}` in a
compose file sees the swapped value too. The resolved compose
configuration is parsed in memory and never printed;
if `docker compose config` fails, its output is withheld for the same
reason.

## A benchmark

For each candidate, the variable under test is set in the env file —
the line that was there is put back on exit, also on failure or
interruption, leaving lines others changed meanwhile alone. Then, per
repetition: `down -v`, `build`, `up -d`, wait for health, follow the
container's timestamped log, run the test command with the dataset's
scenarios, `down -v`. Finally the report appends the row to the variable's
results section and writes `scenario_breakdown.md` next to the logs.

The commit in the row is `HEAD`, with `+dirty` when tracked files have
uncommitted changes: a row measured on uncommitted code says so.

`report` re-aggregates an existing run directory — to recompute a row
after a report fix, or for runs made by `benchmark.command`.
