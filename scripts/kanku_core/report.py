"""Aggregate a candidate's repetitions into one result row.

Pass rate, failures by class, exact per-call latency and effective cost,
all from the two logs of each repetition. Reference: docs/measurement.md,
docs/artifacts/dataset.md.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from .language import words
from .logs import attribute, failure_tracebacks, is_candidate, parse_calls, parse_outcomes, percentile

DEFAULT_MODEL_PATTERNS = (r"JSONDecodeError",)
DEFAULT_ENVIRONMENT_PATTERNS = (r"ConnectionError", r"ConnectionRefusedError", r"TimeoutError")


@dataclass(frozen=True)
class Prices:
    """USD per million tokens. No cache price means no cache discount."""

    prompt: float
    completion: float
    cache_read: float | None = None

    def cost(self, call: dict) -> float:
        cached = min(call["cached_tokens"], call["input_tokens"])
        cache_price = self.cache_read if self.cache_read is not None else self.prompt
        return (
            (call["input_tokens"] - cached) * self.prompt
            + cached * cache_price
            + call["output_tokens"] * self.completion
        ) / 1_000_000


@dataclass(frozen=True)
class Candidate:
    model: str
    prices: Prices

    @staticmethod
    def parse(spec: str) -> "Candidate":
        """`model:prompt:completion[:cache_read]`, read from the right: model ids may hold colons (`:free`)."""

        def number(text: str) -> bool:
            try:
                float(text)
            except ValueError:
                return False
            return True

        parts = spec.split(":")
        if len(parts) >= 4 and number(parts[-3]) and number(parts[-2]) and (parts[-1] == "" or number(parts[-1])):
            cache = float(parts[-1]) if parts[-1] else None
            return Candidate(":".join(parts[:-3]), Prices(float(parts[-3]), float(parts[-2]), cache))
        if len(parts) >= 3 and number(parts[-2]) and number(parts[-1]):
            return Candidate(":".join(parts[:-2]), Prices(float(parts[-2]), float(parts[-1])))
        raise ValueError(f"candidate '{spec}' must be model:prompt:completion[:cache_read]")


def read_repetition(run_dir: Path, candidate: str, unattributed: str) -> dict:
    pytest_log = (run_dir / "pytest.log").read_text(encoding="utf-8", errors="replace")
    container = run_dir / "container.log"
    calls = []
    if container.is_file():
        calls = [c for c in parse_calls(container.read_text(encoding="utf-8", errors="replace")) if is_candidate(c["model"], candidate)]
    passed, failed, windows = parse_outcomes(pytest_log)
    return {
        "passed": passed,
        "failed": failed,
        "tracebacks": failure_tracebacks(pytest_log, failed),
        "calls": calls,
        "by_scenario": attribute(calls, windows, unattributed),
    }


def classify(name: str, traceback: str, controls: set[str], model: list[re.Pattern], environment: list[re.Pattern]) -> str:
    if name in controls:
        return "control"
    if any(pattern.search(traceback) for pattern in model):
        return "model"
    if any(pattern.search(traceback) for pattern in environment):
        return "environment"
    return "other"


def aggregate(
    repetitions: list[dict],
    prices: Prices,
    controls: set[str],
    model_patterns: tuple[str, ...] = (),
    environment_patterns: tuple[str, ...] = (),
) -> dict:
    model = [re.compile(p) for p in DEFAULT_MODEL_PATTERNS + tuple(model_patterns)]
    environment = [re.compile(p, re.IGNORECASE) for p in DEFAULT_ENVIRONMENT_PATTERNS + tuple(environment_patterns)]
    rates = [len(r["passed"]) / (len(r["passed"]) + len(r["failed"])) for r in repetitions if r["passed"] or r["failed"]]
    counts = {"model": 0, "environment": 0, "control": 0, "other": 0}
    unclassified, failed_controls = set(), set()
    for repetition in repetitions:
        for name in repetition["failed"]:
            category = classify(name, repetition["tracebacks"].get(name, ""), controls, model, environment)
            counts[category] += 1
            if category == "other":
                unclassified.add(name)
            if category == "control":
                failed_controls.add(name)
    failures = sum(counts.values())
    calls = [call for r in repetitions for call in r["calls"]]
    durations = [call["duration"] for call in calls]
    scenarios_per_repetition = sum(len(r["passed"]) + len(r["failed"]) for r in repetitions) / max(len(repetitions), 1)
    cost = None
    if calls and scenarios_per_repetition:
        cost = sum(prices.cost(call) for call in calls) / len(repetitions) / scenarios_per_repetition

    def share(n: int) -> float:
        return round(100 * n / failures, 1) if failures else 0.0

    return {
        "passed_pct": round(100 * sum(rates) / len(rates), 1) if rates else 0.0,
        "model_pct": share(counts["model"]),
        "environment_pct": share(counts["environment"] + counts["control"]),
        "other_pct": share(counts["other"]),
        "unclassified": sorted(unclassified),
        "failed_controls": sorted(failed_controls),
        "calls": len(calls),
        "mean": sum(durations) / len(durations) if durations else None,
        "p50": percentile(durations, 0.5),
        "p90": percentile(durations, 0.9),
        "p95": percentile(durations, 0.95),
        "min": min(durations) if durations else None,
        "max": max(durations) if durations else None,
        "cost": cost,
    }


def row_cells(result: dict, *, run_date: str, model: str, other_variables: str, commit: str, catalog_date: str, notes: str, language: str) -> list[str]:
    w = words(language)

    def seconds(value):
        return "n/a" if value is None else f"{value:.2f}s"

    extra = []
    if notes:
        extra.append(notes)
    if result["other_pct"]:
        extra.append(f"{result['other_pct']}% {w['unclassified']}: {', '.join(result['unclassified'])}")
    if result["failed_controls"]:
        extra.append(f"{w['controls']}: {', '.join(result['failed_controls'])}")
    return [
        run_date,
        f"`{model}`",
        other_variables,
        commit,
        catalog_date,
        f"{result['passed_pct']}%",
        f"{result['model_pct']}%",
        f"{result['environment_pct']}%",
        seconds(result["mean"]),
        seconds(result["p50"]),
        seconds(result["p90"]),
        seconds(result["p95"]),
        seconds(result["min"]),
        seconds(result["max"]),
        "n/a" if result["cost"] is None else f"${result['cost']:.5f}",
        "; ".join(extra) or "—",
    ]


def breakdown(repetitions: list[dict], title: str, language: str) -> str:
    w = words(language)
    names = sorted({name for r in repetitions for name in r["by_scenario"]})
    lines = [f"# {w['breakdown_title']} — {title}", "", "| " + " | ".join(w["breakdown_columns"]) + " |", "|" + "---|" * len(w["breakdown_columns"])]
    for name in names:
        calls = [call for r in repetitions for call in r["by_scenario"].get(name, [])]
        durations = [call["duration"] for call in calls]
        lines.append(
            f"| {name} | {len(calls)} | {sum(durations) / len(durations):.2f}s | {percentile(durations, 0.5):.2f}s | "
            f"{percentile(durations, 0.9):.2f}s | {percentile(durations, 0.95):.2f}s | {max(durations):.2f}s | "
            f"{sum(c['input_tokens'] for c in calls)} | {sum(c['output_tokens'] for c in calls)} | "
            f"{sum(c['reasoning_tokens'] for c in calls)} | {sum(c['cached_tokens'] for c in calls)} |"
        )
    return "\n".join(lines) + "\n"
