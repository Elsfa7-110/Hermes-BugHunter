# Engagement engine

The optional engagement engine is a deterministic, scope-aware workflow runner. It maps a target's surface, ranks candidate endpoints, and can dispatch opt-in hunt and validation tasks through the Hermes CLI.

## Design

1. **Scope first:** all candidate hosts are checked against an allowlist; deny rules win.
2. **Map first:** the default flow performs recon, ranking, and an attack-surface map without calling a model.
3. **Active testing is opt-in:** use `--hunt` to allow the engine to call Hermes for the selected in-scope candidates.
4. **Read-only by default:** state-changing actions remain disabled unless `--allow-intrusive` is explicitly supplied.
5. **Resumable state:** each engagement stores its progress and evidence separately.

## Run

Dry-run the complete workflow without live agent calls:

```bash
python3 engine/engine.py --scope engine/engagement.example.json --base /tmp/bughunter --mock --hunt
```

Map-only run:

```bash
python3 engine/engine.py --scope my-engagement.json
```

Opt-in active testing:

```bash
python3 engine/engine.py --scope my-engagement.json --hunt --parallel 3 --max-hunts 12
```

The default phases are `recon,rank,map`. Optional phases are `hunt,validate,report`. The default engagement data directory is `~/.hermes/bughunter/engagements/`; override it with `--base`.

## Hermes adapter

`engine/agent.py` calls the installed `hermes` CLI in quiet, plain-text one-shot mode. This allows Hermes to use the model, provider, and credentials already selected in the active profile. The engine does not expose a model override and never writes model settings or API credentials. Plain-text mode does not guarantee token-usage metadata, so cost is not fabricated when Hermes does not report it.

Burp or other MCP tools are available to the engine only when they are already configured in the active Hermes profile. No MCP configuration is written by the engine.

The adapter's `--ignore-rules` option is used only by evaluation baselines to suppress injected rule/skill context. It does not change the Hermes profile on disk.

## Key files

| File | Purpose |
|---|---|
| `scope.py` | deterministic allowlist, wildcard, CIDR, and deny-wins checks |
| `recon.py` | service fingerprinting, endpoint extraction, parameter discovery, and secret scanning |
| `skill_map.py` | maps endpoints and vulnerability classes to installed skills |
| `state.py` | resumable engagement state and run artifacts |
| `agent.py` | one-shot Hermes CLI adapter |
| `engine.py` | recon, rank, map, hunt, validate, and report orchestration |
| `memory.py` | optional engagement memory under `~/.hermes/bughunter/` |
| `attack_metrics.py` | optional target-independent counters under `~/.hermes/bughunter/` |

## Safety

The engine enforces scope at each dispatch boundary. It does not treat third-party services as in-scope merely because a target integrates with them. The default mode avoids destructive requests and does not exercise exposed credentials. Review the scope file and rules of engagement before enabling active testing.
