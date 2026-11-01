"""Load the project adapter, `.claude/kanku.yaml`.

The adapter is the only place a project tells kanku what it has. Every
other module reads its values from here, so nothing in kanku knows about a
particular project. Reference: docs/adapter.md.
"""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

ADAPTER_PATH = Path(".claude") / "kanku.yaml"
SUPPORTED_VERSION = 1
LANGUAGES = ("en", "es")


class AdapterError(Exception):
    pass


@dataclass(frozen=True)
class Acceptance:
    compose: tuple[str, ...]
    container: str
    health: str
    test: str
    env: dict[str, str] = field(default_factory=dict)
    health_timeout: int = 200
    full_stats: str | None = None


@dataclass(frozen=True)
class Service:
    name: str
    variables: tuple[str, ...]
    acceptance: Acceptance | None
    side_effect_keys: tuple[str, ...] = ()
    classify_model: tuple[str, ...] = ()
    classify_environment: tuple[str, ...] = ()


@dataclass(frozen=True)
class Config:
    project_root: Path
    raw: dict
    language: str
    env_file: Path
    services: dict[str, Service]
    repetitions: int
    command: str | None
    results_dir: Path
    docs: dict[str, object]
    min_tool_success_rate: float
    max_unrated_days: int

    def service(self, name: str) -> Service:
        if name not in self.services:
            raise AdapterError(f"no service '{name}' in the adapter (have: {', '.join(sorted(self.services))})")
        return self.services[name]


def load_config(project_root: Path, adapter: Path | None = None) -> Config:
    path = adapter or project_root / ADAPTER_PATH
    if not path.is_file():
        raise AdapterError(f"no adapter at {path} — run /kanku:init")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as error:
        raise AdapterError(f"{path}: not valid YAML: {error}") from None
    if not isinstance(raw, dict):
        raise AdapterError(f"{path}: the adapter must be a mapping")
    if raw.get("version") != SUPPORTED_VERSION:
        raise AdapterError(f"{path}: version must be {SUPPORTED_VERSION}")
    language = raw.get("language", "en")
    if language not in LANGUAGES:
        raise AdapterError(f"{path}: language must be one of {', '.join(LANGUAGES)}")
    catalog = raw.get("catalog") or {}
    if catalog.get("provider", "openrouter") != "openrouter":
        raise AdapterError(f"{path}: catalog.provider must be openrouter")
    services_raw = raw.get("services") or {}
    if not isinstance(services_raw, dict) or not services_raw:
        raise AdapterError(f"{path}: services must name at least one service")
    benchmark = raw.get("benchmark") or {}
    return Config(
        project_root=project_root,
        raw=raw,
        language=language,
        env_file=project_root / raw.get("env_file", ".env"),
        services={name: _service(name, value or {}, path) for name, value in services_raw.items()},
        repetitions=int(benchmark.get("repetitions", 3)),
        command=benchmark.get("command"),
        results_dir=project_root / benchmark.get("results_dir", "benchmark_results"),
        docs=raw.get("docs") or {},
        min_tool_success_rate=float(catalog.get("min_tool_success_rate", 0.9)),
        max_unrated_days=int(catalog.get("max_unrated_days", 90)),
    )


def _service(name: str, raw: dict, path: Path) -> Service:
    variables = tuple(raw.get("variables") or ())
    if not variables:
        raise AdapterError(f"{path}: services.{name}.variables must list the service's model variables")
    acceptance_raw = raw.get("acceptance")
    acceptance = None
    if acceptance_raw:
        missing = [key for key in ("compose", "container", "health", "test") if not acceptance_raw.get(key)]
        if missing:
            raise AdapterError(f"{path}: services.{name}.acceptance needs {', '.join(missing)}")
        compose = acceptance_raw["compose"]
        acceptance = Acceptance(
            compose=tuple([compose] if isinstance(compose, str) else compose),
            container=acceptance_raw["container"],
            health=acceptance_raw["health"],
            test=acceptance_raw["test"],
            env={str(key): str(value) for key, value in (acceptance_raw.get("env") or {}).items()},
            health_timeout=int(acceptance_raw.get("health_timeout", 200)),
            full_stats=acceptance_raw.get("full_stats"),
        )
    classify = raw.get("classify") or {}
    return Service(
        name=name,
        variables=variables,
        acceptance=acceptance,
        side_effect_keys=tuple(raw.get("side_effect_keys") or ()),
        classify_model=tuple(classify.get("model") or ()),
        classify_environment=tuple(classify.get("environment") or ()),
    )
