import subprocess
import unittest
from unittest.mock import patch

import agent


class AgentResultTests(unittest.TestCase):
    def run_result(self, returncode, text="Completed", stderr=""):
        completed = subprocess.CompletedProcess(
            args=["hermes", "chat"], returncode=returncode,
            stdout=text, stderr=stderr,
        )
        with patch.object(agent.subprocess, "run", return_value=completed):
            return agent.run_agent("Synthetic task")

    def test_nonzero_exit_is_an_error_and_keeps_partial_output(self):
        result = self.run_result(1, text="Partial output")
        self.assertEqual(result["error"], "exit:1")
        self.assertEqual(result["result"], "Partial output")

    def test_preserves_successful_plain_text_response(self):
        result = self.run_result(0, text="Completed")
        self.assertIsNone(result["error"])
        self.assertEqual(result["result"], "Completed")
        self.assertEqual(result["usage"], {})

    def test_provider_rate_limit_is_classified(self):
        result = self.run_result(1, text="Provider rate limit reached")
        self.assertEqual(result["error"], "rate-limited")

    def test_ignore_rules_is_opt_in(self):
        completed = subprocess.CompletedProcess(["hermes"], 0, stdout="ok", stderr="")
        with patch.object(agent.subprocess, "run", return_value=completed) as run:
            agent.run_agent("Synthetic task", ignore_rules=True)
        self.assertIn("--ignore-rules", run.call_args.args[0])

    def test_model_is_not_forced_by_default(self):
        completed = subprocess.CompletedProcess(["hermes"], 0, stdout="ok", stderr="")
        with patch.object(agent.subprocess, "run", return_value=completed) as run:
            agent.run_agent("Synthetic task")
        self.assertNotIn("--model", run.call_args.args[0])

    def test_quiet_one_shot_inherits_hermes_profile(self):
        completed = subprocess.CompletedProcess(["hermes"], 0, stdout="ok", stderr="")
        with patch.object(agent.subprocess, "run", return_value=completed) as run:
            agent.run_agent("Synthetic task")
        command = run.call_args.args[0]
        self.assertIn("--oneshot", command)
        self.assertIn("--quiet", command)
        self.assertNotIn("--format", command)
        self.assertIn("--query-file", command)
        self.assertEqual(run.call_args.kwargs.get("input"), "Synthetic task")
