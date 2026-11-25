# HackerOne MCP server

A stdio MCP server that exposes read-only HackerOne research and account data to Hermes Agent. It uses only the Python standard library and reuses the HackerOne GraphQL client shape from `skills/offensive-osint/scripts/h1_reference.py`.

## Tools

| Tool | Credentials | What it returns |
| --- | :---: | --- |
| `search_disclosed_reports` | No | Disclosed Hacktivity reports for duplicate checks and technique research. |
| `get_program` | No | A public program's bounty range, resolved-report count, launch date, and state. |
| `get_program_scope` | No | Public program scope and policy details. |
| `list_my_programs` | Yes | Programs visible to your HackerOne account, including private invitations. |
| `get_my_program` | Yes | One program's policy and full account-visible scope. |
| `list_my_reports` | Yes | Your own reports and their state. |

The account-specific tools appear only when `HACKERONE_API_USERNAME` and `HACKERONE_API_TOKEN` are present in the server process environment. Create a read-only API token in HackerOne under **Settings → API Token**. Nothing in this server submits or changes reports.

## Optional Hermes connection

This MCP server is optional. Copying the `skills/` directory is sufficient to use the bug-hunting skills; no MCP connection is needed for that.

To expose the public HackerOne tools to Hermes, add a local stdio server (replace the example path with the absolute path on your machine):

```bash
hermes mcp add hackerone --command python3 --args /absolute/path/to/DeepSeek-BugHunter/mcp/hackerone/server.py
```

For account-specific tools, set `HACKERONE_API_USERNAME` and `HACKERONE_API_TOKEN` in the environment available to Hermes, then restart the session. Alternatively, configure the server in `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  hackerone:
    command: "python3"
    args: ["/absolute/path/to/DeepSeek-BugHunter/mcp/hackerone/server.py"]
    env:
      HACKERONE_API_USERNAME: "<your username>"
      HACKERONE_API_TOKEN: "<your read-only token>"
```

On Windows, use the full path to `python.exe` if `python3` resolves to the Microsoft Store stub. Review the MCP server's permissions and tool list before using it.

## Search syntax

`query` is passed to HackerOne's search (for example, `oauth AND redirect_uri`). `program` adds `team_handle:<handle>` as a server-side filter. `sort` can be `relevance` (default), `votes`, or `bounty`. Results are capped at 50 per call.

Hermes MCP reference: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/mcp.md
