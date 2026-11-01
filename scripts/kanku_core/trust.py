"""The user's approval of the adapter.

The runner executes commands taken from the adapter — compose files, test
commands, a whole replacement runner — unattended, with the real
environment file mounted. It runs only an adapter whose exact content the
user approved with `/kanku:trust`. Approvals live outside every repository,
in the user's state directory, keyed by the repository's git common
directory (shared by its worktrees). Reference: docs/decisions/0009-trust-by-hash.md.
"""

import hashlib
import json
import os
import subprocess
from pathlib import Path

from .config import Config


def trust_file() -> Path:
    if os.environ.get("KANKU_TRUST_FILE"):
        return Path(os.environ["KANKU_TRUST_FILE"])
    state = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(state) / "kanku" / "trusted-adapters.json"


def adapter_hash(config: Config) -> str:
    return hashlib.sha256(json.dumps(config.raw, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def repository_key(project_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return str(project_root.resolve())
    if completed.returncode != 0 or not completed.stdout.strip():
        return str(project_root.resolve())
    return str((project_root / completed.stdout.strip()).resolve())


def is_trusted(config: Config) -> bool:
    return _load().get(repository_key(config.project_root)) == adapter_hash(config)


def trust(config: Config) -> Path:
    approvals = _load()
    approvals[repository_key(config.project_root)] = adapter_hash(config)
    path = trust_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(approvals, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def summary(config: Config) -> str:
    """What approving this adapter lets kanku run."""
    lines = [f"env file: {config.env_file.relative_to(config.project_root) if config.env_file.is_relative_to(config.project_root) else config.env_file}"]
    if config.command:
        lines.append(f"benchmark.command (replaces kanku's runner): {config.command}")
    for service in config.services.values():
        lines.append(f"service {service.name}: variables {', '.join(service.variables)}")
        if service.acceptance:
            a = service.acceptance
            lines.append(f"  compose: {', '.join(a.compose)} (container {a.container}, health {a.health})")
            lines.append(f"  test: {a.test}")
            if a.env:
                lines.append(f"  test env: {', '.join(f'{k}={v}' for k, v in a.env.items())}")
            if a.full_stats:
                lines.append(f"  full acceptance: {a.full_stats}")
        else:
            lines.append("  no acceptance: decided from the catalog")
        if service.side_effect_keys:
            lines.append(f"  must resolve empty: {', '.join(service.side_effect_keys)}")
    return "\n".join(lines)


def _load() -> dict[str, str]:
    path = trust_file()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}
