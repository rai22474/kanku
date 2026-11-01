"""Parse the two artifacts of a repetition: the pytest log and the container log.

The container log carries one `llm_call` line per model call; the pytest log
carries a `BENCHMARK_TEST_START` marker per test and pytest's verbose
outcomes. Reference: docs/measurement.md.
"""

import re
from collections import defaultdict
from datetime import UTC, datetime

LLM_CALL = re.compile(r"llm_call (?P<pairs>(?:\w+=\S+\s*)+)")
PAIR = re.compile(r"(\w+)=(\S+)")
DOCKER_PREFIX = re.compile(r"^\S+\s+\|\s+(?P<timestamp>\d{4}-\d\d-\d\dT\S+)\s")
LEADING_TIMESTAMP = re.compile(r"^(?P<timestamp>\d{4}-\d\d-\d\dT\S+)\s")
TEST_START = re.compile(r"BENCHMARK_TEST_START (?P<nodeid>\S+) (?P<timestamp>\S+)")
TOKEN_FIELDS = ("input_tokens", "output_tokens", "reasoning_tokens", "cached_tokens")


def test_name(nodeid: str) -> str:
    """The function name a node id ends in — what -k selects and pytest reports."""
    return nodeid.strip().strip("`").rsplit("::", 1)[-1]


def parse_timestamp(raw: str) -> datetime:
    """RFC 3339 with up to nanoseconds and a Z or an offset; naive means UTC."""
    raw = raw.strip()
    offset = ""
    if raw.endswith("Z"):
        raw = raw[:-1]
    else:
        match = re.search(r"[+-]\d\d:\d\d$", raw)
        if match:
            offset, raw = match.group(0), raw[: match.start()]
    if "." in raw:
        whole, fraction = raw.split(".", 1)
        raw = f"{whole}.{fraction[:6]}"
    parsed = datetime.fromisoformat(raw + offset)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def parse_calls(container_log: str) -> list[dict]:
    calls = []
    for line in container_log.splitlines():
        match = LLM_CALL.search(line)
        if not match:
            continue
        pairs = dict(PAIR.findall(match.group("pairs")))
        if "model" not in pairs or "duration" not in pairs:
            continue
        stamp = DOCKER_PREFIX.match(line) or LEADING_TIMESTAMP.match(line)
        call = {
            "timestamp": parse_timestamp(stamp.group("timestamp")) if stamp else None,
            "model": pairs["model"],
            "duration": float(pairs["duration"]),
            "status": pairs.get("status", "success"),
        }
        for key in TOKEN_FIELDS:
            call[key] = int(pairs.get(key, 0) or 0)
        calls.append(call)
    return calls


def is_candidate(call_model: str, candidate: str) -> bool:
    """A call is the candidate's when its model is the candidate, maybe behind a router prefix."""
    return call_model == candidate or call_model.endswith("/" + candidate)


def parse_outcomes(pytest_log: str) -> tuple[list[str], list[str], list[dict]]:
    """(passed names, failed names, test windows).

    pytest's verbose reporter and the marker print interleave: the outcome
    can land on the line after the marker instead of after the node id. So
    the last marker seen is the current test. Without markers, falls back to
    `nodeid PASSED` on one line.
    """
    lines = pytest_log.splitlines()
    windows = []
    for line in lines:
        match = TEST_START.search(line)
        if match:
            windows.append({"test": test_name(match.group("nodeid")), "start": parse_timestamp(match.group("timestamp"))})
    windows.sort(key=lambda window: window["start"])
    if not windows:
        passed = [test_name(n) for n in re.findall(r"^(\S+::\S+) PASSED", pytest_log, flags=re.MULTILINE)]
        failed = [test_name(n) for n in re.findall(r"^(\S+::\S+) FAILED", pytest_log, flags=re.MULTILINE)]
        return passed, failed, []
    passed, failed, current = [], [], None
    for line in lines:
        match = TEST_START.search(line)
        if match:
            current = test_name(match.group("nodeid"))
            continue
        stripped = line.strip()
        if current and stripped.startswith("PASSED"):
            passed.append(current)
            current = None
        elif current and (stripped.startswith("FAILED") or stripped.startswith("ERROR")):
            failed.append(current)
            current = None
    return passed, failed, windows


def failure_tracebacks(pytest_log: str, failed: list[str]) -> dict[str, str]:
    tracebacks = {}
    for name in failed:
        match = re.search(rf"_+ {re.escape(name)} _+\n(.*?)(?=\n_{{5,}} |\n=+ )", pytest_log, re.DOTALL)
        tracebacks[name] = match.group(1) if match else ""
    return tracebacks


def attribute(calls: list[dict], windows: list[dict], unattributed: str) -> dict[str, list[dict]]:
    """Each call goes to the test whose window — its marker to the next — holds it."""
    grouped = defaultdict(list)
    for call in calls:
        scenario = unattributed
        if call["timestamp"] is not None:
            for index, window in enumerate(windows):
                end = windows[index + 1]["start"] if index + 1 < len(windows) else None
                if call["timestamp"] >= window["start"] and (end is None or call["timestamp"] < end):
                    scenario = window["test"]
                    break
        grouped[scenario].append(call)
    return dict(grouped)


def percentile(values: list[float], target: float) -> float | None:
    """Linear interpolation between closest ranks."""
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * target
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight
