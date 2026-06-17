# crispasr-agent-transcriber

Local transcription helpers for Codex and other AI agents using CrispASR.

The v0.1 path is intentionally small:

- English audio is routed to CrispASR `cohere`.
- Chinese audio is routed to CrispASR `qwen3-1.7b`.
- `--profile auto` locally probes the media language first, then uses one selected backend.
- Audio and video files stay on the local machine.
- Video and unsupported audio are converted with ffmpeg to a temporary mono 16 kHz WAV before upload.

## Install

```powershell
uv sync --extra dev
```

Install CrispASR separately and put `crispasr` on PATH, or pass `--crispasr-bin`.

## Model rule

This tool does not download models by default. For managed server mode, pass a local GGUF path:

```powershell
uv run python scripts/transcribe.py .\sample.wav --profile english --manage-server --model C:\models\cohere-transcribe-q4_k.gguf
```

If you deliberately want CrispASR to resolve `-m auto`, add:

```powershell
--allow-model-auto-download
```

The same rule applies to `--profile auto`: pass a local audio language detection model:

```powershell
--lid-model C:\models\crispasr\silero-lid-95-f16.gguf
```

## Manual server mode

Start exactly one CrispASR server for the content you are processing:

```powershell
crispasr --server --backend cohere -m C:\models\cohere-transcribe-q4_k.gguf --port 8080
crispasr --server --backend qwen3-1.7b -m C:\models\qwen3-asr-1.7b-q4_k.gguf --port 8080
```

Then transcribe:

```powershell
uv run python scripts/transcribe.py .\sample.mp4 --profile auto --lid-model C:\models\crispasr\silero-lid-95-f16.gguf --server-url http://127.0.0.1:8080 --format verbose_json --out-dir .\outputs
```

If the running server backend does not match the detected language, the tool stops and prints the command to run.

## Managed server mode

The tool can start one CrispASR server after language detection:

```powershell
uv run python scripts/transcribe.py .\sample.wav --profile chinese --manage-server --model C:\models\qwen3-asr-1.7b-q4_k.gguf --format srt
```

Use `--keep-server` if you want the started server to remain running.

## MCP

Install the optional MCP dependency:

```powershell
uv sync --extra mcp
```

Run the server:

```powershell
uv run python -m crispasr_mcp.server
```

The MCP tools are:

- `crispasr_health`
- `crispasr_backends`
- `crispasr_detect_language`
- `transcribe_audio`
- `transcribe_video`
- `transcribe_folder`

## Verify

```powershell
uv run pytest
uv run ruff check .
```
