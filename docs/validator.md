# The validator

[README](../README.md) · [Docs](index.md)

`scripts/kanku check` reads the project's model documents and reports what
contradicts their [formats](artifacts/index.md): one line per problem,
`<path>: <message>`, exit code 1. It runs no command from the adapter, so it
needs no [trust](decisions/0009-trust-by-hash.md).

```text
scripts/kanku check [--base REF] [--file PATH]
```

- `--base` — the git ref the append-only rules compare with. `HEAD` by
  default: what an edit changed since the last commit. In CI, the branch
  being merged into (`--base origin/main`), so a change committed on the way
  is still caught.
- `--file` — report only that file's problems.

## The rules

| Document | Rule |
|---|---|
| requirements | One row per adapter variable, no row for a variable the adapter lacks; *Index* is `agentic`, `intelligence` or `coding`; a variable named in *Hard* exists. |
| candidates | One section per adapter variable; the catalog-read date is there; the heading is `` `VAR` — <status> (`model`, date) ``. *decided*: exactly one chosen row, the model of the heading, the row and the `Chosen:` line is the same, and no *pending* word in its heading or decision. *pending* and *default*: no chosen row, no `Chosen:` line. Verdicts are the language's four; prices are numbers or `—`. |
| agents | Each section is a service of the adapter; each variable in *Model used* is one of that service's. |
| datasets | The scenario table parses (node ids, a *Scenario* column); results tables have 16 columns; a measured row has a commit and a catalog-read date; the rows of one results section were measured on the same code — their commits may differ only in kanku's own documents and results. |
| datasets, against the base | A result row present in the base is still in its section or has moved to history; every history line is still there; the scenarios don't change under rows measured on them. |
| decisions | Every *decided* variable has a record; revision entries present in the base are unchanged. With sanchin's records, the record is any decision record that names the variable. |

The words — statuses, verdicts, headings — are the adapter's language set
([artifacts/](artifacts/index.md#word-sets)). Columns are read by position:
the structure is fixed, only their names are translated.

Rules against the base are skipped without git, for a file the base doesn't
have, and for a results table still being brought to the format. The
commit rule skips a commit git doesn't know (a shallow clone).

## The hook

The plugin's `PostToolUse` hook runs after every `Write` or `Edit` in a
project with `.claude/kanku.yaml`. When the edited file is one of the
documents above, it runs the check against `HEAD` and blocks with that
file's problems only, so the edit is fixed before the run moves on. Any
other file is ignored. An adapter that doesn't load is reported without
blocking: the checks are off until it is fixed, and that must not be
silent.

## In CI

The project's own pipeline can run it on every change to its documents:

```yaml
- run: ${KANKU}/scripts/kanku check --base origin/main
```

with `KANKU` a checkout of the kanku version the project pins.
