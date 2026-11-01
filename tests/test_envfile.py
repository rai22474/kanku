import tempfile
import unittest
from pathlib import Path

from kanku_core.envfile import model_value, swapped

ENV = "A=1\nAPP_MODEL=old/model\nSECRET=s3cret\n"


class SwapTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / ".env"
        self.path.write_text(ENV)

    def tearDown(self):
        self.directory.cleanup()

    def test_swaps_and_restores(self):
        with swapped(self.path, "APP_MODEL", "new/model"):
            self.assertEqual(model_value(self.path, "APP_MODEL"), "new/model")
        self.assertEqual(self.path.read_text(), ENV)

    def test_restores_on_failure(self):
        with self.assertRaises(RuntimeError), swapped(self.path, "APP_MODEL", "new/model"):
            raise RuntimeError("boom")
        self.assertEqual(self.path.read_text(), ENV)

    def test_removes_a_line_that_was_not_there(self):
        with swapped(self.path, "NEW_MODEL", "x/y"):
            self.assertEqual(model_value(self.path, "NEW_MODEL"), "x/y")
        self.assertEqual(self.path.read_text(), ENV)

    def test_keeps_lines_others_changed_meanwhile(self):
        with swapped(self.path, "APP_MODEL", "new/model"):
            self.path.write_text(self.path.read_text() + "B=2\n")
        self.assertEqual(self.path.read_text(), ENV + "B=2\n")

    def test_value_quoted_or_commented(self):
        self.path.write_text('APP_MODEL="q/m"\nOTHER=v # note\nEMPTY=\n')
        self.assertEqual(model_value(self.path, "APP_MODEL"), "q/m")
        self.assertEqual(model_value(self.path, "OTHER"), "v")
        self.assertIsNone(model_value(self.path, "EMPTY"))
        self.assertIsNone(model_value(self.path, "MISSING"))


if __name__ == "__main__":
    unittest.main()
