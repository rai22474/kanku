"""The report, against a real run: the row the original harness wrote for it is the oracle.

Fixture: three repetitions of one candidate on a nine-scenario dataset, from
the project kanku grew in; container logs reduced to their llm_call lines,
local paths replaced. The original row: 70.4 % passed, failures 50 % model /
25 % environment / 25 % unclassified, latency mean 8.97 s, p50 4.50, p90
20.17, p95 32.38, min 0.44, max 79.37.
"""

import unittest

from fixture import FIXTURES
from kanku_core.report import Candidate, Prices, aggregate, read_repetition, row_cells

MODEL = "z-ai/glm-5.3-flash"
CONTROLS = {"test_pre_work_analysis"}
MODEL_PATTERNS = ("LlmCallsLimitExceededError",)
ENVIRONMENT_PATTERNS = (
    r"no (he )?pud[eo].*(meteorológic|pronóstico)",
    r"weather (service|api|data).*(error|fail|unavailable)",
    r"(error|fail).*weather (service|api|data)",
    r"host\.docker\.internal",
)


def repetitions():
    return [read_repetition(FIXTURES / "run_glm" / f"rep{i}", MODEL, "unattributed") for i in (1, 2, 3)]


class OracleTest(unittest.TestCase):
    def setUp(self):
        self.result = aggregate(repetitions(), Prices(0.15, 0.5, 0.03), CONTROLS, MODEL_PATTERNS, ENVIRONMENT_PATTERNS)

    def test_pass_rate(self):
        self.assertEqual(self.result["passed_pct"], 70.4)

    def test_failure_classes(self):
        self.assertEqual((self.result["model_pct"], self.result["environment_pct"], self.result["other_pct"]), (50.0, 25.0, 25.0))
        self.assertEqual(self.result["unclassified"], ["test_health_analysis_for_latest_photo", "test_protect_bonsai"])

    def test_latency(self):
        got = tuple(round(self.result[key], 2) for key in ("mean", "p50", "p90", "p95", "min", "max"))
        self.assertEqual(got, (8.97, 4.50, 20.17, 32.38, 0.44, 79.37))

    def test_only_the_candidates_calls_counted(self):
        # 257 llm_call lines: 187 of the candidate (behind the router prefix), 70 of a pinned variable's model.
        self.assertEqual(self.result["calls"], 187)


class CostTest(unittest.TestCase):
    def test_cached_tokens_billed_at_cache_price(self):
        call = {"input_tokens": 1_000_000, "cached_tokens": 400_000, "output_tokens": 100_000}
        self.assertAlmostEqual(Prices(1.0, 2.0, 0.1).cost(call), 0.6 + 0.04 + 0.2)

    def test_no_cache_price_means_no_discount(self):
        call = {"input_tokens": 1_000_000, "cached_tokens": 400_000, "output_tokens": 0}
        self.assertAlmostEqual(Prices(1.0, 2.0).cost(call), 1.0)

    def test_cost_is_per_scenario_per_repetition(self):
        rep = {"passed": ["a", "b"], "failed": [], "tracebacks": {}, "by_scenario": {},
               "calls": [{"duration": 1.0, "input_tokens": 1_000_000, "cached_tokens": 0, "output_tokens": 0}]}
        result = aggregate([rep, rep], Prices(1.0, 0.0), set())
        self.assertAlmostEqual(result["cost"], 2.0 / 2 / 2)


class CandidateTest(unittest.TestCase):
    def test_four_fields(self):
        self.assertEqual(Candidate.parse("a/b:0.1:0.2:0.01"), Candidate("a/b", Prices(0.1, 0.2, 0.01)))

    def test_three_fields(self):
        self.assertEqual(Candidate.parse("a/b:0.1:0.2"), Candidate("a/b", Prices(0.1, 0.2)))

    def test_empty_cache_field(self):
        self.assertEqual(Candidate.parse("a/b:0.1:0.2:"), Candidate("a/b", Prices(0.1, 0.2)))

    def test_model_with_a_colon(self):
        self.assertEqual(Candidate.parse("a/b:free:0:0"), Candidate("a/b:free", Prices(0.0, 0.0)))
        self.assertEqual(Candidate.parse("a/b:nitro:1:2:0.5"), Candidate("a/b:nitro", Prices(1.0, 2.0, 0.5)))

    def test_rejects_missing_prices(self):
        with self.assertRaises(ValueError):
            Candidate.parse("a/b")


class RowTest(unittest.TestCase):
    def test_sixteen_cells_with_unclassified_and_controls_in_notes(self):
        result = aggregate(repetitions(), Prices(0.15, 0.5), CONTROLS, MODEL_PATTERNS, ENVIRONMENT_PATTERNS)
        cells = row_cells(result, run_date="d", model=MODEL, other_variables="o", commit="c", catalog_date="k", notes="", language="en")
        self.assertEqual(len(cells), 16)
        self.assertEqual(cells[5], "70.4%")
        self.assertIn("test_protect_bonsai", cells[15])
        self.assertIn("controls failed: test_pre_work_analysis", cells[15])


if __name__ == "__main__":
    unittest.main()
