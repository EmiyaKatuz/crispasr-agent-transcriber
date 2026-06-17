# crispasr-agent-transcriber

Local transcription helpers for Codex and other AI agents using CrispASR.

The v0.1 path is intentionally small:

- English audio is routed to CrispASR `cohere` (Cohere Transcribe 03-2026).
- Chinese audio is routed to CrispASR `qwen3-1.7b` (Qwen3-ASR 1.7B).
- `--profile auto` locally probes the media language first, then uses one selected backend.
- Audio and video files stay on the local machine.
- Video and unsupported audio are converted with ffmpeg to a temporary mono 16 kHz WAV before upload.

## Quick start

```powershell
# Clone and install dependencies
git clone https://github.com/EmiyaKatuz/crispasr-agent-transcriber.git
cd crispasr-agent-transcriber
uv sync --extra dev

# Install CrispASR binary (one time)
uv run python scripts/transcribe.py --install-crispasr

# Check installed version and update availability
uv run python scripts/transcribe.py --crispasr-status

# Update to the latest release
uv run python scripts/transcribe.py --update-crispasr
```

Or use the convenience script:

```powershell
.\scripts\setup.ps1
```

## CrispASR binary management

The tool automatically detects, installs, and updates the CrispASR binary.

| Command | What it does |
|---|---|
| `--install-crispasr` | Downloads the latest CrispASR release for your platform and extracts it to `bin/`. |
| `--update-crispasr` | Checks for a newer release and upgrades if one is available. |
| `--crispasr-status` | Shows the installed version and whether an update is available. |
| `--crispasr-bin-dir` | Custom directory for the CrispASR binary (default: `./bin`). |
| `--crispasr-bin` | Explicit path to `crispasr.exe` (overrides auto-detection). |

When `--manage-server` is set and no binary is found, the tool auto-installs CrispASR before starting the server.

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