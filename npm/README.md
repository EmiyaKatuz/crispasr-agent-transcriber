# @emiyakatuz/crispasr-agent-transcriber

Cross-platform installer for the
[CrispASR Agent Transcriber](https://github.com/EmiyaKatuz/crispasr-agent-transcriber)
Codex plugin and MCP server.

```powershell
npx @emiyakatuz/crispasr-agent-transcriber@latest install
```

The installer downloads the matching GitHub Release, verifies its SHA-256
checksum, installs Python/MCP dependencies with `uv`, installs the best
available CrispASR binary (CUDA, then Vulkan, then CPU), and registers the
plugin in the Codex Personal marketplace.

Models are never downloaded automatically. The installer creates the plugin's
`models/` directory and prints the exact model filenames and official source
links before stopping.

## Commands

```powershell
npx @emiyakatuz/crispasr-agent-transcriber@latest install
npx @emiyakatuz/crispasr-agent-transcriber@latest update
npx @emiyakatuz/crispasr-agent-transcriber@latest doctor
npx @emiyakatuz/crispasr-agent-transcriber@latest --json doctor
npx @emiyakatuz/crispasr-agent-transcriber@latest uninstall
```

`uninstall` preserves local models, CrispASR binaries, and outputs. Add
`--purge-data` only when those files should also be removed.

## Prerequisites

- Node.js 20 or newer
- [uv](https://docs.astral.sh/uv/)
- [ffmpeg](https://ffmpeg.org/)

Media remains local. This installer downloads code and CrispASR binaries from
the project's documented GitHub sources, but never uploads media and never
downloads ASR models.
