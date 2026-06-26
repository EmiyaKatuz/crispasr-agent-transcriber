# crispasr-agent-transcriber

<!-- mcp-name: io.github.EmiyaKatuz/crispasr-agent-transcriber -->

Local-only transcription for Codex and MCP-based AI agents, powered by
[CrispASR](https://github.com/CrispStrobe/CrispASR). No cloud uploads,
no API keys required for transcription.

[GitHub Release](https://github.com/EmiyaKatuz/crispasr-agent-transcriber/releases/latest)
| [npm installer](https://www.npmjs.com/package/@emiyakatuz/crispasr-agent-transcriber)
| [PyPI package](https://pypi.org/project/crispasr-agent-transcriber/)
| [MCP Registry](https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.EmiyaKatuz%2Fcrispasr-agent-transcriber)

## What it does

Give it a local audio or video file. It:

1. Probes the spoken language (English or Chinese) using CrispASR's FireRed LID.
2. Starts a local CrispASR server with the right backend -- Cohere Transcribe
   for English, Qwen3-ASR for Chinese.
3. Extracts audio from video with ffmpeg when needed.
4. Calls CrispASR's `/v1/audio/transcriptions` endpoint.
5. Writes the transcript and metadata to disk.
6. For video understanding, captures synchronized keyframes and writes an
   agent-readable manifest.

Everything runs on your machine. Media never leaves it.

## Quick install for Codex

The plugin includes the Codex Skill, command-line tool, and MCP server. Media
stays on your computer. Model files are never downloaded during install/update;
use the explicit `models` command when you want the installer to fetch them.

### 1. Install prerequisites

Install Node.js 20 or newer, [uv](https://docs.astral.sh/uv/), and
[ffmpeg](https://ffmpeg.org/). The installer uses `uv` to provide Python.

```powershell
node --version
uv --version
ffmpeg -version
```

### 2. Run the installer

```powershell
npx @emiyakatuz/crispasr-agent-transcriber@latest install
```

The installer:

- downloads the matching GitHub Release and verifies its SHA-256 checksum;
- installs the plugin under `~/plugins/crispasr-agent-transcriber`;
- installs the Python and MCP dependencies;
- detects CUDA, Vulkan, or CPU and installs the best CrispASR build;
- registers the plugin in the Codex Personal marketplace;
- preserves existing models, binaries, and outputs during updates.

### 3. Add the local models

Download the recommended local English, Chinese, and language-detection bundle:

```powershell
npx @emiyakatuz/crispasr-agent-transcriber@latest models
```

The command downloads only approved GGUF files into:

```text
~/plugins/crispasr-agent-transcriber/models/
```

Then verify the installation:

```powershell
npx @emiyakatuz/crispasr-agent-transcriber@latest doctor
```

### 4. Enable the plugin

With a Codex build that supports plugin commands, run:

```powershell
codex plugin add crispasr-agent-transcriber@personal
```

If the CLI has no `codex plugin` command, open the Codex desktop Plugins view
and install **CrispASR Transcriber** from the Personal marketplace. Start a new
conversation, then ask:

```text
Transcribe C:\path\to\sample.mp4 with CrispASR using auto language detection.
Save a verbose JSON transcript and an SRT subtitle file.
```

### Update or uninstall

```powershell
npx @emiyakatuz/crispasr-agent-transcriber@latest update
npx @emiyakatuz/crispasr-agent-transcriber@latest uninstall
```

Uninstall preserves local models, CrispASR binaries, and outputs. Use
`uninstall --purge-data` only when those files should also be deleted. See
[Plugin installation](docs/plugin_install.md) for manual installation and
troubleshooting.

## Direct command-line use

After installation, you can run the transcription script without Codex:

```powershell
Set-Location (Join-Path $HOME "plugins\crispasr-agent-transcriber")
uv run python scripts/transcribe.py sample.mp4 --profile auto `
  --manage-server `
  --models-dir models `
  --format verbose_json
```

## Use with other AI agents

The MCP server is the cross-agent interface. Any agent that supports MCP stdio
can run the released package directly from GitHub:

```powershell
uvx --from "crispasr-agent-transcriber[mcp] @ git+https://github.com/EmiyaKatuz/crispasr-agent-transcriber.git@v0.4.0" crispasr-agent-mcp
```

Use the same command and arguments in Claude Desktop, Cursor, or another MCP
client. See [AI agent integrations](docs/agent_integrations.md) for a generic
MCP configuration and Codex CLI command.

## Maintainer publishing

End users do not need the release steps. Maintainers should follow the
[publishing guide](docs/publishing.md) for Codex Marketplace, PyPI, MCP
Registry, and cross-agent distribution.

## Required models

Install/update never downloads models. Use the explicit `models` command or
download these three recommended GGUF files into a local directory such as
`models/`:

| Purpose | Local file | Variant / size | Model page | File page |
|---|---|---|---|---|
| English ASR | `cohere-transcribe-q4_k.gguf` | Q4_K, smaller default | [Cohere Transcribe 03-2026 GGUF](https://huggingface.co/cstr/cohere-transcribe-03-2026-GGUF) | [Download](https://huggingface.co/cstr/cohere-transcribe-03-2026-GGUF/blob/main/cohere-transcribe-q4_k.gguf) |
| Chinese ASR | `qwen3-asr-1.7b-q4_k.gguf` | Q4_K, smaller default | [Qwen3-ASR 1.7B GGUF](https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF) | [Download](https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF/blob/main/qwen3-asr-1.7b-q4_k.gguf) |
| Language detection | `firered-lid-q4_k.gguf` | Q4_K default | [FireRed LID GGUF](https://huggingface.co/cstr/firered-lid-GGUF) | [Download](https://huggingface.co/cstr/firered-lid-GGUF/blob/main/firered-lid-q4_k.gguf) |

Optional model IDs include `english-q5-0`, `english-q5-1`, `english-q6`,
`english-q8`, `english-f16`, `chinese-q8`, `chinese-f16`, `lid-q2`, `lid-q8`,
and `lid-f16`. Download a specific option with:

```powershell
npx @emiyakatuz/crispasr-agent-transcriber@latest models --model-id english-q8
```

All three upstream model families are Apache 2.0 licensed.

For automatic English/Chinese routing, pass both ASR paths. The language probe
runs first, and only the matching model is loaded:

```powershell
--english-model models\cohere-transcribe-q4_k.gguf
--chinese-model models\qwen3-asr-1.7b-q4_k.gguf
--lid-backend firered --lid-model models\firered-lid-q4_k.gguf
```

For an explicit `english` or `chinese` profile, `--model` remains available as
a single-model override.

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
  --models-dir models `
  --format srt `
  --out-dir outputs
```

Add `--keep-server` to leave the server running after transcription.

### Manual server (you start CrispASR)

```powershell
# Terminal 1 -- start the server
crispasr --server --backend cohere `
  -m models\cohere-transcribe-q4_k.gguf `
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
--format text|verbose_json|srt|vtt|json
--out-dir PATH
--server-url URL
--allow-remote-server
--manage-server
--keep-server
--model PATH               Local GGUF override for an explicit profile
--english-model PATH       Cohere model selected after English detection
--chinese-model PATH       Qwen3-ASR model selected after Chinese detection
--models-dir PATH          Directory containing approved local GGUF models
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
--list-models
--download-models
--model-id MODEL_ID
--overwrite-models
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
| `crispasr_list_models` | List approved model choices and local install status |
| `crispasr_download_models` | Explicitly download approved model files |
| `crispasr_resolve_model_paths` | Return recommended local model paths |
| `transcribe_audio` | Transcribe an audio file |
| `transcribe_video` | Transcribe a video file |
| `understand_video` | Transcribe a video, capture synced keyframes, and return an agent context |
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
- **No implicit model downloads.** Install/update never downloads models, and
  CrispASR model auto-download (`-m auto`) requires
  `--allow-model-auto-download`. The `models` command and
  `crispasr_download_models` tool download only allowlisted Hugging Face files.
- **Temporary files are cleaned up.** Converted WAV files and LID probe
  windows are deleted when transcription finishes.
- **Binary downloads are explicit.** CrispASR binary installs only from the
  official `CrispStrobe/CrispASR` GitHub releases.
- **Verified plugin releases.** The npm installer requires the plugin ZIP to
  match the SHA-256 value published in the same GitHub Release.
- **Narrow installer writes.** The installer manages only its plugin directory
  and the named Personal marketplace entry. Updates preserve local models,
  binaries, and outputs.
- **Generated understanding stays local.** Video keyframes, manifests, and
  agent context files are written under the selected output directory and are
  ignored by Git.

## Verify

```powershell
uv run pytest
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
| [Cohere Transcribe 03-2026](https://huggingface.co/cstr/cohere-transcribe-03-2026-GGUF) | Apache 2.0 | English ASR model (loaded by CrispASR) |
| [Qwen3-ASR 1.7B](https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF) | Apache 2.0 | Chinese ASR model (loaded by CrispASR) |
| [FireRed LID](https://huggingface.co/cstr/firered-lid-GGUF) | Apache 2.0 | Language detection model (loaded by CrispASR) |
| [httpx](https://github.com/encode/httpx) | BSD | HTTP client for CrispASR API |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | MIT | MCP server framework |
| [Node.js](https://nodejs.org/) | MIT | npm installer runtime |
| [adm-zip](https://github.com/cthackers/adm-zip) | MIT | Verified plugin ZIP extraction |

Model files must be downloaded separately by the user from their respective
HuggingFace repositories. See [Required models](#required-models) above.

## Related projects

- [CrispASR](https://github.com/CrispStrobe/CrispASR) -- the ASR engine this
  tool wraps
- [CrisperWeaver](https://github.com/CrispStrobe/CrisperWeaver) -- CrispASR's
  desktop GUI (not used by this tool)
