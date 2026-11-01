import unittest

from fixture import Project
from kanku_core.dataset import DatasetError, append_row, check_results_table, scenarios, selection


class ScenariosTest(unittest.TestCase):
    def setUp(self):
        self.project = Project()

    def tearDown(self):
        self.project.close()

    def test_scenarios_and_controls_from_the_table(self):
        found = scenarios(self.project.dataset, "es")
        self.assertEqual(len(found), 9)
        self.assertEqual([s.name for s in found if s.control], ["test_pre_work_analysis"])
        self.assertTrue(selection(found).startswith("test_create_bonsai or test_propose_and_confirm_fertilization_plan"))

    def test_a_scenario_must_be_a_node_id(self):
        self.project.dataset.write_text(self.project.dataset.read_text().replace("`manage_bonsai/create_bonsai_via_advice.py::test_create_bonsai`", "create a bonsai"))
        with self.assertRaises(DatasetError):
            scenarios(self.project.dataset, "es")


class AppendTest(unittest.TestCase):
    def setUp(self):
        self.project = Project()

    def tearDown(self):
        self.project.close()

    def row(self, marker):
        return [marker] + ["x"] * 15

    def test_replaces_the_placeholder_in_the_variables_section(self):
        append_row(self.project.dataset, "APP_MODEL", "es", self.row("first"))
        text = self.project.dataset.read_text()
        self.assertNotIn("| — | — | — |", text)
        self.assertLess(text.index("| first |"), text.index("## Resultados — `REASONING_MODEL`"))

    def test_appends_after_the_last_row(self):
        append_row(self.project.dataset, "REASONING_MODEL", "es", self.row("second"))
        text = self.project.dataset.read_text()
        self.assertLess(text.index("| 2026-09-01 |"), text.index("| second |"))
        self.assertLess(text.index("| second |"), text.index("## Histórico"))

    def test_unknown_variable(self):
        with self.assertRaises(DatasetError):
            append_row(self.project.dataset, "VISION_MODEL", "es", self.row("x"))

    def test_variable_name_is_matched_whole(self):
        with self.assertRaises(DatasetError):
            check_results_table(self.project.dataset, "MODEL", "es")

    def test_table_not_in_kanku_format(self):
        self.project.dataset.write_text(self.project.dataset.read_text().replace("| Catálogo leído ", ""))
        with self.assertRaises(DatasetError):
            check_results_table(self.project.dataset, "APP_MODEL", "es")


if __name__ == "__main__":
    unittest.main()
