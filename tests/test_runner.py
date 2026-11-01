"""The runner's flow without docker: swap, repetitions, row — with the repetition itself stubbed."""

import io
import shutil
import unittest
from contextlib import redirect_stderr
from unittest import mock

from fixture import FIXTURES, Project
from kanku_core import runner
from kanku_core.config import load_config
from kanku_core.dataset import scenarios
from kanku_core.envfile import model_value
from kanku_core.report import Candidate


class BenchmarkFlowTest(unittest.TestCase):
    def setUp(self):
        self.project = Project()
        self.config = load_config(self.project.root)
        self.seen = []

    def tearDown(self):
        self.project.close()

    def fake_repetition(self, config, service, scenario_list, out):
        self.seen.append(model_value(config.env_file, "APP_MODEL"))
        shutil.copytree(FIXTURES / "run_glm" / out.name, out)

    def test_candidate_set_during_repetitions_restored_after_and_row_written(self):
        env_before = self.project.root.joinpath(".env").read_text()
        with mock.patch.object(runner, "repetition", self.fake_repetition), redirect_stderr(io.StringIO()):
            rows = runner.benchmark(
                self.config, self.config.service("app"), "APP_MODEL", self.project.dataset,
                scenarios(self.project.dataset, "es"), [Candidate.parse("z-ai/glm-5.3-flash:0.15:0.5")],
                "VISION_MODEL=v/one", "2026-09-11", 3,
            )
        self.assertEqual(self.seen, ["z-ai/glm-5.3-flash"] * 3)
        self.assertEqual(self.project.root.joinpath(".env").read_text(), env_before)
        self.assertEqual(rows[0][5], "70.4%")
        self.assertIn("`z-ai/glm-5.3-flash`", self.project.dataset.read_text())

    def test_env_restored_when_a_repetition_fails(self):
        env_before = self.project.root.joinpath(".env").read_text()

        def failing(*_):
            raise RuntimeError("compose up failed")

        with mock.patch.object(runner, "repetition", failing), redirect_stderr(io.StringIO()), self.assertRaises(RuntimeError):
            runner.benchmark(
                self.config, self.config.service("app"), "APP_MODEL", self.project.dataset,
                scenarios(self.project.dataset, "es"), [Candidate.parse("a/b:1:1")], "—", "2026-09-11", 3,
            )
        self.assertEqual(self.project.root.joinpath(".env").read_text(), env_before)


if __name__ == "__main__":
    unittest.main()
