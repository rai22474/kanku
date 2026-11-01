"""`kanku report` end to end: a real run directory into the dataset's row."""

import io
import unittest
from contextlib import redirect_stdout

from fixture import Project
from kanku_core.cli import main


class ReportCommandTest(unittest.TestCase):
    def setUp(self):
        self.project = Project()

    def tearDown(self):
        self.project.close()

    def test_row_and_breakdown_written(self):
        run = self.project.copy_run()
        with redirect_stdout(io.StringIO()):
            code = main([
                "--project", str(self.project.root), "report", "--service", "app", "--variable", "APP_MODEL",
                "--dataset", str(self.project.dataset), "--run-dir", str(run), "--candidate", "z-ai/glm-5.3-flash:0.15:0.5:0.03",
                "--catalog-date", "2026-09-11", "--other-variables", "VISION_MODEL=v/one", "--commit", "95d96a2", "--run-date", "2026-09-11 19:20 UTC",
            ])
        self.assertEqual(code, 0)
        text = self.project.dataset.read_text()
        self.assertIn("| 2026-09-11 19:20 UTC | `z-ai/glm-5.3-flash` | VISION_MODEL=v/one | 95d96a2 | 2026-09-11 | 70.4% | 50.0% | 25.0% | 8.97s | 4.50s | 20.17s | 32.38s | 0.44s | 79.37s |", text)
        self.assertIn("controles fallidos: test_pre_work_analysis", text)
        breakdown = (run / "scenario_breakdown.md").read_text()
        self.assertIn("# Desglose por escenario", breakdown)
        self.assertIn("| test_care_guide_generated_as_wiki_page | 27 | 14.55s |", breakdown)

    def test_trust_shows_what_it_approves(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["--project", str(self.project.root), "trust"]), 0)
            self.assertEqual(main(["--project", str(self.project.root), "trust", "--approve"]), 0)
            self.assertEqual(main(["--project", str(self.project.root), "trust"]), 0)
        shown = out.getvalue()
        self.assertIn("test: uv run pytest tests/acceptance", shown)
        self.assertIn("must resolve empty: BOT_TOKEN, ADMIN_CHAT_ID", shown)
        self.assertIn("no acceptance: decided from the catalog", shown)
        self.assertIn("NOT approved", shown)
        self.assertTrue(shown.rstrip().endswith("kanku: approved"))


if __name__ == "__main__":
    unittest.main()
