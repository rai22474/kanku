# Requirements

[README](../../README.md) · [Docs](../index.md) · [Artifacts](index.md)

One row per model variable, after the grouping of step 2 is validated. It
holds the criteria only; which model is chosen lives in
[candidates](candidates.md). At `docs.requirements`.

```markdown
# Requirements

| Variable | Agents | Profile | Index | Hard | Desirable |
|---|---|---|---|---|---|
| `PLANNER_MODEL` | planner | agentic, interprets intent | agentic | tools; `tool_success_rate` ≥ 0.9; intelligence top quartile | p95 < 8 s |
| `APP_MODEL` | summarizer | understanding | intelligence | `response_format`; intelligence top quartile | cache read price |
| `JUDGE_MODEL` | acceptance judge | judge | intelligence | intelligence above `PLANNER_MODEL`'s | — |
```

- **Index:** the one index the variable is compared by
  ([process/catalog.md](../process/catalog.md#step-6--compare-by-the-right-index-at-the-effective-price)).
- **Hard:** disqualifying. Capability thresholds are percentiles or
  relative to a named variable, never absolute values.
- **Desirable:** breaks ties only.

The validator checks that every variable of the adapter has a row, that
*Index* is one of `agentic`, `intelligence`, `coding`, and that a relative
threshold names an existing variable.
