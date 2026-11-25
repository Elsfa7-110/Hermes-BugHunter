#!/usr/bin/env python3
"""Invoke Hermes Agent without changing the user's active profile.

The adapter uses the model, provider, credentials, tools, and MCP servers already
configured in Hermes. It never reads or writes provider secrets or profile config.
"""
import json
import re
import subprocess
import time


def run_agent(task, skills_on=False, max_turns=40, timeout=600, ignore_rules=False):
    """Run a one-shot Hermes turn and return normalized engine output.

    Hermes always resolves the model, provider, and credentials from the active profile.
    ``skills_on`` remains accepted for compatibility with evaluation callers; the
    standard run relies on Hermes skill discovery. ``ignore_rules`` is used only
    for a skills-off baseline and is an invocation flag, not a profile mutation.
    """
    cmd = [
        "hermes", "chat", "--oneshot", "--quiet", "--query-file", "-",
        "--max-turns", str(max_turns),
    ]
    if ignore_rules:
        cmd.append("--ignore-rules")

    started = time.time()
    try:
        proc = subprocess.run(
            cmd, input=str(task), capture_output=True, text=True,
            timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return {"result": "", "error": "timeout", "duration_s": round(time.time() - started, 1)}
    except (FileNotFoundError, OSError) as exc:
        return {"result": "", "error": f"exec:{exc}", "duration_s": round(time.time() - started, 1)}

    result = (proc.stdout or "").strip()
    combined = (result + "\n" + (proc.stderr or "")).lower()
    if any(token in combined for token in ("usage limit", "rate limit", "quota exceeded", "provider limit")):
        error = "rate-limited"
    elif proc.returncode:
        error = f"exit:{proc.returncode}"
    else:
        error = None

    return {
        "result": result,
        "error": error,
        "usage": {},  # Plain-text one-shot mode preserves profile inheritance; token usage is not guaranteed.
        "num_turns": None,
        "duration_s": round(time.time() - started, 1),
    }


def extract_json(text):
    """Extract the last valid JSON object or array from a model response."""
    if not text:
        return None
    blocks = re.findall(r"```(?:json\s*|\s*)(.*?)```", text, re.S)
    for block in reversed(blocks):
        try:
            value = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(value, (dict, list)):
            return value
    decoder = json.JSONDecoder()
    last = None
    index = 0
    while index < len(text):
        if text[index] in "[{":
            try:
                value, end = decoder.raw_decode(text, index)
            except (ValueError, RecursionError):
                break
            if isinstance(value, (dict, list)):
                last = value
            index = end
        else:
            index += 1
    return last


if __name__ == "__main__":
    completed = subprocess.CompletedProcess(["hermes", "chat"], 0, stdout="completed\n", stderr="")
    original = subprocess.run
    try:
        subprocess.run = lambda *a, **kw: completed
        assert run_agent("Synthetic task")["result"] == "completed"
    finally:
        subprocess.run = original
    print("Hermes agent adapter self-test: PASS")
