import io
import json
import subprocess
import unittest
from contextlib import redirect_stdout
from unittest import mock

from fixture import ADAPTER, DATASET, Project
from kanku_core import cli
from kanku_core.config import load_config
from kanku_core.validate import check

ADAPTER_WITH_DOCS = ADAPTER.replace(
    "docs:\n  benchmarks: docs/benchmarks\n",
    "docs:\n  benchmarks: docs/benchmarks\n  requirements: docs/requirements.md\n"
    "  candidates: docs/candidates.md\n  agents: docs/agents.md\n  decisions: docs/decisions.md\n",
)

REQUIREMENTS = """
# Requisitos

| Variable | Agentes | Perfil | Índice | Imprescindibles | Deseables |
|---|---|---|---|---|---|
| `APP_MODEL` | sensei | agéntico | agentic | tools; `tool_success_rate` ≥ 0.9 | p95 |
| `VISION_MODEL` | fotos | visión | intelligence | imagen | — |
| `REASONING_MODEL` | juez | juicio | intelligence | inteligencia por encima de `APP_MODEL` | — |
| `MEMORY_MODEL` | memoria | comprensión | intelligence | `response_format` | — |
"""

TABLE = """| Modelo | Prompt $/M | Completion $/M | Cache read $/M | Índice | tool_success_rate | Razonamiento obligatorio | Edad (días) | Veredicto | Notas |
|---|---|---|---|---|---|---|---|---|---|"""

CANDIDATES = f"""
# Candidatos

Catálogo leído: 2026-11-01.

## `APP_MODEL` — decidida (`a/base`, 2026-11-01)

{TABLE}
| `a/base` | 0.40 | 1.60 | 0.10 | agentic 58 | 0.97 | no | 120 | elegido | ganó |
| `b/other` | 0.30 | 2.50 | — | agentic 63 | 0.95 | sí | 40 | descartado | p95 3× |

### Decisión

Elegido: `a/base`. Ganó el benchmark.

## `VISION_MODEL` — pendiente

{TABLE}
| `v/one` | 0.20 | 0.80 | — | — | 0.93 | no | 30 | desconocido | sin índice |

### Decisión

Pendiente: falta el benchmark.

## `REASONING_MODEL` — por defecto

{TABLE}

### Decisión

Se queda el valor por defecto del servicio.

## `MEMORY_MODEL` — decidida (`m/mem`, 2026-11-01)

{TABLE}
| `m/mem` | 0.10 | 0.20 | — | intelligence 40 | — | no | 200 | elegido | por catálogo |

### Decisión

Elegido: `m/mem`. Solo catálogo.
"""

AGENTS = """
# Agentes

## app

| Agente | Perfil | Modelo usado | Requisitos | Fuente |
|---|---|---|---|---|
| sensei | agentic | `APP_MODEL` | tools | app/sensei.py:10 |
| fotos | vision | `VISION_MODEL ?? APP_MODEL` | imagen | app/fotos.py:5 |

## memory

| Agente | Perfil | Modelo usado | Requisitos | Fuente |
|---|---|---|---|---|
| memoria | understanding | `MEMORY_MODEL` | json | memory/main.py:3 |
"""

DECISIONS = """
# Decisiones de modelos

## `APP_MODEL`

**Decidida:** `a/base` (2026-11-01).

### Revisiones

- **2026-11-01** — decidida `a/base`. Evidencia: dataset.

## `MEMORY_MODEL`

**Decidida:** `m/mem` (2026-11-01).

### Revisiones

- **2026-11-01** — decidida `m/mem`. Evidencia: solo catálogo.
"""


def git(project, *arguments):
    subprocess.run(["git", "-C", str(project.root), "-c", "user.name=t", "-c", "user.email=t@t", *arguments], check=True, capture_output=True)


def commit_all(project, message="docs"):
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", message)
    return subprocess.run(["git", "-C", str(project.root), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()


class ValidatorTest(unittest.TestCase):
    def setUp(self):
        self.project = Project(adapter=ADAPTER_WITH_DOCS)
        self.project.write("docs/requirements.md", REQUIREMENTS)
        self.project.write("docs/candidates.md", CANDIDATES)
        self.project.write("docs/agents.md", AGENTS)
        self.project.write("docs/decisions.md", DECISIONS)

    def tearDown(self):
        self.project.close()

    def problems(self, base="HEAD"):
        return check(load_config(self.project.root), base)

    def edit(self, relative, old, new):
        path = self.project.root / relative
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def assertProblem(self, fragment):
        problems = self.problems()
        self.assertTrue(any(fragment in problem for problem in problems), f"no problem with '{fragment}' in {problems}")

    def test_consistent_documents_pass(self):
        self.assertEqual(self.problems(), [])

    def test_every_variable_needs_a_requirements_row_and_a_candidates_section(self):
        self.edit("docs/requirements.md", "| `MEMORY_MODEL` | memoria | comprensión | intelligence | `response_format` | — |\n", "")
        self.edit("docs/candidates.md", "## `REASONING_MODEL`", "## `OTHER_MODEL`")
        problems = self.problems()
        self.assertIn("docs/requirements.md: no row for `MEMORY_MODEL`", problems)
        self.assertIn("docs/candidates.md: no section for `REASONING_MODEL`", problems)
        self.assertIn("docs/candidates.md: `OTHER_MODEL` is not a variable of any service in the adapter", problems)

    def test_requirements_index_and_relative_thresholds(self):
        self.edit("docs/requirements.md", "| visión | intelligence |", "| visión | best |")
        self.edit("docs/requirements.md", "por encima de `APP_MODEL`", "por encima de `PLANNER_MODEL`")
        self.assertProblem("`VISION_MODEL` has index 'best'")
        self.assertProblem("name `PLANNER_MODEL`, not a variable")

    def test_decided_with_two_chosen_rows(self):
        self.edit("docs/candidates.md", "| 40 | descartado |", "| 40 | elegido |")
        self.assertProblem("`APP_MODEL`: decided, but the table has 2 'elegido' rows")

    def test_decided_whose_table_and_text_disagree(self):
        self.edit("docs/candidates.md", "Elegido: `a/base`", "Elegido: `b/other`")
        self.assertProblem("name different models: a/base, b/other")

    def test_pending_marker_left_in_a_decided_section(self):
        self.edit("docs/candidates.md", "Ganó el benchmark.", "Ganó el benchmark; precio pendiente de confirmar.")
        self.assertProblem("`APP_MODEL`: decided, but its heading or decision still says 'pendiente'")

    def test_pending_with_a_chosen_row_or_line(self):
        self.edit("docs/candidates.md", "| 30 | desconocido |", "| 30 | elegido |")
        self.edit("docs/candidates.md", "Pendiente: falta el benchmark.", "Elegido: `v/one`.")
        self.assertProblem("`VISION_MODEL`: pending, but the table has a 'elegido' row")
        self.assertProblem("`VISION_MODEL`: pending, but the decision has a 'Elegido:' line")

    def test_verdicts_prices_and_catalog_date(self):
        self.edit("docs/candidates.md", "| 30 | desconocido |", "| 30 | quizá |")
        self.edit("docs/candidates.md", "| `v/one` | 0.20 |", "| `v/one` | barato |")
        self.edit("docs/candidates.md", "Catálogo leído: 2026-11-01.", "")
        self.assertProblem("`v/one` has verdict 'quizá'")
        self.assertProblem("`v/one` has price 'barato'")
        self.assertProblem("no 'Catálogo leído: <date>' line")

    def test_unknown_status(self):
        self.edit("docs/candidates.md", "## `VISION_MODEL` — pendiente", "## `VISION_MODEL` — en curso")
        self.assertProblem("status 'en curso' must be one of decidida, pendiente, por defecto")

    def test_agents_use_only_their_service_variables(self):
        self.edit("docs/agents.md", "`MEMORY_MODEL` | json", "`APP_MODEL` | json")
        self.assertProblem("agent 'memoria' uses `APP_MODEL`, not a variable of memory")

    def test_decided_variable_needs_a_record(self):
        self.edit("docs/decisions.md", "## `MEMORY_MODEL`", "## `OTRA`")
        self.assertProblem("docs/decisions.md: no record for `MEMORY_MODEL`")

    def test_revision_entries_are_append_only(self):
        commit_all(self.project)
        self.edit("docs/decisions.md", "Evidencia: dataset.", "Evidencia: otra.")
        self.assertProblem("revision entry changed or removed")

    def test_a_new_revision_entry_is_fine(self):
        commit_all(self.project)
        self.edit("docs/decisions.md", "### Revisiones\n\n- **2026-11-01** — decidida `a/base`", "### Revisiones\n\n- **2026-12-01** — `a/base` → `b/other`.\n- **2026-11-01** — decidida `a/base`")
        self.assertEqual(self.problems(), [])

    def test_sanchin_records_when_present(self):
        self.project.write(".claude/kanku.yaml", ADAPTER_WITH_DOCS.replace("  decisions: docs/decisions.md\n", ""))
        self.project.write(".claude/sanchin.yaml", "base_docs:\n  decisions: docs/adr/\n")
        self.project.write("docs/adr/ADR-001.md", "# ADR-001\n\nAPP_MODEL is `a/base`.\n")
        self.assertEqual(self.problems(), ["docs/adr: no decision record names `MEMORY_MODEL`, decided in the candidates"])


class DatasetRulesTest(unittest.TestCase):
    ROW = "| 2026-11-01 | `c/new` | VISION_MODEL=v/one | {commit} | 2026-11-01 | 90% | 100% | 0% | 1s | 1s | 1s | 1s | 1s | 1s | $0.1 | — |"

    def setUp(self):
        self.project = Project()
        self.relative = "docs/benchmarks/app_APP_MODEL_2026-09-10.md"

    def tearDown(self):
        self.project.close()

    def problems(self):
        return check(load_config(self.project.root))

    def append(self, row):
        self.project.dataset.write_text(
            self.project.dataset.read_text(encoding="utf-8").replace("| — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |", row),
            encoding="utf-8",
        )

    def test_the_fixture_dataset_passes(self):
        self.assertEqual(self.problems(), [])

    def test_a_wrong_column_count(self):
        self.edit_dataset("| Coste/escenario | Notas |", "| Notas |")
        self.assertTrue(any("has 15 columns, the format has 16" in p for p in self.problems()), self.problems())

    def test_a_row_needs_commit_and_catalog_date(self):
        self.append(self.ROW.format(commit="—").replace("| 2026-11-01 | 90%", "| — | 90%"))
        problems = self.problems()
        self.assertTrue(any("(`c/new`) has no commit" in p for p in problems), problems)
        self.assertTrue(any("(`c/new`) has no catalog-read date" in p for p in problems), problems)

    def test_rows_are_append_only_or_move_to_history(self):
        commit_all(self.project)
        self.edit_dataset("| 2026-09-01 | `x/y` | — | abc |", "| 2026-09-02 | `x/y` | — | abc |")
        self.assertTrue(any("was changed or removed" in p for p in self.problems()))

    def test_moving_a_row_to_history_is_fine(self):
        commit_all(self.project)
        row = "| 2026-09-01 | `x/y` | — | abc | 2026-09-01 | 100% | 0% | 0% | 1s | 1s | 1s | 1s | 1s | 1s | $0.1 | — |"
        self.edit_dataset(row + "\n", "")
        self.edit_dataset("Nada.", "Nada.\n\nAntes del arreglo del parser:\n\n" + row)
        self.assertEqual(self.problems(), [])

    def test_history_is_append_only(self):
        commit_all(self.project)
        self.edit_dataset("Nada.", "Otra cosa.")
        self.assertTrue(any("history line changed or removed: Nada." in p for p in self.problems()))

    def test_scenarios_fixed_once_measured(self):
        commit_all(self.project)
        self.edit_dataset("| búsqueda | `manage_species/create_species_via_advice.py::test_care_guide_generated_as_wiki_page` | | wiki |\n", "")
        self.assertTrue(any("the scenarios changed under measured rows" in p for p in self.problems()))

    def test_rows_of_one_comparison_share_their_code(self):
        first = commit_all(self.project, "code")
        self.append(self.ROW.format(commit=first))
        self.project.write("docs/benchmarks/index.md", "# Datasets\n")
        docs_only = commit_all(self.project, "docs only")
        self.append_to_app_section(self.ROW.format(commit=docs_only).replace("`c/new`", "`d/docs`"))
        self.assertEqual([p for p in self.problems() if "differ in code" in p], [])
        self.project.write("app/main.py", "print(1)\n")
        code_change = commit_all(self.project, "code change")
        self.append_to_app_section(self.ROW.format(commit=code_change).replace("`c/new`", "`e/code`"))
        self.assertTrue(any("differ in code (app/main.py)" in p for p in self.problems()), self.problems())

    def edit_dataset(self, old, new):
        text = self.project.dataset.read_text(encoding="utf-8")
        self.assertIn(old, text)
        self.project.dataset.write_text(text.replace(old, new, 1), encoding="utf-8")

    def append_to_app_section(self, row):
        text = self.project.dataset.read_text(encoding="utf-8")
        marker = "\n\n## Resultados — `REASONING_MODEL`"
        self.project.dataset.write_text(text.replace(marker, "\n" + row + marker, 1), encoding="utf-8")


class HookTest(unittest.TestCase):
    def setUp(self):
        self.project = Project(adapter=ADAPTER_WITH_DOCS)
        self.project.write("docs/requirements.md", REQUIREMENTS)
        self.project.write("docs/candidates.md", CANDIDATES)

    def tearDown(self):
        self.project.close()

    def run_hook(self, relative):
        payload = json.dumps({"tool_input": {"file_path": str(self.project.root / relative)}})
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(payload)), redirect_stdout(out):
            code = cli.main(["--project", str(self.project.root), "hook"])
        self.assertEqual(code, 0)
        return json.loads(out.getvalue()) if out.getvalue().strip() else None

    def test_a_broken_candidates_edit_blocks_with_its_problems_only(self):
        text = (self.project.root / "docs/candidates.md").read_text(encoding="utf-8")
        (self.project.root / "docs/candidates.md").write_text(text.replace("Elegido: `a/base`", "Elegido: `b/other`"), encoding="utf-8")
        (self.project.root / "docs/requirements.md").write_text(REQUIREMENTS.replace("| `MEMORY_MODEL`", "| `X_MODEL`"), encoding="utf-8")
        output = self.run_hook("docs/candidates.md")
        self.assertEqual(output["decision"], "block")
        self.assertIn("name different models", output["reason"])
        self.assertNotIn("requirements.md", output["reason"])

    def test_a_clean_edit_and_an_unrelated_file_are_silent(self):
        self.assertIsNone(self.run_hook("docs/candidates.md"))
        self.project.write("README.md", "# x\n")
        self.assertIsNone(self.run_hook("README.md"))

    def test_a_project_without_kanku_is_silent(self):
        (self.project.root / ".claude/kanku.yaml").unlink()
        self.assertIsNone(self.run_hook("docs/candidates.md"))


if __name__ == "__main__":
    unittest.main()
