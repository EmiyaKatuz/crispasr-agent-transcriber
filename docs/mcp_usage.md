# MCP Usage

Install the optional MCP dependencies:

```powershell
uv sync --extra mcp
```

Run:

```powershell
uv run --extra mcp crispasr-agent-mcp
```

Example Codex MCP config:

```toml
[mcp_servers.crispasr-agent-transcriber]
command = "uv"
args = ["run", "--extra", "mcp", "crispasr-agent-mcp"]
cwd = "C:\\path\\to\\crispasr-agent-transcriber"
```

For clients other than Codex, see [AI agent integrations](agent_integrations.md).

Model downloads are not started by default. Pass local model paths to managed-server calls.
For `profile=auto`, also pass a local `lid_model` path.
