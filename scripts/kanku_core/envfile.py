"""Read and swap one variable in the project's environment file.

The file holds secrets: nothing here returns or prints a value other than
a model variable's, and the swap restores the original line on exit — also
when the run fails or is interrupted. Reference: docs/process/working-rules.md#secrets.
"""

import re
import signal
from contextlib import contextmanager
from pathlib import Path


def _line_pattern(key: str) -> re.Pattern:
    return re.compile(rf"^(?:export\s+)?{re.escape(key)}=(.*)$", re.MULTILINE)


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value.split(" #", 1)[0].strip()


def model_value(path: Path, key: str) -> str | None:
    """The value of a model variable — never call it for anything else. None when unset or empty."""
    if not path.is_file():
        return None
    matches = _line_pattern(key).findall(path.read_text(encoding="utf-8"))
    value = _unquote(matches[-1]) if matches else ""
    return value or None


def _write_line(path: Path, key: str, line: str | None) -> None:
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    pattern = _line_pattern(key)
    if line is None:
        text = pattern.sub("", text)
        text = re.sub(r"\n{2,}$", "\n", text)
    elif pattern.search(text):
        text = pattern.sub(lambda _: line, text, count=1)
    else:
        text = text + ("" if text.endswith("\n") or not text else "\n") + line + "\n"
    path.write_text(text, encoding="utf-8")


@contextmanager
def swapped(path: Path, key: str, value: str):
    """Set `key=value` for the duration, then put back exactly the line that was there (or none)."""
    original = None
    if path.is_file():
        match = _line_pattern(key).search(path.read_text(encoding="utf-8"))
        original = match.group(0) if match else None
    previous = {}

    def interrupt(signum, _frame):
        raise KeyboardInterrupt(f"signal {signum}")

    for signum in (signal.SIGTERM, signal.SIGHUP):
        previous[signum] = signal.signal(signum, interrupt)
    try:
        _write_line(path, key, f"{key}={value}")
        yield
    finally:
        _write_line(path, key, original)
        for signum, handler in previous.items():
            signal.signal(signum, handler)
