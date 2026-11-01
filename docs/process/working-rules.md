# Working rules

[README](../../README.md) · [Docs](../index.md) · [Process](index.md)

## Unattended by default

A run goes from step 1 to the report without pausing between steps.
Launching benchmarks (they cost real money — that is their purpose),
writing the decided value into the environment file, fixing a bounded
wiring bug found on the way, writing the documents: all proceed without
asking. *Why:* the process is meant to be launched once a month; a run that
asks a question per step doesn't get launched.

## When to really stop

Only for these:

- **Pushing, or anything that deploys.** Never without the user asking, even
  with the local commit made.
- **A live security incident** — exposed credentials, real side effects
  triggered from a test environment. Stop, report exactly what happened
  **without printing the secret**, and wait for confirmation while it is
  still active.
- **No candidate meets a variable's hard requirements.** There is no
  reasonable default: document the gap and ask. Never relax a filter on
  your own. *Why:* a relaxed filter turns a requirement into a preference
  without anyone deciding it.
- **Deleting or overwriting** a dataset, a decision record or a results
  section instead of appending to it. Confirm first.

## Secrets

- Never print, read whole or dump the environment file or the full output
  of `docker compose config`. Edit the exact fragment; to check a value,
  parse it in code and report only whether it is empty, or its length.
  *Why:* anything printed stays in the session history and its logs.

## Results

- Never fabricate or assume the result of a benchmark still running; wait
  for its real notification before interpreting or documenting anything
  about that comparison.
- Independent comparisons run in parallel when they don't compete for a
  port or a compose project.

## Lessons

A rule learned in a project becomes a rule here only with a general *why*
([decisions/0012](../decisions/0012-general-whys.md)). The incident that
taught it stays in that project's [protocol log](../artifacts/protocol.md).
