# The adapter

[README](../README.md) · [Docs](index.md)

> **Draft.** The fields are settled; the runner and validator that read them
> are being written, and names may still change before 0.1.0.

`.claude/kanku.yaml` is the only place a project tells kanku what it has:
its services, their model variables, how to run their acceptance suites,
where its documents live. The skills, the runner and the validator read it;
none of them knows anything about a particular project. `/kanku:init`
writes it from what already exists, and `/kanku:trust` approves it
([decisions/0009](decisions/0009-trust-by-hash.md)).

## Full example

```yaml
version: 1
language: es                      # language of the project's documents: en | es

catalog:
  provider: openrouter            # the only one in 0.x
  min_tool_success_rate: 0.9      # hard filter for agentic variables
  max_unrated_days: 90            # a missing index disqualifies after this age

env_file: .env                    # where model variables are set; never printed

services:
  app:
    root: app                     # where the service's tests run from
    variables: [APP_MODEL, PLANNER_MODEL, VISION_MODEL]
    acceptance:
      compose: [app/tests/acceptance/docker-compose.acceptance.yml]
      container: app              # the service whose log carries llm_call lines
      health: http://localhost:8060/health
      test: uv run --project app pytest tests/acceptance
      full_stats: bash app/tests/acceptance/run_acceptance.sh all   # step 17
    side_effect_keys: [ADMIN_BOT_TOKEN, ADMIN_CHAT_ID]   # must resolve empty
    classify:                     # failure patterns, added to kanku's own
      model: [JSONDecodeError, LlmCallsLimitExceededError]
      environment: ['weather API .* unreachable']
  memory:
    variables: [MEMORY_MODEL]     # no acceptance: decided from the catalog

benchmark:
  repetitions: 3
  command: null                   # set to replace kanku's runner entirely

docs:
  agents: docs/models/agents.md
  requirements: docs/models/requirements.md
  candidates: docs/models/candidates.md
  benchmarks: docs/models/benchmarks
  protocol: docs/models/benchmark-protocol.md
  decisions: null                 # null: sanchin's decision records if present, else docs/models/decisions.md
  runs: docs/models/runs
  citing:                         # other pages that name variables (step 15)
    - docs/services/*/agents/*.md
    - '*/README.md'
```

## Fields

| Field | Read by | Meaning |
|---|---|---|
| `version` | all | Adapter format version. A change to the format is a major version of kanku. |
| `language` | skills, validator | Language of the project's documents, and the heading set the validator matches ([artifacts/](artifacts/index.md)). |
| `catalog.provider` | skills | The catalog source. Only `openrouter` in 0.x ([decisions/0004](decisions/0004-openrouter-only-catalog.md)). |
| `catalog.min_tool_success_rate` | skills | Hard filter for agentic variables. Default 0.9. |
| `catalog.max_unrated_days` | skills, validator | Age after which a missing index disqualifies. Default 90. |
| `env_file` | runner | The file the containers read model variables from. The runner swaps the variable under test in it and restores it on exit, also on failure. |
| `services.<name>.variables` | all | The model variables the service reads. Every other variable of the service is pinned during a benchmark (step 8). |
| `services.<name>.acceptance` | runner | How to bring the service up and run its scenarios. Absent: the service is decided from the catalog. |
| `services.<name>.acceptance.full_stats` | skills | The full acceptance run with statistics, for step 17. |
| `services.<name>.side_effect_keys` | runner | Keys that must resolve empty in the benchmark containers (step 10). |
| `services.<name>.classify` | report | Extra failure patterns per class: `model`, `environment`. Controls come from the dataset. |
| `benchmark.repetitions` | runner | Repetitions per candidate. Default 3. |
| `benchmark.command` | runner | The project's own runner, replacing kanku's. It receives the same arguments and must leave the same artifacts ([measurement.md](measurement.md)). |
| `docs.*` | all | Paths of the [artifacts](artifacts/index.md). `decisions: null` uses sanchin's records when `.claude/sanchin.yaml` exists. `citing` lists globs of other pages to update and sweep. |
