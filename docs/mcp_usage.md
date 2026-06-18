# MCP Usage

Install the optional MCP dependencies:

```powershell
uv sync --extra mcp
```

Run:

```powershell
uv run --extra mcp python -m crispasr_mcp.server
```

Example Codex MCP config:

```toml
[mcp_servers.crispasr-agent-transcriber]
command = "uv"
args = ["run", "--extra", "mcp", "python", "-m", "crispasr_mcp.server"]
cwd = "C:\\path\\to\\crispasr-agent-transcriber"
```

Model downloads are not started by default. Pass local model paths to managed-server calls.
For `profile=auto`, also pass a local `lid_model` path.
