"""Smoke tests for the optional, non-mutating Hermes MCP snippet helper."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "setup_harness_mcp.py"


class HermesMCPConfigTests(unittest.TestCase):
    def test_prints_hermes_yaml_without_modifying_home(self):
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ, "HOME": home, "USERPROFILE": home}
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--name", "burp", "--command", "java",
                 "--arg=-jar", "--arg", "/opt/burp/mcp.jar"],
                capture_output=True, text=True, env=env, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("mcp_servers:", result.stdout)
            self.assertIn("  burp:", result.stdout)
            self.assertIn('command: "java"', result.stdout)
            self.assertIn('args: ["-jar", "/opt/burp/mcp.jar"]', result.stdout)
            self.assertIn("No file was read or modified", result.stdout)
            self.assertEqual(list(Path(home).iterdir()), [])

    def test_missing_command_is_rejected(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--command", result.stderr)


if __name__ == "__main__":
    unittest.main()
