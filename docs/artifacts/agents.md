# Agents inventory

[README](../../README.md) · [Docs](../index.md) · [Artifacts](index.md)

Every agent or runner with an embedded LLM, as the code wires it — not as
the documents say it is wired. One section per service. At `docs.agents`.

```markdown
# Agents

Regenerated: 2026-11-01. Source of truth: the code; this page is checked
against it on every run.

## <service>

| Agent | Profile | Model used | Requirements | Source |
|---|---|---|---|---|
| planner | agentic | `PLANNER_MODEL ?? APP_MODEL` | tools (4, sequenced), writes without review | src/app/planner.py:42 |
| summarizer | understanding | `APP_MODEL` | structured output | src/app/summary.py:18 |
| photo-reader | vision | `VISION_MODEL` | image input, structured output | src/app/vision.py:30 |
```

- **Profile:** `agentic` (decides and executes tool calls), `understanding`
  (extraction, synthesis, classification, writing), `coding`, `vision`,
  `judge` (evaluates another model's output). An agent with two profiles
  lists both.
- **Model used:** the variable it reads, with its fallback chain (`A ?? B`).
- **Source:** `file:line` where the model is built for that agent.

The validator checks that every variable named in *Model used* is a
variable of that service in the adapter.
