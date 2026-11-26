---
name: pickup
description: "Resume a hunt: history plus untested surface. Usage: /pickup target.com"
sources: ["commands/pickup.md"]
---

# /pickup

Pick up where you left off on a target.

> Use `/pickup` to load this bundle’s per-target engagement ledger.

## What This Does

1. Reads the target rollup from `~/.hermes/bughunter/memory/targets/<host>.json`.
2. Shows hunt history (sessions, last seen, tech stack).
3. Lists confirmed findings and the endpoints already tested.

## Usage

```
/pickup target.com
```

## Implementation

The agent reads the rollup directly:

```bash
python3 -c "import sys; sys.path.insert(0,'engine'); import memory, json; print(json.dumps(memory.rollup('target.com'), indent=2))"
```

## If No Previous Hunt

```
No ledger data for target.com. Run `/recon target.com` then `/autopilot target.com` first.
```

> **Note — cross-engagement recall is opt-in.** The target rollup `/pickup` reads
> is written only when the engine ran with `--use-memory`. A **default** engine run
> intentionally persists **nothing** target-identifying across engagements (no
> hostnames, URLs, or findings pooled), so `/pickup` will show no prior data for it.
> Re-run with `--use-memory` when you deliberately want persistent per-target recall.
