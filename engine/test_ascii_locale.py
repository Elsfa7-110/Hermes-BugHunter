"""Regression test: engine output must survive a restrictive ASCII locale.

Force a C locale with Python UTF-8 coercion disabled so Unicode output cannot
implicitly rely on the terminal encoding.
"""
import os
import subprocess
import sys
import tempfile
import unittest

_ENGINE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_ENGINE)
_ASCII_ENV = dict(os.environ, PYTHONUTF8="0", PYTHONCOERCECLOCALE="0", LC_ALL="C")


class AsciiLocaleTests(unittest.TestCase):
    def test_mock_hunt_run_survives_ascii_locale(self):
        """Full --mock --hunt flow must finish without a UnicodeEncodeError."""
        with tempfile.TemporaryDirectory() as base:
            r = subprocess.run(
                [sys.executable, "engine/engine.py",
                 "--scope", "engine/engagement.example.json",
                 "--base", base, "--mock", "--hunt"],
                cwd=_REPO, env=_ASCII_ENV, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0,
                             f"engine crashed under ASCII locale:\n{r.stderr}")
            self.assertNotIn("UnicodeEncodeError", r.stderr)


if __name__ == "__main__":
    unittest.main()
