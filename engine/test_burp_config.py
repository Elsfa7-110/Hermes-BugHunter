import subprocess
import unittest
from unittest.mock import patch

import agent


class HermesDispatchTests(unittest.TestCase):
    def test_uses_plain_text_oneshot_and_active_profile(self):
        completed = subprocess.CompletedProcess(["hermes"], 0, stdout="done", stderr="")
        with patch.object(agent.subprocess, "run", return_value=completed) as run:
            result = agent.run_agent("Synthetic task")
        command = run.call_args.args[0]
        self.assertEqual(command[0:2], ["hermes", "chat"])
        self.assertIn("--oneshot", command)
        self.assertIn("--quiet", command)
        self.assertNotIn("--model", command)
        self.assertEqual(result["result"], "done")
