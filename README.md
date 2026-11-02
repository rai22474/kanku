<h1 align="center">kanku</h1>

<p align="center"><b>A repeatable model-selection process for the LLM agents inside your application.</b><br>
Real requirements · live catalog · benchmarks on your own acceptance suite · decisions that stay consistent.</p>

---

> **Status: under construction (0.0.x).** The process, the formats, the
> runner, the validator and the skills are written; the first real run on a
> project comes before 0.1.0.

An application with several LLM agents has to pick a model for each of them,
and pick again every month: the catalog, the prices and the benchmark
indexes move faster than the code. Picking by the highest catalog index
overpays for intelligence an agent doesn't need; picking by price per token
ignores how many tokens the task really takes; and a choice nobody
re-measures goes stale silently.

kanku is a Claude Code plugin that runs one model-selection process, the
same way every time, mostly unattended:

1. **Inventory** — every agent with an embedded LLM, read from the code, and
   what it really needs: tools, structured output, vision, judgement.
2. **Grouping** — agents grouped by requirement profile, not by the
   environment variable they happen to share today.
3. **Catalog** — the live catalog filtered by hard requirements, compared by
   the index that matches the task, priced by what is really paid (cache
   included).
4. **Benchmark** — finalists run against the project's own acceptance
   scenarios, one variable at a time, three repetitions, with per-call
   latency percentiles and effective cost.
5. **Decision** — documented everywhere it is cited, history appended and
   never rewritten, checked for consistency by a validator.

What is specific to a project — its services, variables, compose files,
document paths, failure patterns — goes into an **adapter**
(`.claude/kanku.yaml`); what is left is the process.

**Goal:** the best experience for each agent — the lowest latency and cost
that meet its reliability bar, not the highest index available.

## Requirements

- Claude Code.
- The [OpenRouter](https://openrouter.ai) MCP server, authorized: the
  catalog, its benchmark indexes and its cache prices come from it.
- For benchmarks: an acceptance suite run by pytest, and the agents emitting
  the `llm_call` log line ([docs/measurement.md](docs/measurement.md)).
  Projects without either still get catalog-based decisions.

## Skills

| Skill | What it does |
|---|---|
| `/kanku:init` | Writes `.claude/kanku.yaml` from what the project already has, and reports what isn't in kanku's formats yet. |
| `/kanku:trust` | Shows what the adapter makes kanku run, and records your approval. Only you invoke it. |
| `/kanku:run` | Runs the process unattended, from the inventory to the run report — all services, or the variable you name. |

## Docs

[docs/index.md](docs/index.md).

## License

MIT.
