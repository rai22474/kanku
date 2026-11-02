"""The words of the project's documents, per adapter language.

The structure of every document is fixed; its headings, column names and
state words are not. The validator and the report match these sets.
Reference: docs/artifacts/index.md.
"""

WORDS = {
    "en": {
        "scenarios": "Scenarios",
        "results": "Results",
        "history": "History",
        "scenario": "Scenario",
        "control": "Control",
        "yes": ("yes", "y", "x", "✓"),
        "decided": "decided",
        "pending": "pending",
        "default_status": "default",
        "verdicts": ("chosen", "finalist", "discarded", "unknown"),
        "chosen_prefix": "Chosen:",
        "decision": "Decision",
        "catalog_read": "Catalog read",
        "revisions": "Revisions",
        "unattributed": "unattributed",
        "default": "(default)",
        "unclassified": "of the failures unclassified (review by hand)",
        "controls": "controls failed",
        "breakdown_title": "Breakdown by scenario",
        "breakdown_columns": (
            "Scenario", "Calls (all repetitions)", "Mean", "p50", "p90", "p95", "Max",
            "Input tokens", "Output tokens", "Reasoning tokens", "Cached tokens",
        ),
    },
    "es": {
        "scenarios": "Escenarios",
        "results": "Resultados",
        "history": "Histórico",
        "scenario": "Escenario",
        "control": "Control",
        "yes": ("sí", "si", "x", "✓"),
        "decided": "decidida",
        "pending": "pendiente",
        "default_status": "por defecto",
        "verdicts": ("elegido", "finalista", "descartado", "desconocido"),
        "chosen_prefix": "Elegido:",
        "decision": "Decisión",
        "catalog_read": "Catálogo leído",
        "revisions": "Revisiones",
        "unattributed": "sin_atribuir",
        "default": "(por defecto)",
        "unclassified": "de los fallos sin clasificar (revisar a mano)",
        "controls": "controles fallidos",
        "breakdown_title": "Desglose por escenario",
        "breakdown_columns": (
            "Escenario", "Llamadas (todas las repeticiones)", "Media", "p50", "p90", "p95", "Máx",
            "Tokens entrada", "Tokens salida", "Tokens reasoning", "Tokens caché",
        ),
    },
}

RESULT_COLUMNS = 16


def words(language: str) -> dict:
    return WORDS[language]
