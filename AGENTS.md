# Project Instructions

This repository builds local-only transcription helpers for Codex and MCP agents.

- Do not upload media to cloud transcription services.
- Prefer the CrispASR HTTP server and `/v1/audio/transcriptions`.
- Do not automate the CrisperWeaver GUI as the main path.
- Keep file access narrow: accept local files only, validate paths, and reject URLs.
- Use ffmpeg with argument lists and `shell=False`.
- Do not commit model files, audio/video files, transcripts, generated outputs, or temp WAVs.
- Do not trigger model downloads during verification. If a local model is missing, stop and tell the user what to download.
- Before reporting back, run the available tests and explain the outcome in plain language.

## Plugin structure

This repository is also a Codex plugin. The plugin manifest is at
`.codex-plugin/plugin.json`, and the MCP server config is at `.mcp.json`.

- Skills live in `skills/crispasr-transcription/`.
- The MCP server lives in `mcp_server/crispasr_mcp/`.
- Plugin assets (icons, README) live in `assets/`.
- Installation instructions are in `docs/plugin_install.md`.

When modifying the plugin manifest or MCP config, keep paths relative to the
repository root so the plugin works when cloned to any location.

## npm installer

The `npm/` directory contains the public `npx` installer.

- Keep its version synchronized with `pyproject.toml`, `plugin.json`, and
  `server.json`.
- Never add model downloads to the installer.
- Verify GitHub Release SHA-256 checksums before extracting plugin files.
- Preserve `models/`, `bin/`, and `outputs/` during updates and normal removal.
- Run `npm test` and `npm pack --dry-run` from the `npm/` directory after
  changes.
