# 2 · Catalog

[README](../../README.md) · [Docs](../index.md) · [Process](index.md)

Steps 4–6. Takes the requirements and the live catalog; leaves the
[candidates](../artifacts/candidates.md) of each variable regenerated, with
effective prices.

## Step 4 — Filter the catalog, live, and capture the cache price

Search the catalog through the OpenRouter MCP using its server-side
filters — `supported_parameters` (tools, `response_format`), input
modality, context length, `min_tool_success_rate`, minimum indexes, age,
sorted by the relevant index. Don't fetch the whole catalog and filter by
hand. *Why:* the server applies every filter the same way every time; a
filter applied by hand is the one that gets forgotten.

For each survivor, record `prompt`, `completion` and `input_cache_read`
(and `input_cache_write` when published). Then cross-check availability:
the model's endpoints are up and the provider restrictions allow it.

Rules:

- **Live, every time.** Never quote a price or an index from an earlier run,
  even for the same variable a week later. *Why:* prices and indexes change
  between runs, and a remembered figure looks exactly like a current one.
- **Regenerate the candidates of a variable as a whole.** Apply every filter
  to every candidate at once. Don't patch the previous table candidate by
  candidate. *Why:* conclusions from the previous run don't survive a changed
  requirement, and a patched table carries them silently.
- **When re-deciding, look for new candidates.** Re-marking the old ones as
  disqualified isn't a review.

## Step 5 — Distrust a high index on a model with mandatory reasoning

A model whose reasoning is mandatory, at a high default effort, can have the
highest index of its group and still do worse in practice than a candidate
with a lower index and no mandatory reasoning. *Why:* the index is measured
at that effort, but the agent pays it in latency and reasoning tokens on
every call, and reasoning can leak into the output, breaking structured
responses.

When two candidates are close in index and only one has mandatory
reasoning, that is a real reason to prefer the other, not a footnote. If
there is budget for empirical validation, validate that comparison first.

## Step 6 — Compare by the right index, at the effective price

Choose the index from the task profile of step 2, in this order:

1. The model writes or reasons about source code → `coding`.
2. The model decides and executes actions — calls tools, orchestrates
   steps, delegates — → `agentic` (a single tool call per turn is still
   agentic: what is measured is that call's reliability).
3. Otherwise — extraction, synthesis, classification, writing, judging
   against a rubric — → `intelligence`.

Never a generic index when a more specific one applies. *Why:* the indexes
aggregate different tests; comparing by the wrong one ranks the candidates
on work the agent doesn't do.

**Effective price.** Compare cost with the effective price: the cached
share of the input billed at `input_cache_read`, the rest at `prompt`, plus
`completion` — never the raw catalog price. *Why:* agents re-send long, fixed
prompts within a session; a candidate that looks dearer per token can be
cheaper per task once its cache discount applies.

**Pareto.** When no survivor dominates the others — one wins on quality,
another on cost or latency — drop the dominated ones (another is at least as
good on every axis and strictly better on one) and choose a point of the
frontier by the variable's profile: a latency ceiling for interactive
agents, the cheapest that meets a quality floor for high-volume ones,
reliability first for agents that write without review. Write down why that
point.
