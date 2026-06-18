# crispasr-agent-transcriber

Local-only transcription for Codex and MCP-based AI agents, powered by
[CrispASR](https://github.com/CrispStrobe/CrispASR). No cloud uploads,
no API keys required for transcription.

## What it does

Give it a local audio or video file. It:

1. Probes the spoken language (English or Chinese) using CrispASR's FireRed LID.
2. Starts a local CrispASR server with the right backend -- Cohere Transcribe
   for English, Qwen3-ASR for Chinese.
3. Extracts audio from video with ffmpeg when needed.
4. Calls CrispASR's `/v1/audio/transcriptions` endpoint.
5. Writes the transcript and metadata to disk.

Everything runs on your machine. Media never leaves it.

## Quick start

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/),
[ffmpeg](https://ffmpeg.org/), and three model files (see below).

```powershell
git clone https://github.com/EmiyaKatuz/crispasr-agent-transcriber.git
cd crispasr-agent-transcriber

# Install Python dependencies
uv sync --extra dev

# Install the CrispASR binary (auto-detects GPU: CUDA > Vulkan > CPU)
uv run python scripts/transcribe.py --install-crispasr

# Transcribe a file
uv run python scripts/transcribe.py sample.mp4 --profile auto `
  --manage-server `
  --lid-backend firered --lid-model models\firered-lid-q2_k.gguf `
  --model models\cohere-transcribe.gguf `
  --format verbose_json
```

Or run `.\scripts\setup.ps1` for a guided first-time setup.

## Install as a Codex plugin

The plugin bundles the Codex Skill and the MCP server. Models remain local and
are not included in the plugin download.

Every tagged GitHub Release includes a
`crispasr-agent-transcriber-plugin-<version>.zip` bundle. Extract that archive
under `$HOME\plugins\crispasr-agent-transcriber`, or clone the repository there
directly as shown below.

Clone the repository into the standard personal plugin directory:

```powershell
$pluginRoot = Join-Path $HOME "plugins\crispasr-agent-transcriber"
git clone https://github.com/EmiyaKatuz/crispasr-agent-transcriber.git $pluginRoot
Set-Location $pluginRoot
uv sync --extra mcp
```

Add this entry to `%USERPROFILE%\.agents\plugins\marketplace.json`. If the
file already contains plugins, append the entry to its existing `plugins`
array instead of replacing the file:

```json
{
  "name": "crispasr-agent-transcriber",
  "source": {
    "source": "local",
    "path": "./plugins/crispasr-agent-transcriber"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Productivity"
}
```

Install it with a Codex build that supports plugin commands:

```powershell
codex plugin add crispasr-agent-transcriber@personal
```

If your Codex CLI does not expose `codex plugin`, open the Codex desktop
Plugins view and install **CrispASR Transcriber** from the Personal marketplace.
The first MCP launch automatically installs the Python MCP dependency through
`uv`; CrispASR models must still be downloaded manually into `models/`.

See [Plugin installation](docs/plugin_install.md) for the complete setup and
verification steps.

## Use with other AI agents

The MCP server is the cross-agent interface. Any agent that supports MCP stdio
can run the released package directly from GitHub:

```powershell
uvx --from "crispasr-agent-transcriber[mcp] @ git+https://github.com/EmiyaKatuz/crispasr-agent-transcriber.git@v0.3.1" crispasr-agent-mcp
```

Use the same command and arguments in Claude Desktop, Cursor, or another MCP
client. See [AI agent integrations](docs/agent_integrations.md) for a generic
MCP configuration and Codex CLI command.

## Required models

This tool does **not** download models automatically. Download these three
GGUF files and keep them in a local directory (the repo's `models/` folder
works well):

| Purpose | File | ~Size | Source |
|---|---|---|---|
| English ASR | `cohere-transcribe.gguf` | 3.9 GB | [Cohere on HuggingFace](https://huggingface.co/cstr) |
| Chinese ASR | `qwen3-asr-1.7b-q4_k.gguf` | 1.3 GB | [Qwen3-ASR GGUF](https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF) |
| Language detection | `firered-lid-q2_k.gguf` | 350 MB | [FireRed LID GGUF](https://huggingface.co/cstr/firered-lid-GGUF) |

Pass them on every run:

```powershell
--model models\cohere-transcribe.gguf
--lid-backend firered --lid-model models\firered-lid-q2_k.gguf
```

## CrispASR binary management

The tool auto-detects, installs, and updates the CrispASR binary from
[GitHub releases](https://github.com/CrispStrobe/CrispASR/releases).

| Flag | Effect |
|---|---|
| `--install-crispasr` | Download latest platform binary to `bin/` |
| `--update-crispasr` | Upgrade to newest release |
| `--crispasr-status` | Show installed version + update availability |
| `--crispasr-bin-dir PATH` | Custom directory (default `./bin`) |
| `--crispasr-bin PATH` | Exact path to `crispasr.exe` |

When `--manage-server` is set and no binary is found, it auto-installs before
starting the server.

### GPU detection

On install and update, the tool checks your hardware:

1. **CUDA** -- `nvidia-smi` available, or `CUDA_PATH` / `CUDA_HOME` set, or
   CUDA in `PATH` -> downloads `crispasr-*-cuda` variant.
2. **Vulkan** -- `vulkaninfo` or `VULKAN_SDK` set (only when CUDA is absent) ->
   downloads `crispasr-*-vulkan` variant.
3. **CPU** -- fallback when no GPU toolkit is detected.

macOS always uses the universal binary.

## Profiles

| Profile | Backend | ASR model | Language hint |
|---|---|---|---|
| `english` | `cohere` | Cohere Transcribe 03-2026 | `en` |
| `chinese` | `qwen3-1.7b` | Qwen3-ASR 1.7B | `zh` |
| `auto` | determined by LID | determined by LID | detected |

`auto` mode runs FireRed language detection on the media, then routes English
to Cohere or Chinese to Qwen3-1.7B. Mixed or uncertain content stops with a
clear error asking you to re-run with `--profile english` or `--profile chinese`.

## Usage

### Managed server (tool starts CrispASR for you)

```powershell
uv run python scripts/transcribe.py sample.wav `
  --profile auto `
  --manage-server `
  --model models\qwen3-asr-1.7b-q4_k.gguf `
  --lid-backend firered --lid-model models\firered-lid-q2_k.gguf `
  --format srt `
  --out-dir outputs
```

Add `--keep-server` to leave the server running after transcription.

### Manual server (you start CrispASR)

```powershell
# Terminal 1 -- start the server
crispasr --server --backend cohere `
  -m models\cohere-transcribe.gguf `
  --port 8080

# Terminal 2 -- transcribe
uv run python scripts/transcribe.py sample.mp4 `
  --profile english `
  --server-url http://127.0.0.1:8080 `
  --format verbose_json
```

If the running server's backend doesn't match the selected profile, the tool
prints the exact command you need to start the correct server.

### Output formats

| `--format` | File extension | Contents |
|---|---|---|
| `text` | `.txt` | Plain transcript |
| `verbose_json` | `.json` | Full response with segments |
| `srt` | `.srt` | SubRip subtitles |
| `vtt` | `.vtt` | WebVTT subtitles |

A `.metadata.json` sidecar is always written alongside the transcript.

### Video files

Video files are detected automatically. ffmpeg extracts the audio track to a
temporary mono 16 kHz WAV before sending it to CrispASR. The temporary file
is deleted when transcription finishes.

### All CLI flags

```
--profile auto|english|chinese
--format text|verbose_json|srt|vtt
--out-dir PATH
--server-url URL
--allow-remote-server
--manage-server
--keep-server
--model PATH               Local GGUF model path
--allow-model-auto-download
--lid-model PATH           Local LID model path
--lid-backend firered|silero|ecapa|whisper
--host HOST                Managed server host (default 127.0.0.1)
--port PORT                Managed server port (default 8080)
--language CODE            Language hint for transcription
--prompt TEXT              Initial prompt/context
--vad                      Enable voice activity detection
--diarize                  Enable speaker diarization
--diarize-method METHOD
--hotwords WORD,WORD       Comma-separated hotwords
--no-timestamps
--preprocess auto|always|never
--api-key KEY              If CRISPASR_API_KEYS is enabled
--crispasr-bin-dir PATH
--crispasr-bin PATH
--install-crispasr
--update-crispasr
--crispasr-status
```

## MCP server

```powershell
uv sync --extra mcp
uv run --extra mcp crispasr-agent-mcp
```

Exposed tools:

| Tool | Description |
|---|---|
| `crispasr_health` | Check CrispASR server health |
| `crispasr_backends` | List available backends |
| `crispasr_detect_language` | Run language detection on a file |
| `transcribe_audio` | Transcribe an audio file |
| `transcribe_video` | Transcribe a video file |
| `transcribe_folder` | Batch-transcribe a folder |

## Security model

- **No cloud uploads.** Media files stay on the local filesystem.
- **No remote servers by default.** `--server-url` only accepts localhost
  unless `--allow-remote-server` is explicitly passed.
- **No URL inputs.** Only local file paths are accepted. URLs, S3, and other
  remote schemes are rejected.
- **No shell injection.** ffmpeg is called with argument lists and
  `shell=False`. No user-controlled strings are interpolated into shell
  commands.
- **No model downloads by default.** CrispASR model auto-download (`-m auto`)
  requires `--allow-model-auto-download`. The same guard applies to language
  detection models.
- **Temporary files are cleaned up.** Converted WAV files and LID probe
  windows are deleted when transcription finishes.
- **Binary downloads are explicit.** CrispASR binary installs only from the
  official `CrispStrobe/CrispASR` GitHub releases.

## Verify

```powershell
uv run pytest        # 63 tests
uv run ruff check .  # zero lint warnings
```

## License

This project is licensed under the [MIT License](LICENSE).

### Third-party components and attribution

This tool orchestrates several independently-licensed projects. It does not
bundle, fork, or redistribute their code -- it downloads pre-built binaries
and calls them as subprocesses or HTTP services at runtime.

| Component | License | Role |
|---|---|---|
| [CrispASR](https://github.com/CrispStrobe/CrispASR) | MIT | ASR engine, server, language detection |
| [ffmpeg](https://ffmpeg.org/) | LGPL 2.1+ / GPL 2+ | Media decoding and audio extraction |
| [Cohere Transcribe 03-2026](https://huggingface.co/cstr) | Cohere model license | English ASR model (loaded by CrispASR) |
| [Qwen3-ASR 1.7B](https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF) | Apache 2.0 | Chinese ASR model (loaded by CrispASR) |
| [FireRed LID](https://huggingface.co/cstr/firered-lid-GGUF) | Apache 2.0 | Language detection model (loaded by CrispASR) |
| [httpx](https://github.com/encode/httpx) | BSD | HTTP client for CrispASR API |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | MIT | MCP server framework |

Model files must be downloaded separately by the user from their respective
HuggingFace repositories. See [Required models](#required-models) above.

## Related projects

- [CrispASR](https://github.com/CrispStrobe/CrispASR) -- the ASR engine this
  tool wraps
- [CrisperWeaver](https://github.com/CrispStrobe/CrisperWeaver) -- CrispASR's
  desktop GUI (not used by this tool)
