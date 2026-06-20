# AI Agent Integrations

The portable integration surface is the MCP server. The Codex plugin bundles
that server together with a Codex Skill, while other agents can launch the
same server directly over MCP stdio.

## Requirements

- Python 3.11 or newer
- `uv` / `uvx`
- ffmpeg available in `PATH`
- Local CrispASR models

Media is processed locally. Model files are never included in the plugin or
uploaded to a remote service.

## Portable MCP command

Use the tagged GitHub release as the package source:

```powershell
uvx --from "crispasr-agent-transcriber[mcp] @ git+https://github.com/EmiyaKatuz/crispasr-agent-transcriber.git@v0.3.4" crispasr-agent-mcp
```

The process uses MCP stdio and stays running while the client is connected.

## Generic MCP configuration

Most MCP clients accept a server name plus `command`, `args`, and optional
environment variables:

```json
{
  "mcpServers": {
    "crispasr-agent-transcriber": {
      "command": "uvx",
      "args": [
        "--from",
        "crispasr-agent-transcriber[mcp] @ git+https://github.com/EmiyaKatuz/crispasr-agent-transcriber.git@v0.3.4",
        "crispasr-agent-mcp"
      ]
    }
  }
}
```

Clients that use a different outer key can reuse the same `command` and
`args` values.

## Codex CLI

```powershell
codex mcp add crispasr-agent-transcriber -- uvx --from "crispasr-agent-transcriber[mcp] @ git+https://github.com/EmiyaKatuz/crispasr-agent-transcriber.git@v0.3.4" crispasr-agent-mcp
```

The Codex plugin remains the preferred Codex installation because it also
provides the `crispasr-transcription` Skill and plugin UI metadata.

## Desktop agents

For Claude Desktop, Cursor, and other MCP-compatible desktop agents, add the
generic configuration to the client's MCP configuration file. Restart the
client after changing the configuration.

## Model paths

The MCP tools accept explicit local paths for:

- `model`: the selected transcription model
- `lid_model`: the FireRed language detection model used by `profile=auto`
- `crispasr_bin`: an explicit CrispASR executable when auto-discovery is not
  appropriate

Keep these files in a stable local directory. Do not place them inside a
temporary plugin cache because client updates may replace that cache.

## Compatibility contract

Other agents only need to support MCP stdio. They do not need to understand
Codex Skills or `.codex-plugin/plugin.json`. The six MCP tools and their
structured responses are the cross-agent API.
