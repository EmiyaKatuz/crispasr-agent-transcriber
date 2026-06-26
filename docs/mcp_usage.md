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

Model downloads are not started by install/update or by transcription tools.
Agents can explicitly call:

| Tool | Purpose |
|---|---|
| `crispasr_list_models` | Show approved GGUF choices and installed files in `models_dir` |
| `crispasr_download_models` | Download the recommended bundle or selected `model_ids` |
| `crispasr_resolve_model_paths` | Return `english_model`, `chinese_model`, and `lid_model` paths |
| `crispasr_detect_language` | Run FireRed LID on a local media file |
| `transcribe_audio` | Transcribe local audio |
| `transcribe_video` | Transcribe local video audio |
| `understand_video` | Transcribe video, capture synchronized keyframes, persist a manifest, and return an agent context |
| `transcribe_folder` | Batch-transcribe supported media files in one folder |

Recommended agent flow:

1. Call `crispasr_list_models`.
2. If recommended files are missing and the user approves downloads, call
   `crispasr_download_models`.
3. For normal audio/video transcription, call `transcribe_audio` or
   `transcribe_video` with `manage_server=true` and `models_dir`.
4. For video understanding, call `understand_video`. It writes:
   - `<stem>.video_understanding.json` with the full transcript, segments, and
     keyframe metadata;
   - `<stem>.agent_context.json` with a compact payload for the calling agent;
   - `<stem>.keyframes/*.jpg` synchronized to transcript segment times.

For `profile=auto`, `models_dir` is enough once the recommended LID model is
installed. Explicit `english_model`, `chinese_model`, and `lid_model` arguments
still override the defaults.
