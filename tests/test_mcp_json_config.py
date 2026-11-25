"""The MCP helper is intentionally print-only and must not mutate config files."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "setup_harness_mcp.py"


class MCPHelperSafetyTests(unittest.TestCase):
    def test_existing_config_files_remain_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config = home / ".hermes" / "config.yaml"
            config.parent.mkdir(parents=True)
            original = "model: existing-profile\nmcp_servers: {}\n"
            config.write_text(original, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--command", "fixture"],
                capture_output=True, text=True,
                env={**os.environ, "HOME": tmp, "USERPROFILE": tmp}, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(config.read_text(encoding="utf-8"), original)
            self.assertIn("mcp_servers:", result.stdout)
            self.assertIn("Model and credential settings are untouched", result.stdout)


if __name__ == "__main__":
    unittest.main()
