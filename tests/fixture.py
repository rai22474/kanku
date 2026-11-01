"""A tiny project on disk, built per test, with a kanku adapter and a dataset."""

import os
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

ADAPTER = """
version: 1
language: es
env_file: .env
services:
  app:
    variables: [APP_MODEL, VISION_MODEL, REASONING_MODEL]
    acceptance:
      compose: [tests/acceptance/docker-compose.acceptance.yml]
      container: app
      health: http://localhost:8060/health
      test: uv run pytest tests/acceptance
    side_effect_keys: [BOT_TOKEN, ADMIN_CHAT_ID]
    classify:
      model: [LlmCallsLimitExceededError]
      environment:
        - 'no (he )?pud[eo].*(meteorológic|pronóstico)'
        - 'weather (service|api|data).*(error|fail|unavailable)'
        - '(error|fail).*weather (service|api|data)'
        - 'host\\.docker\\.internal'
  memory:
    variables: [MEMORY_MODEL]
docs:
  benchmarks: docs/benchmarks
"""

HEADER = (
    "| Fecha de ejecución | Candidato | Otras variables | Commit | Catálogo leído | Pasados | Fallos: modelo "
    "| Fallos: entorno | Latencia media | p50 | p90 | p95 | mín | máx | Coste/escenario | Notas |"
)

DATASET = f"""
# Dataset — app / `APP_MODEL` — curado el 2026-09-10

## Escenarios del dataset

| Categoría | Escenario | Control | Motivo |
|---|---|---|---|
| tool-calling | `manage_bonsai/create_bonsai_via_advice.py::test_create_bonsai` | | canario |
| salida estructurada | `fertilization_plan/fertilization_plan_via_advice.py::test_propose_and_confirm_fertilization_plan` | | plan |
| salida estructurada | `fertilizer_recommendation/fertilizer_recommendation_via_advice.py::test_fertilizer_recommendation_saves_to_wiki` | | runner |
| visión | `diagnose_bonsai_health/diagnose_bonsai_health_via_advice.py::test_health_analysis_for_latest_photo` | | visión |
| visión | `work_execution/work_execution_via_advice.py::test_photos_isolated_and_analyzed` | | visión |
| multi-turno | `work_refinement/work_refinement_via_advice.py::test_pre_work_analysis` | sí | ruidoso |
| desambiguación | `manage_species/create_species_via_advice.py::test_user_asked_to_choose_variety_when_ambiguous` | | intención |
| juicio | `protect_bonsai/advise_protection_for_nighttime_frost_risk.py::test_protect_bonsai` | | juez |
| búsqueda | `manage_species/create_species_via_advice.py::test_care_guide_generated_as_wiki_page` | | wiki |

## Condiciones fijas

Ninguna.

## Resultados — `APP_MODEL`

{HEADER}
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

## Resultados — `REASONING_MODEL`

{HEADER}
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-01 | `x/y` | — | abc | 2026-09-01 | 100% | 0% | 0% | 1s | 1s | 1s | 1s | 1s | 1s | $0.1 | — |

## Histórico (no comparable)

Nada.
"""


class Project:
    def __init__(self, adapter: str = ADAPTER, env: str = "APP_MODEL=a/base\nVISION_MODEL=v/one\nREASONING_MODEL=r/two\nOPENROUTER_API_KEY=sk-secret-value\n"):
        self._directory = tempfile.TemporaryDirectory()
        self.root = Path(self._directory.name)
        self.write(".claude/kanku.yaml", adapter)
        self.write(".env", env)
        self.dataset = self.write("docs/benchmarks/app_APP_MODEL_2026-09-10.md", DATASET)
        self.trust_file = self.root.parent / f"{self.root.name}-trust.json"
        os.environ["KANKU_TRUST_FILE"] = str(self.trust_file)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
        return path

    def copy_run(self, name: str = "run_glm") -> Path:
        target = self.root / "benchmark_results" / name
        shutil.copytree(FIXTURES / name, target)
        return target

    def close(self):
        self._directory.cleanup()
        self.trust_file.unlink(missing_ok=True)
