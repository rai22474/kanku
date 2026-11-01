# 4 · Decision

[README](../../README.md) · [Docs](../index.md) · [Process](index.md)

Steps 15–17. Takes the results, or a catalog-only decision; leaves the
[decision record](../artifacts/decisions.md) revised, every document citing
the variable updated, and the [run report](../artifacts/run-report.md).

## Step 15 — Document the decision everywhere it is cited

- **Candidates:** the table and the decision text, together. *Why:* a table
  edited apart from its text ends up marking the loser as chosen.
- **Requirements**, when a criterion changed.
- **Dataset:** the result rows. Rows from before a code change go to the
  history section, never mixed with comparable results.
- **Decision record:** a new revision entry. A decision already in force is
  never rewritten; it is revised. *Why:* the history of why a model was chosen
  is what the next review needs, and an edited record erases it.
- **Every page that cites the variable** — agent pages, stack pages,
  service READMEs, the adapter's `docs.citing` list.
- **The environment** — the project's `.env` (or what the adapter names)
  gets the decided value. Write it with an exact-fragment edit; never read
  or print the whole file.

## Step 16 — Consistency sweep

Before a variable is closed, search every document touched — and every
document that mentions the variable without being touched — for state
markers that contradict each other: "chosen" in a table next to
"discarded" in its text, "pending" in the heading of a resolved section,
two variables said to share a model after the code split them. The
validator checks the formats it knows; the sweep covers the prose it
doesn't. *Why:* a decision lives in several places, and every place not
updated keeps stating the old one with the same authority.

## Step 17 — Full acceptance, not only the dataset

Once the variables in scope are closed, run the **full** acceptance suite
of each affected service with statistics on (percentiles and real cost of
the whole run). *Why:* the dataset is deliberately small and can miss whole
categories of scenario where a regression shows up.

New failures outside the dataset are judged: a one-run fluke, an
environment or code bug, or a reason to reopen the variable. None is
ignored because the dataset passed.

## The run report

The run ends with a self-contained report, written to the adapter's
`docs.runs` and summarized in the chat: what was reviewed, what changed and
why, what was left pending and why, what to watch in production. *Why:*
whoever reads it didn't watch the run.
