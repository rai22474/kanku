"""Read a dataset file and append result rows to it.

The dataset's scenario table is the single source of what a benchmark runs
and which scenarios are controls. Reference: docs/artifacts/dataset.md.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from .language import RESULT_COLUMNS, words
from .logs import test_name


class DatasetError(Exception):
    pass


@dataclass(frozen=True)
class Scenario:
    nodeid: str
    name: str
    control: bool


def sections(text: str) -> list[tuple[str, int, int]]:
    """(heading, start, end) of every `## ` section."""
    starts = [match.start() for match in re.finditer(r"^## ", text, flags=re.MULTILINE)]
    result = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(text)
        heading = text[start:].split("\n", 1)[0][3:].strip()
        result.append((heading, start, end))
    return result


def table_rows(block: str) -> list[list[str]]:
    rows = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def scenarios(path: Path, language: str) -> list[Scenario]:
    w = words(language)
    text = path.read_text(encoding="utf-8")
    section = next((s for s in sections(text) if s[0].startswith(w["scenarios"])), None)
    if section is None:
        raise DatasetError(f"{path}: no '## {w['scenarios']}' section")
    rows = table_rows(text[section[1]:section[2]])
    if len(rows) < 2:
        raise DatasetError(f"{path}: the scenario table is empty")
    header = rows[0]
    scenario_column = next((i for i, cell in enumerate(header) if cell.startswith(w["scenario"])), None)
    if scenario_column is None:
        raise DatasetError(f"{path}: the scenario table has no '{w['scenario']}' column")
    control_column = next((i for i, cell in enumerate(header) if cell == w["control"]), None)
    result = []
    for row in rows[1:]:
        nodeid = row[scenario_column].strip("`") if scenario_column < len(row) else ""
        if "::" not in nodeid:
            raise DatasetError(f"{path}: '{nodeid}' is not a test node id (path::test)")
        control = control_column is not None and control_column < len(row) and row[control_column].lower() in w["yes"]
        result.append(Scenario(nodeid=nodeid, name=test_name(nodeid), control=control))
    return result


def selection(scenario_list: list[Scenario]) -> str:
    """The -k expression that runs exactly these scenarios."""
    return " or ".join(scenario.name for scenario in scenario_list)


def results_section(text: str, variable: str, language: str) -> tuple[int, int]:
    w = words(language)
    candidates = [s for s in sections(text) if s[0].startswith(w["results"])]
    named = [s for s in candidates if re.search(rf"(?<![A-Z0-9_]){re.escape(variable)}(?![A-Z0-9_])", s[0])]
    if named:
        return named[0][1], named[0][2]
    bare = [s for s in candidates if s[0] == w["results"]]
    if len(bare) == 1:
        return bare[0][1], bare[0][2]
    raise DatasetError(f"no '## {w['results']} — {variable}' section in the dataset")


def check_results_table(path: Path, variable: str, language: str) -> None:
    text = path.read_text(encoding="utf-8")
    start, end = results_section(text, variable, language)
    rows = table_rows(text[start:end])
    if not rows:
        raise DatasetError(f"{path}: the results section for {variable} has no table")
    if len(rows[0]) != RESULT_COLUMNS:
        raise DatasetError(
            f"{path}: the results table for {variable} has {len(rows[0])} columns, kanku's format has "
            f"{RESULT_COLUMNS} (docs/artifacts/dataset.md) — bring it to the format first"
        )


def append_row(path: Path, variable: str, language: str, cells: list[str]) -> None:
    """Append as the last row of the variable's results table; a placeholder row of dashes is replaced."""
    if len(cells) != RESULT_COLUMNS:
        raise DatasetError(f"a result row has {RESULT_COLUMNS} cells, got {len(cells)}")
    text = path.read_text(encoding="utf-8")
    start, end = results_section(text, variable, language)
    section = text[start:end]
    row = "| " + " | ".join(cell.replace("|", "\\|").replace("\n", " ") for cell in cells) + " |"
    lines = section.split("\n")
    table = [i for i, line in enumerate(lines) if line.strip().startswith("|")]
    if not table:
        raise DatasetError(f"{path}: the results section for {variable} has no table")
    last = table[-1]
    if all(cell.strip() == "—" for cell in lines[last].strip().strip("|").split("|")):
        lines[last] = row
    else:
        lines.insert(last + 1, row)
    path.write_text(text[:start] + "\n".join(lines) + text[end:], encoding="utf-8")
