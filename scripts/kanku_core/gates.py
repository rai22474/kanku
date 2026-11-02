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

REACH_MARKER = "kanku/reach-check"


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


def compose_command(config: Config, service: Service) -> list[str]:
    """`docker compose` with the stack's files, interpolating from the adapter's env file.

    The env file is the one the runner swaps, so `${VAR}` in a compose file
    sees the candidate as well as `env_file:` does.
    """
    command = ["docker", "compose"]
    if config.env_file.is_file():
        command += ["--env-file", str(config.env_file)]
    return command + [arg for path in service.acceptance.compose for arg in ("-f", path)]


def compose_config(config: Config, service: Service, runner=subprocess.run) -> dict:
    """The resolved compose configuration. It holds secrets: keep it in memory, never print it."""
    completed = runner(
        [*compose_command(config, service), "config", "--format", "json"],
        cwd=config.project_root, capture_output=True, text=True, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("docker compose config failed (output withheld: it may hold secrets)")
    return json.loads(completed.stdout)


def reaches(resolved: dict, service: Service, variable: str, expected: str) -> list[Problem]:
    """Step 10: the variable under test reaches the container from the env file.

    Checked with a marker value swapped into the env file: anything else in
    the container — a value the compose file sets, a variable it never
    passes — means every candidate would run the same model, silently.
    """
    definition = (resolved.get("services") or {}).get(service.acceptance.container)
    if definition is None:
        return [Problem("reaches", f"the compose stack has no service '{service.acceptance.container}' (acceptance.container)")]
    environment = definition.get("environment") or {}
    if isinstance(environment, list):
        environment = dict(item.split("=", 1) if "=" in item else (item, "") for item in environment)
    if environment.get(variable) != expected:
        how = "is not passed to it" if variable not in environment else "gets a value the env file doesn't control (set under environment:?)"
        return [Problem("reaches", f"{variable} doesn't reach '{service.acceptance.container}' from the env file: it {how} — every candidate would run the same model")]
    return []


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
        with envfile.swapped(config.env_file, variable, REACH_MARKER):
            resolved = compose_config(config, service, runner)
    except (RuntimeError, ValueError, OSError) as error:
        problems.append(Problem("compose", str(error)))
        return problems, others
    problems += reaches(resolved, service, variable, REACH_MARKER)
    problems += side_effects(resolved, service)
    problems += nothing_running(resolved, service, running_projects(runner), in_use)
    return problems, others
