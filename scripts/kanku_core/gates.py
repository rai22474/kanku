"""Launch gates: checked by code before any benchmark starts.

Each was skipped in practice by an agent that knew the rule; a run starts
only when all pass. None of them prints a value from the environment or
from the resolved compose configuration — only key names and empty or not.
Reference: docs/process/benchmark.md (steps 8 and 10), docs/decisions/0008-deterministic-gates.md.
"""

import json
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from . import envfile
from .config import Config, Service
from .dataset import DatasetError, check_results_table
from .trust import is_trusted


@dataclass(frozen=True)
class Problem:
    gate: str
    message: str

    def __str__(self) -> str:
        return f"[{self.gate}] {self.message}"


def pinned(config: Config, service: Service, variable: str, allow_unset: tuple[str, ...]) -> tuple[list[Problem], str]:
    """Step 8: every other model variable of the service is set explicitly. Returns the problems and the
    `Other variables` cell for the result row."""
    problems, cells = [], []
    for other in service.variables:
        if other == variable:
            continue
        value = envfile.model_value(config.env_file, other)
        if value:
            cells.append(f"{other}={value}")
        elif other in allow_unset:
            cells.append(f"{other}=(default)")
        else:
            problems.append(Problem("pinned", f"{other} is not set in the env file; set it to its decided value, or pass --allow-unset {other} if its decision is the default"))
    return problems, "; ".join(cells) or "—"


def compose_config(config: Config, service: Service, runner=subprocess.run) -> dict:
    """The resolved compose configuration. It holds secrets: keep it in memory, never print it."""
    files = [arg for path in service.acceptance.compose for arg in ("-f", path)]
    completed = runner(
        ["docker", "compose", *files, "config", "--format", "json"],
        cwd=config.project_root, capture_output=True, text=True, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("docker compose config failed (output withheld: it may hold secrets)")
    return json.loads(completed.stdout)


def side_effects(resolved: dict, service: Service) -> list[Problem]:
    """Step 10: every side-effect key resolves empty in every service of the stack."""
    problems = []
    for name, definition in (resolved.get("services") or {}).items():
        environment = definition.get("environment") or {}
        if isinstance(environment, list):
            environment = dict(item.split("=", 1) if "=" in item else (item, "") for item in environment)
        for key in service.side_effect_keys:
            if environment.get(key):
                problems.append(Problem("side-effects", f"{key} resolves non-empty in compose service '{name}'; blank it under environment:"))
    return problems


def running_projects(runner=subprocess.run) -> set[str]:
    completed = runner(["docker", "compose", "ls", "--format", "json"], capture_output=True, text=True, check=False)
    if completed.returncode != 0 or not completed.stdout.strip():
        return set()
    return {project.get("Name", "") for project in json.loads(completed.stdout)}


def published_ports(resolved: dict) -> set[int]:
    ports = set()
    for definition in (resolved.get("services") or {}).values():
        for port in definition.get("ports") or []:
            if isinstance(port, dict) and port.get("published"):
                ports.add(int(port["published"]))
    return ports


def port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        return probe.connect_ex((host, port)) == 0


def nothing_running(resolved: dict, service: Service, projects: set[str], in_use=port_in_use) -> list[Problem]:
    """Step 10: no other run holds the compose project or a port the stack publishes."""
    problems = []
    name = resolved.get("name")
    if name and name in projects:
        problems.append(Problem("nothing-running", f"compose project '{name}' is already running — another benchmark or acceptance run?"))
    ports = published_ports(resolved)
    health = urlparse(service.acceptance.health)
    if health.port:
        ports.add(health.port)
    for port in sorted(ports):
        if in_use(port):
            problems.append(Problem("nothing-running", f"port {port} is already in use"))
    return problems


def launch(config: Config, service: Service, variable: str, dataset: Path, allow_unset: tuple[str, ...] = (), runner=subprocess.run, in_use=port_in_use) -> tuple[list[Problem], str]:
    """Every launch gate. Returns the problems (empty: go) and the `Other variables` cell."""
    if not is_trusted(config):
        return [Problem("trust", "the adapter is not approved, or changed since — the user runs /kanku:trust")], "—"
    problems: list[Problem] = []
    if variable not in service.variables:
        problems.append(Problem("adapter", f"{variable} is not a variable of service '{service.name}'"))
    if service.acceptance is None:
        problems.append(Problem("adapter", f"service '{service.name}' has no acceptance: decide it from the catalog"))
        return problems, "—"
    if not config.env_file.is_file():
        problems.append(Problem("env", f"no env file at {config.env_file}"))
    try:
        check_results_table(dataset, variable, config.language)
    except (DatasetError, OSError) as error:
        problems.append(Problem("dataset", str(error)))
    pin_problems, others = pinned(config, service, variable, allow_unset)
    problems += pin_problems
    if config.command:
        return problems, others
    try:
        resolved = compose_config(config, service, runner)
    except (RuntimeError, ValueError) as error:
        problems.append(Problem("compose", str(error)))
        return problems, others
    problems += side_effects(resolved, service)
    problems += nothing_running(resolved, service, running_projects(runner), in_use)
    return problems, others
