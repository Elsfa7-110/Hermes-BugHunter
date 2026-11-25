"""Regression test: cbh output must survive a restrictive ASCII locale.

The CLI emits status glyphs and arrows. Force a C locale with Python UTF-8
coercion disabled to catch accidental reliance on a Unicode terminal encoding.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ASCII_ENV = dict(os.environ, PYTHONUTF8="0", PYTHONCOERCECLOCALE="0", LC_ALL="C")


class CbhAsciiLocaleTests(unittest.TestCase):
    def test_triage_survives_ascii_locale(self):
        with tempfile.TemporaryDirectory() as tmp:
            finding = Path(tmp) / "finding.md"
            finding.write_text("# clickjacking on logout page\n", encoding="utf-8")
            r = subprocess.run(
                [sys.executable, "cbh/cli.py", "triage", str(finding)],
                cwd=_REPO, env=_ASCII_ENV, capture_output=True, text=True, encoding="utf-8")
            self.assertNotIn("UnicodeEncodeError", r.stderr,
                             f"cbh crashed under ASCII locale:\n{r.stderr}")


if __name__ == "__main__":
    unittest.main()
