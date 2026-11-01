# Decision records

[README](../../README.md) · [Docs](../index.md) · [Artifacts](index.md)

Where the choice of each variable is recorded with its why, and revised.

**With sanchin.** When the project has `.claude/sanchin.yaml`, the records
are sanchin's decision records: kanku reads their directory and format from
that adapter, and writes each model change as a revision of the record that
decided the variable — or a new record, when none did. **Without sanchin**,
kanku keeps one file at `docs.decisions`. kanku's own `docs.decisions`, when
set, wins over sanchin's. *Why:* one project, one place for decisions; kanku
shouldn't open a second register next to the one the project already keeps.

```markdown
# Model decisions

## `PLANNER_MODEL`

**Decided:** `vendor/model-a` (2026-11-01).

Why: …

### Revisions

- **2026-12-03** — `vendor/model-a` → `vendor/model-d`. Same pass rate, 40 %
  cheaper by effective price. Evidence: [dataset](benchmarks/app_PLANNER_MODEL_2026-11-01.md#results--planner_model).
- **2026-11-01** — decided `vendor/model-a`. Evidence: …
```

- A decision in force is never rewritten; it is revised by an entry,
  newest first. *Why:* the next review needs to know what was tried and why
  it lost.
- An entry names the evidence: a dataset section, an analogy with another
  variable, or "catalog only".

The validator checks that existing entries are unchanged and that every
decided variable in the candidates has a record.
