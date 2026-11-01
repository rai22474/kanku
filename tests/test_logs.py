import unittest
from datetime import UTC, datetime

from kanku_core.logs import attribute, is_candidate, parse_calls, parse_outcomes, parse_timestamp, percentile


class CallsTest(unittest.TestCase):
    def test_docker_prefixed_line(self):
        line = "app-1  | 2026-09-11T18:55:30.888203000Z 2026-09-11 18:55:30,887 - x - INFO - llm_call model=openrouter/a/b duration=2.146 status=success input_tokens=1319 output_tokens=111 reasoning_tokens=21 cached_tokens=7"
        (call,) = parse_calls(line)
        self.assertEqual(call["model"], "openrouter/a/b")
        self.assertEqual(call["duration"], 2.146)
        self.assertEqual((call["input_tokens"], call["output_tokens"], call["reasoning_tokens"], call["cached_tokens"]), (1319, 111, 21, 7))
        self.assertEqual(call["timestamp"], datetime(2026, 9, 11, 18, 55, 30, 888203, tzinfo=UTC))

    def test_line_without_timestamp_still_counts(self):
        (call,) = parse_calls("llm_call model=a/b duration=1.0 status=error input_tokens=1 output_tokens=2 reasoning_tokens=0 cached_tokens=0")
        self.assertIsNone(call["timestamp"])
        self.assertEqual(call["status"], "error")

    def test_missing_counts_are_zero(self):
        (call,) = parse_calls("llm_call model=a/b duration=1.0")
        self.assertEqual(call["cached_tokens"], 0)

    def test_other_lines_ignored(self):
        self.assertEqual(parse_calls("INFO started\nllm_call_count=3"), [])


class CandidateTest(unittest.TestCase):
    def test_router_prefix(self):
        self.assertTrue(is_candidate("openrouter/a/b", "a/b"))
        self.assertTrue(is_candidate("a/b", "a/b"))
        self.assertFalse(is_candidate("openrouter/a/bc", "a/b"))


class OutcomesTest(unittest.TestCase):
    def test_outcome_on_the_line_after_the_marker(self):
        log = (
            "t.py::test_a BENCHMARK_TEST_START t.py::test_a 2026-01-01T00:00:00+00:00\n"
            "PASSED\n"
            "t.py::test_b BENCHMARK_TEST_START t.py::test_b 2026-01-01T00:01:00+00:00\n"
            "FAILED\n"
        )
        passed, failed, windows = parse_outcomes(log)
        self.assertEqual((passed, failed), (["test_a"], ["test_b"]))
        self.assertEqual([w["test"] for w in windows], ["test_a", "test_b"])

    def test_without_markers(self):
        passed, failed, windows = parse_outcomes("t.py::test_a PASSED\nt.py::test_b FAILED\n")
        self.assertEqual((passed, failed, windows), (["test_a"], ["test_b"], []))


class AttributionTest(unittest.TestCase):
    def test_window_from_marker_to_next(self):
        windows = [{"test": "a", "start": parse_timestamp("2026-01-01T00:00:00Z")}, {"test": "b", "start": parse_timestamp("2026-01-01T00:01:00Z")}]
        calls = [{"timestamp": parse_timestamp(t)} for t in ("2025-12-31T23:59:59Z", "2026-01-01T00:00:30Z", "2026-01-01T00:01:00Z")] + [{"timestamp": None}]
        grouped = attribute(calls, windows, "unattributed")
        self.assertEqual({k: len(v) for k, v in grouped.items()}, {"unattributed": 2, "a": 1, "b": 1})


class PercentileTest(unittest.TestCase):
    def test_interpolates(self):
        self.assertEqual(percentile([1, 2, 3, 4], 0.5), 2.5)
        self.assertIsNone(percentile([], 0.5))


if __name__ == "__main__":
    unittest.main()
