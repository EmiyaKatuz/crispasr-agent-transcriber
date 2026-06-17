# MCP Usage

Install the optional MCP dependencies:

```powershell
uv sync --extra mcp
```

Run:

```powershell
uv run python -m crispasr_mcp.server
```

Example Codex MCP config:

```toml
[mcp_servers.crispasr-agent-transcriber]
command = "uv"
args = ["run", "python", "-m", "crispasr_mcp.server"]
cwd = "C:\\Users\\Katuz\\Documents\\CrispASR transcription"
```

Model downloads are not started by default. Pass local model paths to managed-server calls.
For `profile=auto`, also pass a local `lid_model` path.
