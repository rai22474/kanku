"""Loaded by kanku's runner with `-p kanku_pytest_plugin`.

Prints a timestamped marker at the start of each test, so each `llm_call`
line in the container log can be attributed to the scenario that made it.
Reference: docs/measurement.md#the-test-start-marker.
"""

import datetime
import sys


def pytest_runtest_logstart(nodeid, location):
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()
    print(f"BENCHMARK_TEST_START {nodeid} {timestamp}", file=sys.stdout, flush=True)
