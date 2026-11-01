"""The benchmark runner: N repetitions per candidate, one result row each.

Per repetition: bring the compose stack down and up fresh, wait for health,
capture the service's timestamped log, run the dataset's scenarios with the
test-start marker, bring the stack down. The variable under test is swapped
in the env file for the candidate and restored on exit.
Reference: docs/process/benchmark.md (step 11), docs/decisions/0006-plugin-ships-runner.md.
"""

import os
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from . import envfile
from .config import Config, Service
from .dataset import Scenario, append_row, selection
from .language import words
from .report import Candidate, aggregate, breakdown, read_repetition, row_cells

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
PLUGIN = "kanku_pytest_plugin"


def log(message: str) -> None:
    print(f"kanku: {message}", file=sys.stderr, flush=True)


def compose(config: Config, service: Service, *args: str, **kwargs) -> subprocess.CompletedProcess:
    files = [arg for path in service.acceptance.compose for arg in ("-f", path)]
    return subprocess.run(["docker", "compose", *files, *args], cwd=config.project_root, check=False, **kwargs)


def wait_healthy(url: str, timeout: int) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status < 400:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(5)
    return False


def commit(project_root: Path) -> str:
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=project_root, capture_output=True, text=True, check=False).stdout.strip() or "unknown"
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=project_root, capture_output=True, text=True, check=False).stdout.strip()
    return f"{head}+dirty" if dirty else head


def repetition(config: Config, service: Service, scenarios: list[Scenario], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    acceptance = service.acceptance
    compose(config, service, "down", "-v", capture_output=True)
    if compose(config, service, "build").returncode != 0:
        raise RuntimeError("docker compose build failed")
    if compose(config, service, "up", "-d", "--no-build").returncode != 0:
        raise RuntimeError("docker compose up failed")
    try:
        if not wait_healthy(acceptance.health, acceptance.health_timeout):
            raise RuntimeError(f"{acceptance.health} did not become healthy in {acceptance.health_timeout}s")
        files = [arg for path in acceptance.compose for arg in ("-f", path)]
        with open(out / "container.log", "w", encoding="utf-8") as container_log:
            follower = subprocess.Popen(
                ["docker", "compose", *files, "logs", "-f", "--timestamps", acceptance.container],
                cwd=config.project_root, stdout=container_log, stderr=subprocess.STDOUT,
            )
            try:
                environment = dict(os.environ)
                environment.update(acceptance.env)
                environment["PYTHONPATH"] = str(SCRIPTS_DIR) + (os.pathsep + environment["PYTHONPATH"] if environment.get("PYTHONPATH") else "")
                command = f"{acceptance.test} -v -s --tb=short -p {PLUGIN} -k {shlex.quote(selection(scenarios))}"
                with open(out / "pytest.log", "w", encoding="utf-8") as pytest_log:
                    process = subprocess.Popen(command, shell=True, cwd=config.project_root, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    for line in process.stdout:
                        pytest_log.write(line)
                        sys.stdout.write(line)
                    process.wait()
            finally:
                time.sleep(2)
                follower.terminate()
                follower.wait(timeout=30)
    finally:
        compose(config, service, "down", "-v", capture_output=True)


def benchmark(
    config: Config,
    service: Service,
    variable: str,
    dataset: Path,
    scenarios: list[Scenario],
    candidates: list[Candidate],
    other_variables: str,
    catalog_date: str,
    repetitions: int,
    notes: str = "",
) -> list[list[str]]:
    language = config.language
    controls = {s.name for s in scenarios if s.control}
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    rows = []
    for candidate in candidates:
        run_dir = config.results_dir / service.name / f"{candidate.model.replace('/', '_').replace(':', '_')}_{run_id}"
        with envfile.swapped(config.env_file, variable, candidate.model):
            for index in range(1, repetitions + 1):
                log(f"{variable}={candidate.model} — repetition {index}/{repetitions}")
                repetition(config, service, scenarios, run_dir / f"rep{index}")
        rows.append(record(config, service, variable, dataset, run_dir, candidate, other_variables, catalog_date, controls, notes))
    return rows


def record(config, service, variable, dataset, run_dir, candidate, other_variables, catalog_date, controls, notes="", run_date=None, commit_id=None) -> list[str]:
    language = config.language
    reps = [read_repetition(path, candidate.model, words(language)["unattributed"]) for path in sorted(run_dir.glob("rep*")) if (path / "pytest.log").is_file()]
    if not reps:
        raise RuntimeError(f"no repetition with a pytest.log under {run_dir}")
    result = aggregate(reps, candidate.prices, controls, service.classify_model, service.classify_environment)
    run_date = run_date or datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    cells = row_cells(
        result, run_date=run_date, model=candidate.model, other_variables=other_variables,
        commit=commit_id or commit(config.project_root), catalog_date=catalog_date, notes=notes, language=language,
    )
    append_row(dataset, variable, language, cells)
    (run_dir / "scenario_breakdown.md").write_text(breakdown(reps, f"{candidate.model} — {run_date}", language), encoding="utf-8")
    log(f"row appended to {dataset}; breakdown at {run_dir / 'scenario_breakdown.md'}")
    return cells
