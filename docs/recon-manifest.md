# Recon-to-Hunt Manifest

`manifest.json` is the data contract between passive reconnaissance and the authorized testing workflow. The `offensive-osint` skill and `cbh recon` can produce discovery data; `cbh surface`, `/hunt`, and `/surface` can consume it so findings do not need to be retyped.

The manifest is written to `recon/<target>/manifest.json`.

JSON Schema: [`recon-manifest.schema.json`](recon-manifest.schema.json).

## Producers

| Producer | Fields |
|---|---|
| `cbh recon <target>` | `target`, `generated_at`, `counts`, `assets`, `ranked_surface` |
| `offensive-osint` skill — `secret_scan.py` | `secrets[]` |
| `offensive-osint` skill — identity-fabric probes | `identity_fabric{}` |

A producer that does not discover a section leaves it empty (`[]` / `{}`), never absent.

## Consumers

| Consumer | Use |
|---|---|
| `cbh surface <target>` | Prints ranked P1 / P2 / Kill surface from `ranked_surface` |
| `hunt <target> [manifest.json]` | Seeds `scope.md` (live hosts) and `notes.md` (ranked surface) |
| `/hunt`, `/surface` | Uses the same data in a Hermes session |

`hunt` resolves the manifest from: second argument → `$HUNT_MANIFEST` → `./recon/<target>/manifest.json`.

## Schema (v1.0)

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | `"1.0"` |
| `target` | string | Root domain |
| `generated_at` | string | UTC ISO-8601 |
| `producers` | string[] | Tool and version identifiers |
| `counts` | object | `{subdomains, resolved, live}` |
| `assets` | object[] | `{host, ips[], url, status, server, title, tech[], source}` (`url` / `status` may be null for DNS-only assets) |
| `ranked_surface` | object[] | `{url, host, bug_classes[], priority, rationale}`; priority is `P1`, `P2`, or `KILL` |
| `secrets` | object[] | `{pattern, severity, category, source}` |
| `identity_fabric` | object | Identity-provider and tenant metadata discovered by the relevant probes |

## Example

```json
{
  "schema_version": "1.0",
  "target": "acme.com",
  "generated_at": "2026-06-25T12:00:00+00:00",
  "producers": ["cbh-recon/2.1.0"],
  "counts": {"subdomains": 47, "resolved": 31, "live": 12},
  "assets": [
    {"host": "api.acme.com", "ips": ["192.0.2.10"], "url": "https://api.acme.com", "status": 200, "server": "nginx", "title": "API", "tech": [], "source": "crtsh+httpx"}
  ],
  "ranked_surface": [
    {"url": "https://api.acme.com", "host": "api.acme.com", "bug_classes": ["hunt-api-misconfig", "hunt-idor"], "priority": "P1", "rationale": "high-value API surface"}
  ],
  "secrets": [],
  "identity_fabric": {}
}
```

## Round trip

```bash
cbh recon acme.com
cbh surface acme.com
hunt acme.com recon/acme.com/manifest.json
```
