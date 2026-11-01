# 1 · Inventory

[README](../../README.md) · [Docs](../index.md) · [Process](index.md)

Steps 1–3. Takes the code; leaves the [agents inventory](../artifacts/agents.md)
current, the grouping validated, and the [requirements](../artifacts/requirements.md)
of each variable written.

## Step 1 — Agents and what they really need

For every agent or runner with an embedded LLM, in every service of the
adapter, record what it needs:

- **Tools.** Real tools, several, with a decision about their sequence — or
  none, or a single trivial one called at the end to save a result?
- **Persistence without review.** Does it write content that is stored
  without a human reading it first?
- **Vision**, **audio**, **files** — any input modality beyond text.
- **Structured output.** Does the caller parse its output against a schema?
- **Judgement.** Does it interpret ambiguous intent, or evaluate another
  model's output?
- **Model actually used**, including fallbacks: `A ?? B` when the agent reads
  `A` and falls back to `B` if `A` is unset.

Read all of this from the code — model factories, entry points, each
agent's construction — and only then compare it with the inventory
document. *Why:* documents describe the intended wiring; the code is what
runs. A variable can be "decided" in the documents and never set anywhere,
and an agent can be rewired without its page changing.

Don't assign variables yet. That is step 2.

## Step 2 — Derive the grouping; don't accept the current one

From the inventory, group the agents by **requirement profile**, not by the
variable they read today, and compare the result with the grouping in the
code. For each group ask:

- Does it mix real tool-calling (weighed by `agentic_index` and
  `tool_success_rate`) with understanding or classification without tools
  (weighed by `intelligence_index`)?
- Does it impose on any agent a requirement that agent doesn't have — vision
  on a text-only agent, tools on a summarizer?
- Does a fallback make an unset variable carry another variable's agents,
  and with them their requirements?

*Why:* a variable shared by agents with different profiles is measured by the
wrong index and pays for the strictest requirement on every agent. The
mismatch is a pattern, not an accident: once one service splits a variable,
the same split is usually due in the others. Check every service on every
run, not only the one in scope.

When the derived grouping differs from the code, that is the signal to
change the wiring — model factories, entry points — and the reason is
written down before going on. Never change wiring without this step for
that group. *Why:* wiring changed on a guess contaminates every benchmark
that follows, and nothing in the results shows it.

## Step 3 — Requirements of each validated variable

For each variable, write or update its row in the requirements document:

- **Hard requirements** disqualify: tools, structured output, modality,
  minimum context, privacy and allowed providers, maximum cost or latency,
  minimum reliability and capability.
- **Desirable requirements** only break ties.

Rules for the thresholds:

- **`tool_success_rate` is a hard filter for agentic variables** —
  the adapter's `catalog.min_tool_success_rate`, 0.9 by default. *Why:* it
  separates models that fail a tool call one time in three from those that
  don't, and an agent that writes without review can't absorb that.
- **It is not enough for agents that interpret intent.** `tool_success_rate`
  says the call came out well-formed, not that it was the right call. An
  agentic variable whose agents translate ambiguous natural language into a
  tool call also gets an `intelligence_index` threshold. *Why:* a
  well-formed wrong call is a silent failure.
- **Never an absolute index value.** Express capability thresholds as a
  percentile of the catalog ("top quartile of models with a reported
  index") or relative to a reference model with a real logical relation
  ("above the model whose output it judges"). *Why:* catalogs recalibrate;
  an absolute number expires in days, while a model's position in the
  distribution moves much less.
- **A judge outranks what it judges.** *Why:* a weaker judge approves its
  betters' mistakes and fails their correct answers.
- **A missing index is an unknown, with an expiry date.** A model without
  the index its variable needs is not disqualified while it is younger than
  `catalog.max_unrated_days` (90 by default); older than that, it is
  treated as failing. *Why:* benchmark coverage lags new releases, so a young
  unrated model is merely unmeasured — but an old one that nobody has
  measured is telling you something.
