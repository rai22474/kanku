"""The validator: the rules of docs/artifacts/ that the process can't leave to memory.

Every problem is a line `<path>: <message>`, the path relative to the
project. Rules about what changed (append-only results, history and
revision entries; scenarios fixed once measured) compare the working tree
with a git base, `HEAD` unless told otherwise; without git, or for a file
the base doesn't have, they are skipped. Nothing here runs a command from
the adapter, so the validator needs no trust.
Reference: docs/artifacts/index.md#what-the-validator-checks.
"""

import re
import subprocess
from pathlib import Path

import yaml

from .config import Config
from .dataset import DatasetError, scenarios_in, sections, table_rows
from .language import RESULT_COLUMNS, words

INDEXES = ("agentic", "intelligence", "coding")
VARIABLE = re.compile(r"(?<![A-Za-z0-9_])[A-Z][A-Z0-9]*_[A-Z0-9_]+(?![A-Za-z0-9_])")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
REQUIREMENTS_COLUMNS = 6
CANDIDATES_COLUMNS = 10
AGENTS_COLUMNS = 5
VERDICT_COLUMN = 8
COMMIT_COLUMN = 3
CATALOG_COLUMN = 4


def check(config: Config, base: str = "HEAD") -> list[str]:
    variables = {variable: service.name for service in config.services.values() for variable in service.variables}
    problems = []
    problems += _requirements(config, variables)
    decided, candidate_problems = _candidates(config, variables)
    problems += candidate_problems
    problems += _agents(config)
    for dataset in dataset_files(config):
        problems += _dataset(config, dataset, base)
    problems += _decisions(config, decided, base)
    return problems


def kanku_documents(config: Config) -> list[Path]:
    """Every file the validator reads: the hook checks an edit only when it is one of them."""
    files = [_doc(config, key) for key in ("requirements", "candidates", "agents")]
    files += dataset_files(config)
    files.append(_own_decisions(config))
    return [file for file in files if file is not None]


def dataset_files(config: Config) -> list[Path]:
    directory = _doc(config, "benchmarks")
    if directory is None or not directory.is_dir():
        return []
    return sorted(path for path in directory.glob("*.md") if path.name != "index.md")


# --- requirements ---------------------------------------------------------


def _requirements(config: Config, variables: dict[str, str]) -> list[str]:
    path = _doc(config, "requirements")
    if path is None or not path.is_file():
        return []
    where = _relative(config, path)
    rows = table_rows(path.read_text(encoding="utf-8"))
    if not rows:
        return [f"{where}: no requirements table"]
    problems = []
    if len(rows[0]) != REQUIREMENTS_COLUMNS:
        return [f"{where}: the requirements table has {len(rows[0])} columns, the format has {REQUIREMENTS_COLUMNS}"]
    seen = set()
    for row in rows[1:]:
        variable = _code(row[0])
        seen.add(variable)
        if variable not in variables:
            problems.append(f"{where}: `{variable}` is not a variable of any service in the adapter")
        index = _code(row[3]).lower().split(" ")[0] if row[3] else ""
        if index not in INDEXES:
            problems.append(f"{where}: `{variable}` has index '{row[3]}', must be one of {', '.join(INDEXES)}")
        for named in VARIABLE.findall(row[4]):
            if named not in variables:
                problems.append(f"{where}: `{variable}`'s hard requirements name `{named}`, not a variable in the adapter")
    for variable in variables:
        if variable not in seen:
            problems.append(f"{where}: no row for `{variable}`")
    return problems


# --- candidates -----------------------------------------------------------


HEADING = re.compile(r"^`(?P<variable>[^`]+)`\s*—\s*(?P<status>[^(]+?)\s*(?:\((?P<inner>.*)\))?\s*$")


def _candidates(config: Config, variables: dict[str, str]) -> tuple[set[str], list[str]]:
    """The decided variables, and the problems."""
    path = _doc(config, "candidates")
    if path is None or not path.is_file():
        return set(), []
    w = words(config.language)
    where = _relative(config, path)
    text = path.read_text(encoding="utf-8")
    problems = []
    if not re.search(rf"^{re.escape(w['catalog_read'])}:\s*\d{{4}}-\d{{2}}-\d{{2}}", text, flags=re.MULTILINE):
        problems.append(f"{where}: no '{w['catalog_read']}: <date>' line")
    statuses = {w["decided"]: "decided", w["pending"]: "pending", w["default_status"]: "default"}
    seen, decided = set(), set()
    for heading, start, end in sections(text):
        match = HEADING.match(heading)
        if not match:
            problems.append(f"{where}: heading '## {heading}' is not `` `<VARIABLE>` — <status> (`<model>`, <date>) ``")
            continue
        variable = match.group("variable")
        seen.add(variable)
        label = f"{where}: `{variable}`"
        if variable not in variables:
            problems.append(f"{label} is not a variable of any service in the adapter")
        status = statuses.get(match.group("status").strip())
        if status is None:
            problems.append(f"{label}: status '{match.group('status').strip()}' must be one of {', '.join(statuses)}")
            continue
        body = text[start:end]
        heading_model = _first_code(match.group("inner") or "")
        decision = _subsection(body, w["decision"])
        chosen_line = re.search(rf"^{re.escape(w['chosen_prefix'])}\s*`([^`]+)`", decision or "", flags=re.MULTILINE)
        chosen_rows, row_problems = _candidate_rows(body, w)
        problems += [f"{label}: {problem}" for problem in row_problems]
        if decision is None:
            problems.append(f"{label}: no '### {w['decision']}' subsection")
        if status == "decided":
            decided.add(variable)
            if heading_model is None:
                problems.append(f"{label}: decided, but the heading names no model")
            if len(chosen_rows) != 1:
                problems.append(f"{label}: decided, but the table has {len(chosen_rows)} '{w['verdicts'][0]}' rows (must be exactly one)")
            if chosen_line is None:
                problems.append(f"{label}: decided, but the decision doesn't start with '{w['chosen_prefix']} `<model>`'")
            named = {model for model in (heading_model, chosen_line and chosen_line.group(1), *chosen_rows) if model}
            if len(named) > 1:
                problems.append(f"{label}: the heading, the table and the decision name different models: {', '.join(sorted(named))}")
            pending = re.compile(rf"(?<!\w){re.escape(w['pending'])}(?!\w)", flags=re.IGNORECASE)
            if pending.search(heading) or pending.search(decision or ""):
                problems.append(f"{label}: decided, but its heading or decision still says '{w['pending']}'")
        else:
            if heading_model is not None and status == "pending":
                problems.append(f"{label}: pending, but the heading names a model")
            if chosen_rows:
                problems.append(f"{label}: {status}, but the table has a '{w['verdicts'][0]}' row")
            if chosen_line is not None:
                problems.append(f"{label}: {status}, but the decision has a '{w['chosen_prefix']}' line")
    for variable in variables:
        if variable not in seen:
            problems.append(f"{where}: no section for `{variable}`")
    return decided, problems


def _candidate_rows(body: str, w: dict) -> tuple[list[str], list[str]]:
    table = body.split("\n### ", 1)[0]
    rows = table_rows(table)
    if not rows:
        return [], ["no candidates table"]
    if len(rows[0]) != CANDIDATES_COLUMNS:
        return [], [f"the candidates table has {len(rows[0])} columns, the format has {CANDIDATES_COLUMNS}"]
    chosen, problems = [], []
    for row in rows[1:]:
        model = _code(row[0])
        for cell in row[1:4]:
            if not re.fullmatch(r"—|\$?\d+(\.\d+)?", cell):
                problems.append(f"`{model}` has price '{cell}'; a price is a number or —")
        verdict = row[VERDICT_COLUMN].lower()
        if verdict not in w["verdicts"]:
            problems.append(f"`{model}` has verdict '{row[VERDICT_COLUMN]}', must be one of {', '.join(w['verdicts'])}")
        elif verdict == w["verdicts"][0]:
            chosen.append(model)
    return chosen, problems


# --- agents ---------------------------------------------------------------


def _agents(config: Config) -> list[str]:
    path = _doc(config, "agents")
    if path is None or not path.is_file():
        return []
    where = _relative(config, path)
    text = path.read_text(encoding="utf-8")
    problems = []
    for heading, start, end in sections(text):
        service = config.services.get(_code(heading))
        if service is None:
            problems.append(f"{where}: section '{heading}' is not a service in the adapter")
            continue
        rows = table_rows(text[start:end])
        if not rows:
            continue
        if len(rows[0]) != AGENTS_COLUMNS:
            problems.append(f"{where}: {service.name}'s table has {len(rows[0])} columns, the format has {AGENTS_COLUMNS}")
            continue
        for row in rows[1:]:
            for named in VARIABLE.findall(row[2]):
                if named not in service.variables:
                    problems.append(f"{where}: agent '{row[0]}' uses `{named}`, not a variable of {service.name} in the adapter")
    return problems


# --- datasets -------------------------------------------------------------


def _dataset(config: Config, path: Path, base: str) -> list[str]:
    w = words(config.language)
    where = _relative(config, path)
    text = path.read_text(encoding="utf-8")
    problems = []
    try:
        current_scenarios = scenarios_in(text, config.language, where)
    except DatasetError as error:
        problems.append(str(error))
        current_scenarios = None
    results = _results(text, w)
    for heading, rows in results.items():
        if rows and len(rows[0]) != RESULT_COLUMNS:
            problems.append(f"{where}: '{heading}' has {len(rows[0])} columns, the format has {RESULT_COLUMNS}")
            continue
        measured = [row for row in rows[1:] if not _placeholder(row)]
        for row in measured:
            if not row[COMMIT_COLUMN] or row[COMMIT_COLUMN] == "—":
                problems.append(f"{where}: a row of '{heading}' ({row[1]}) has no commit")
            if not DATE.search(row[CATALOG_COLUMN]):
                problems.append(f"{where}: a row of '{heading}' ({row[1]}) has no catalog-read date")
        problems += [f"{where}: '{heading}': {problem}" for problem in _one_commit(config, measured)]
    before = _at_base(config, path, base)
    if before is None:
        return problems
    history_now = "\n".join(text[s:e] for h, s, e in sections(text) if h.startswith(w["history"]))
    for heading, rows in _results(before, w).items():
        if rows and len(rows[0]) != RESULT_COLUMNS:
            continue  # a table being brought to the format
        current = {_line(row) for row in results.get(heading, [])[1:]}
        for row in rows[1:]:
            if _placeholder(row):
                continue
            if _line(row) not in current and _line(row) not in _history_lines(history_now):
                problems.append(f"{where}: a row of '{heading}' ({row[0]}, {row[1]}) was changed or removed; result rows are only appended, or moved to history")
    for heading, start, end in sections(before):
        if not heading.startswith(w["history"]):
            continue
        for line in before[start:end].splitlines()[1:]:
            if line.strip() and _normal(line) not in _history_lines(history_now):
                problems.append(f"{where}: history line changed or removed: {line.strip()[:80]}")
    if current_scenarios is not None and _has_measured_rows(before, w):
        try:
            earlier = _scenarios_of(before, config.language)
        except DatasetError:
            earlier = None
        carried = any(
            not _placeholder(row) and _line(row) in {_line(r) for r in _results(before, w).get(heading, [])[1:]}
            for heading, rows in results.items() for row in rows[1:]
        )
        if earlier is not None and earlier != {(s.nodeid, s.control) for s in current_scenarios} and carried:
            problems.append(f"{where}: the scenarios changed under measured rows; move those rows to history, or curate a new dataset")
    return problems


def _results(text: str, w: dict) -> dict[str, list[list[str]]]:
    return {heading: table_rows(text[start:end]) for heading, start, end in sections(text) if heading.startswith(w["results"])}


def _has_measured_rows(text: str, w: dict) -> bool:
    return any(not _placeholder(row) for rows in _results(text, w).values() for row in rows[1:])


def _scenarios_of(text: str, language: str) -> set[tuple[str, bool]]:
    return {(s.nodeid, s.control) for s in scenarios_in(text, language)}


def _one_commit(config: Config, rows: list[list[str]]) -> list[str]:
    """The rows of one comparison measured the same code: their commits differ in kanku's documents at most."""
    commits = sorted({row[COMMIT_COLUMN].split("+")[0] for row in rows if row[COMMIT_COLUMN] not in ("", "—")})
    if len(commits) < 2:
        return []
    ignored = [_relative(config, path) for path in _doc_roots(config)]
    first = commits[0]
    problems = []
    for other in commits[1:]:
        changed = _git(config, "diff", "--name-only", first, other)
        if changed is None:
            continue  # a commit git doesn't have (shallow clone): can't tell
        code = [file for file in changed if not any(file == root or file.startswith(root.rstrip("/") + "/") for root in ignored)]
        if code:
            problems.append(
                f"rows measured on {first} and {other}, which differ in code ({', '.join(code[:3])}{'…' if len(code) > 3 else ''}); "
                "rows from before a code change go to history"
            )
    return problems


def _history_lines(text: str) -> set[str]:
    return {_normal(line) for line in text.splitlines() if line.strip()}


def _normal(line: str) -> str:
    """A table line rebuilt from its cells, so spacing alone is not a change."""
    line = line.strip()
    if line.startswith("|"):
        return _line([cell.strip() for cell in line.strip("|").split("|")])
    return line


def _line(row: list[str]) -> str:
    return "| " + " | ".join(row) + " |"


def _placeholder(row: list[str]) -> bool:
    return all(cell == "—" for cell in row)


# --- decision records -----------------------------------------------------


def _decisions(config: Config, decided: set[str], base: str) -> list[str]:
    own = _own_decisions(config)
    if own is None:
        directory = _sanchin_decisions(config)
        if directory is None or not directory.is_dir():
            return []
        texts = "\n".join(path.read_text(encoding="utf-8") for path in directory.rglob("*.md"))
        return [
            f"{_relative(config, directory)}: no decision record names `{variable}`, decided in the candidates"
            for variable in sorted(decided)
            if not re.search(rf"(?<![A-Z0-9_]){variable}(?![A-Z0-9_])", texts)
        ]
    if not own.is_file():
        return [f"{_relative(config, own)}: missing, and {len(decided)} variable(s) are decided"] if decided else []
    w = words(config.language)
    where = _relative(config, own)
    text = own.read_text(encoding="utf-8")
    recorded = {_code(heading) for heading, _, _ in sections(text)}
    problems = [f"{where}: no record for `{variable}`, decided in the candidates" for variable in sorted(decided - recorded)]
    before = _at_base(config, own, base)
    if before is not None:
        lines = {line.strip() for line in text.splitlines()}
        for entry in _revision_entries(before, w):
            if entry not in lines:
                problems.append(f"{where}: revision entry changed or removed: {entry[:80]}")
    return problems


def _revision_entries(text: str, w: dict) -> list[str]:
    entries, inside = [], False
    for line in text.splitlines():
        if line.startswith("#"):
            inside = line.lstrip("#").strip() == w["revisions"]
            continue
        if inside and line.strip().startswith("- "):
            entries.append(line.strip())
    return entries


def _own_decisions(config: Config) -> Path | None:
    if config.docs.get("decisions"):
        return _doc(config, "decisions")
    if _sanchin_decisions(config) is not None:
        return None
    return config.project_root / "docs" / "models" / "decisions.md"


def _sanchin_decisions(config: Config) -> Path | None:
    adapter = config.project_root / ".claude" / "sanchin.yaml"
    if not adapter.is_file():
        return None
    try:
        raw = yaml.safe_load(adapter.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return None
    directory = (raw.get("base_docs") or {}).get("decisions") if isinstance(raw, dict) else None
    return config.project_root / directory if directory else None


# --- helpers --------------------------------------------------------------


def _doc(config: Config, key: str) -> Path | None:
    value = config.docs.get(key)
    return config.project_root / value if isinstance(value, str) and value else None


def _doc_roots(config: Config) -> list[Path]:
    roots = {config.results_dir}
    for key in ("agents", "requirements", "candidates", "protocol", "decisions"):
        path = _doc(config, key)
        if path is not None:
            roots.add(path.parent)
    for key in ("benchmarks", "runs"):
        path = _doc(config, key)
        if path is not None:
            roots.add(path)
    return sorted(roots)


def _subsection(body: str, title: str) -> str | None:
    match = re.search(rf"^### {re.escape(title)}\s*$", body, flags=re.MULTILINE)
    if not match:
        return None
    rest = body[match.end():]
    following = re.search(r"^#{2,3} ", rest, flags=re.MULTILINE)
    return rest[: following.start()] if following else rest


def _code(cell: str) -> str:
    return cell.strip().strip("`").strip()


def _first_code(text: str) -> str | None:
    match = re.search(r"`([^`]+)`", text)
    return match.group(1) if match else None


def _relative(config: Config, path: Path) -> str:
    return path.relative_to(config.project_root).as_posix() if path.is_relative_to(config.project_root) else str(path)


def _at_base(config: Config, path: Path, base: str) -> str | None:
    lines = _git(config, "show", f"{base}:{_relative(config, path)}", keep_blank=True)
    return None if lines is None else "\n".join(lines)


def _git(config: Config, *arguments: str, keep_blank: bool = False) -> list[str] | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(config.project_root), "-c", "core.quotepath=off", *arguments],
            capture_output=True, text=True, timeout=60, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return [line for line in completed.stdout.splitlines() if keep_blank or line.strip()]
