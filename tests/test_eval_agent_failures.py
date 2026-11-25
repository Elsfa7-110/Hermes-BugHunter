"""Evaluation wrapper tests for the shared Hermes agent adapter."""
import unittest
from unittest.mock import patch

from eval import run_eval


class AgentFailureTests(unittest.TestCase):
    def test_successful_hermes_response_is_preserved_without_fabricated_cost(self):
        payload = {
            "result": "VERDICT: VULNERABLE",
            "error": None,
            "usage": {},
            "num_turns": None,
            "duration_s": 1.25,
        }
        with patch.object(run_eval.HERMES_AGENT, "run_agent", return_value=payload) as invoke:
            result = run_eval.run_agent("fixture", True, 10, 5)
        invoke.assert_called_once_with(
            "fixture", max_turns=10, timeout=5, ignore_rules=False
        )
        self.assertEqual(result["result"], "VERDICT: VULNERABLE")
        self.assertIsNone(result["agent_error"])
        self.assertFalse(result["is_error"])
        self.assertIsNone(result["cost_usd"])
        self.assertEqual(result["duration_s"], 1.25)

    def test_baseline_disables_injected_rules_only_for_that_invocation(self):
        payload = {"result": "", "error": None, "usage": {}}
        with patch.object(run_eval.HERMES_AGENT, "run_agent", return_value=payload) as invoke:
            run_eval.run_agent("fixture", False, 8, 4)
        self.assertTrue(invoke.call_args.kwargs["ignore_rules"])

    def test_hermes_launch_failure_is_reported_as_failed_row(self):
        payload = {
            "result": "", "error": "exec:Hermes CLI not found",
            "usage": {}, "num_turns": None, "duration_s": 0.01,
        }
        with patch.object(run_eval.HERMES_AGENT, "run_agent", return_value=payload):
            result = run_eval.run_agent("fixture", True, 1, 1)
        self.assertTrue(result["is_error"])
        self.assertEqual(result["agent_error"], "exec:Hermes CLI not found")
        self.assertEqual(result["result"], "")


if __name__ == "__main__":
    unittest.main()
