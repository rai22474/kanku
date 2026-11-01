"""Command line: `kanku gates`, `benchmark`, `report`, `trust`.

Run it through `scripts/kanku`, which finds a Python with PyYAML.
Reference: docs/process/benchmark.md.
"""

import argparse
import shlex
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from . import gates, runner
from .config import AdapterError, load_config
from .dataset import DatasetError, scenarios
from .report import Candidate
from .trust import is_trusted, summary, trust


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        config = load_config(Path(arguments.project).resolve())
        return arguments.handler(config, arguments)
    except (AdapterError, DatasetError, ValueError, RuntimeError) as error:
        print(f"kanku: {error}", file=sys.stderr)
        return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kanku")
    parser.add_argument("--project", default=".")
    commands = parser.add_subparsers(required=True)

    def target(sub):
        sub.add_argument("--service", required=True)
        sub.add_argument("--variable", required=True)
        sub.add_argument("--dataset", required=True, type=Path)
        sub.add_argument("--allow-unset", action="append", default=[], metavar="VARIABLE", help="another variable whose decision is the default (left unset on purpose)")

    sub = commands.add_parser("gates", help="run the launch gates without launching")
    target(sub)
    sub.set_defaults(handler=run_gates)

    sub = commands.add_parser("benchmark", help="run the launch gates, then the benchmark")
    target(sub)
    sub.add_argument("--catalog-date", default=datetime.now(UTC).strftime("%Y-%m-%d"), help="when the prices were read from the catalog")
    sub.add_argument("--repetitions", type=int)
    sub.add_argument("--notes", default="")
    sub.add_argument("candidates", nargs="+", metavar="model:prompt:completion[:cache_read]")
    sub.set_defaults(handler=run_benchmark)

    sub = commands.add_parser("report", help="aggregate an existing run directory into a row")
    target(sub)
    sub.add_argument("--run-dir", required=True, type=Path)
    sub.add_argument("--candidate", required=True, metavar="model:prompt:completion[:cache_read]")
    sub.add_argument("--catalog-date", required=True)
    sub.add_argument("--other-variables", required=True)
    sub.add_argument("--commit", required=True)
    sub.add_argument("--run-date", required=True)
    sub.add_argument("--notes", default="")
    sub.set_defaults(handler=run_report)

    sub = commands.add_parser("trust", help="show what the adapter makes kanku run; --approve records the approval")
    sub.add_argument("--approve", action="store_true")
    sub.set_defaults(handler=run_trust)
    return parser


def run_gates(config, arguments) -> int:
    service = config.service(arguments.service)
    problems, others = gates.launch(config, service, arguments.variable, arguments.dataset, tuple(arguments.allow_unset))
    for problem in problems:
        print(f"kanku: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"kanku: launch gates pass. Other variables: {others}")
    return 0


def run_benchmark(config, arguments) -> int:
    service = config.service(arguments.service)
    candidates = [Candidate.parse(spec) for spec in arguments.candidates]
    problems, others = gates.launch(config, service, arguments.variable, arguments.dataset, tuple(arguments.allow_unset))
    for problem in problems:
        print(f"kanku: {problem}", file=sys.stderr)
    if problems:
        return 1
    scenario_list = scenarios(arguments.dataset, config.language)
    repetitions = arguments.repetitions or config.repetitions
    if config.command:
        command = " ".join([config.command, "--service", service.name, "--variable", arguments.variable, "--dataset", str(arguments.dataset), "--repetitions", str(repetitions), *arguments.candidates])
        return subprocess.run(shlex.split(command), cwd=config.project_root, check=False).returncode
    rows = runner.benchmark(
        config, service, arguments.variable, arguments.dataset, scenario_list, candidates,
        others, arguments.catalog_date, repetitions, arguments.notes,
    )
    for row in rows:
        print("| " + " | ".join(row) + " |")
    return 0


def run_report(config, arguments) -> int:
    service = config.service(arguments.service)
    scenario_list = scenarios(arguments.dataset, config.language)
    row = runner.record(
        config, service, arguments.variable, arguments.dataset, arguments.run_dir, Candidate.parse(arguments.candidate),
        arguments.other_variables, arguments.catalog_date, {s.name for s in scenario_list if s.control},
        arguments.notes, arguments.run_date, arguments.commit,
    )
    print("| " + " | ".join(row) + " |")
    return 0


def run_trust(config, arguments) -> int:
    print(summary(config))
    if arguments.approve:
        path = trust(config)
        print(f"kanku: adapter approved ({path})")
    else:
        print("kanku: approved" if is_trusted(config) else "kanku: NOT approved — /kanku:trust approves it")
    return 0
