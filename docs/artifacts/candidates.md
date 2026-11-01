# Candidates

[README](../../README.md) · [Docs](../index.md) · [Artifacts](index.md)

One section per variable, regenerated whole on each run that reviews it.
At `docs.candidates`.

```markdown
# Candidates

Catalog read: 2026-11-01.

## `PLANNER_MODEL` — decided (`vendor/model-a`, 2026-11-01)

Filters from the requirements: tools, `tool_success_rate` ≥ 0.9,
intelligence ≥ 61.2 (top quartile today).

| Model | Prompt $/M | Completion $/M | Cache read $/M | Index | tool_success_rate | Mandatory reasoning | Age (days) | Verdict | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `vendor/model-a` | 0.40 | 1.60 | 0.10 | agentic 58 | 0.97 | no | 120 | chosen | won the benchmark tie on effective price |
| `vendor/model-b` | 0.30 | 2.50 | — | agentic 63 | 0.95 | yes (high) | 40 | discarded | p95 3× model-a; reasoning leaked into JSON |
| `vendor/model-c` | 0.20 | 0.80 | 0.05 | — | 0.93 | no | 30 | unknown | no index yet, under 90 days |

### Decision

Chosen: `vendor/model-a`. Benchmark on [dataset 2026-11-01](benchmarks/app_PLANNER_MODEL_2026-11-01.md):
tied with model-b on pass rate (100 %), cheaper by effective price and
faster at p95. Revision recorded in [ADR-007](adr/ADR-007.md).
```

**Heading:** `` ## `<VARIABLE>` — <status> (`<model>`, <date>) `` — status is
`decided`, `pending` or `default` (unset on purpose: the service's default
applies). `pending` has no model in the heading.

**Verdict** is one of `chosen`, `finalist`, `discarded`, `unknown`.
*Discarded* says why in *Notes*. *Unknown* is a missing index on a model
younger than `catalog.max_unrated_days`.

**Decision** starts with `Chosen: <model>`, or says why the variable is
pending — and, for a decision without a benchmark, whether it is by
analogy (naming the variable) or catalog-only.

The validator checks, per section:

- `decided` ⇔ exactly one `chosen` row, and that model is the one in the
  heading and after `Chosen:`.
- `pending` ⇔ no `chosen` row, and no `Chosen:` line.
- No pending marker (the language's word for *pending*) left in a
  `decided` section's heading or decision.
- Every price column is filled or `—`; the catalog-read date is present.
