# 3 · Benchmark

[README](../../README.md) · [Docs](../index.md) · [Process](index.md)

Steps 7–14. Takes the finalists of a variable and its curated
[dataset](../artifacts/dataset.md); leaves result rows in the dataset and
every fix in the [protocol log](../artifacts/protocol.md).

## Step 7 — Validate empirically, unless one of two exceptions holds

The catalog doesn't predict tool-calling reliability with the project's own
tools, the latency cost of mandatory reasoning, or reasoning leaking into
structured output. So by default, the finalists are benchmarked. Skip it
only when:

- **(a)** there is empirical evidence from a variable with an equivalent
  task profile — the decision then says, explicitly, that it is *by analogy*
  with that variable, not a measurement of its own; or
- **(b)** the service has no acceptance suite, or doesn't emit the
  [measurement](../measurement.md) line — the decision is made from the
  catalog, and the gap is recorded in the run report.

*Why (b) doesn't block:* building a benchmark from scratch is a project of its
own; a documented catalog decision now beats no decision.

## Step 8 — One variable at a time; pin every other

Compare candidates for one variable while every other model variable of
the service is **set explicitly** to its decided value — not left to its
default. The runner refuses to start otherwise (a launch gate).
*Why:* the variables resolve largely disjoint agents, so one at a time is
enough, and far cheaper than combinations. But an unset variable can make
the one under test carry its agents through a fallback, and nothing in the
results shows it.

When a fallback really couples two variables, the variable under test
includes the coupled one's state: write it into that comparison's
conditions, explicitly.

## Step 9 — Reuse the dataset before creating one

A dataset is the curated list of scenarios for a variable, dated. Rules for
building one:

1. List the risk categories in the variable's requirements: tool-calling,
   structured output, vision, multi-turn, disambiguation, judged answers…
2. Pick **one** existing acceptance scenario per category — the simplest
   that exercises it, not the longest.
3. Add at least one **control** scenario, expected to behave the same with
   any model. *Why:* it tells an environment failure from a model failure,
   and warns when a control starts depending on the model.
4. Keep it short — 8 to 12 scenarios. *Why:* it runs three times per
   candidate.

Reuse an existing dataset when its scenarios still fit. Comparing another
variable against the same suite adds a `## Results — <VARIABLE>` section to
the same file. Create a new dataset (new date) only when the list of
scenarios really changes. *Why:* rows measured on different scenarios aren't
comparable, and the date of the dataset is what keeps them apart.

## Step 10 — Check the environment before launching

Before any benchmark or acceptance run — the first four are launch gates
the runner enforces:

- **Nothing else running** on the same compose project name or host port.
  *Why:* two runs on the same project stop each other's containers and
  contaminate the environment file. The check holds only at the instant of
  launching; with several sessions on the same checkout, tell the others
  before a long run.
- **Credentials with real side effects are blank.** When the compose file
  loads the real environment file, every key the adapter lists as
  `side_effect_keys` — messaging bots, webhooks, third-party APIs that act —
  must resolve empty in the container. *Why:* an ephemeral test container
  with production credentials acts in production.
- **Verified by code, never by printing.** Check resolved values by parsing
  `docker compose config --format json` and reporting only empty or not.
  *Why:* a printed configuration puts every secret into the session history.
- The variable under test reaches the container through the file the
  container reads, not through the shell that launches it nor a value the
  compose file sets (a launch gate). *Why:* a variable that doesn't reach
  the container makes every candidate run the same model, and the rows
  look like a real comparison.
- Known environment regressions in the protocol log are checked before a
  new failure is blamed on a model.

## Step 11 — Run

Three repetitions per candidate, the dataset's full scenario list (a
subset only as a deliberate smoke test, noted as such), fresh containers
between repetitions, the same commit for every candidate of a comparison.
*Why:* models are non-deterministic; one run doesn't tell a systematic failure
from a one-off.

Launch it in the background and work on other variables while it runs;
launch independent comparisons in parallel when they don't share a port or a
compose project. *Why:* an unattended run should take as long as its slowest
comparison, not the sum of all of them.

## Step 12 — Interpret without assuming; log every fix at once

A new failure or a suspicious latency is investigated before concluding
"the model is bad": the per-scenario breakdown, percentiles rather than the
mean, reasoning and cached tokens per call. *Why:* the project's own bugs —
an image sent to a text-only model, reasoning leaking into a reply — look
exactly like model failures in the aggregate.

A bounded, clear fix is applied in the code, and the affected benchmark is
repeated with it before anything is concluded about that candidate. Rows
measured before the fix move to the dataset's history. Each fix is written
to the protocol log **when it is applied**: what was found, the root cause,
what changed. *Why:* nobody watches an unattended run; whoever reads the
documents later must not need the git log to learn it happened.

Failures the classifier can't place are listed in the row's notes, never
folded into a percentage.

## Step 13 — Ties: decide

When two candidates tie on reliability — the same pass rate, the same
failures classified as control — after one clean round of three
repetitions, choose the cheaper and faster by effective price and write the
decision down. Repeat only when the tie hinges on a single scenario whose
outcome changes between repetitions. *Why:* a decision recorded with its
caveat is worth more than a variable left "pending confirmation"
indefinitely.

## Step 14 — Noisy scenarios: mark them, don't debug them here

A scenario that fails intermittently for a reason the traceback doesn't
show is marked as a control in the dataset, with the reason, and the run
goes on. *Why:* debugging an unstable feature is separate work; it doesn't
decide which model to use.
