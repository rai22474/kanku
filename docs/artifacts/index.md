# Artifacts

[README](../../README.md) · [Docs](../index.md)

The documents a run reads and writes. Their paths come from the adapter's
`docs` ([adapter.md](../adapter.md)); their structure is fixed here, so the
validator can check what the process can't afford to leave to memory.

**Language.** The structure is fixed; the words are not. Headings, column
names and state words are written in the adapter's `language`, from the set
kanku ships for it (`en`, `es`). Each format below gives the English set and
the keys the validator reads. *Why:* a project's documents read in its own
language, and a validator that matched only English headings would force a
second set of documents.

| Document | What it holds | Written in |
|---|---|---|
| [agents.md](agents.md) | Every agent with an LLM, its real requirements, the model it really uses. | step 1 |
| [requirements.md](requirements.md) | One row per model variable: who uses it, its profile and index, hard and desirable requirements. | steps 2–3 |
| [candidates.md](candidates.md) | One section per variable: its status, the candidates table, the decision. | steps 4–6, 15 |
| [dataset.md](dataset.md) | A curated scenario list for one variable, dated, with its result rows. | steps 9, 11–14 |
| [decisions.md](decisions.md) | The decision records and their revisions. | step 15 |
| [protocol.md](protocol.md) | The project's protocol log: environment conditions and every fix found by a run. | steps 10, 12 |
| [run-report.md](run-report.md) | What one run did, self-contained. | end of the run |

## Word sets

| Key | `en` | `es` |
|---|---|---|
| Statuses | decided, pending, default | decidida, pendiente, por defecto |
| Verdicts | chosen, finalist, discarded, unknown | elegido, finalista, descartado, desconocido |
| Decision line | `Chosen: <model>` | `Elegido: <model>` |
| Headings | Decision, Scenarios, Results, History, Revisions | Decisión, Escenarios, Resultados, Histórico, Revisiones |
| Catalog date line | `Catalog read: <date>` | `Catálogo leído: <date>` |
| Control column, yes | Control; yes, y, x, ✓ | Control; sí, si, x, ✓ |

Headings are matched by their start (`## Results — \`APP_MODEL\``), so
they can carry the variable. Index names (`agentic`, `intelligence`,
`coding`) are the catalog's, in every language.

## What the validator checks

In full: [validator.md](../validator.md).


| Rule | Where | Gate |
|---|---|---|
| Every model variable of the adapter has a requirements row and a candidates section. | requirements, candidates | validator |
| A section's status matches its table and its decision: *decided* has exactly one chosen row, the same model the decision text names and the heading carries; *pending* has none. | candidates | validator (step 16) |
| No *pending* marker in a section whose status is *decided*. | candidates | validator (step 16) |
| A result row's scenarios are the dataset's scenarios; the rows of one comparison share one commit. | dataset | validator |
| Result sections, history sections and decision records are only appended to. | dataset, decisions | validator |
| Every other model variable of the service is set explicitly before a run. | environment | runner (step 8) |
| No other run on the same compose project or port; side-effect keys resolve empty. | environment | runner (step 10) |
