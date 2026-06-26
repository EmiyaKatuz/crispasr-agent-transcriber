# CrispASR Transcriber Plugin

A Codex plugin for transcribing local audio or video files through
[CrispASR](https://github.com/CrispStrobe/CrispASR) — entirely on your machine.

## What it does

- Auto-detects English vs Chinese using FireRed LID
- Routes English to Cohere Transcribe, Chinese to Qwen3-ASR 1.7B
- Extracts audio from video with ffmpeg
- Captures synchronized keyframes for agent-readable video understanding
- Outputs text, verbose JSON, SRT, or VTT
- GPU acceleration: CUDA > Vulkan > CPU
- No cloud uploads, no API keys

## Install

Tagged GitHub Releases include a ready-to-register Codex plugin ZIP. The same
release also exposes a portable MCP command for other AI agents.

### Prerequisites

- Node.js 20+
- [uv](https://docs.astral.sh/uv/)
- [ffmpeg](https://ffmpeg.org/) (in PATH)
- Three model files (see below)

### Install the plugin in Codex

Run the published installer:

```powershell
npx @emiyakatuz/crispasr-agent-transcriber@latest install
```

The installer verifies the GitHub Release, installs dependencies, installs the
GPU-preferred CrispASR build, and registers the Personal marketplace entry.
Then install it with a Codex build that supports plugin commands:

```powershell
codex plugin add crispasr-agent-transcriber@personal
```

If the CLI does not expose `codex plugin`, install **CrispASR Transcriber**
from the Personal marketplace in the Codex desktop Plugins view.

### Download models

Run `npx @emiyakatuz/crispasr-agent-transcriber@latest models`, or place these
three GGUF files in `models/`:

| Purpose | File | ~Size | Source |
|---|---|---|---|
| English ASR | `cohere-transcribe-q4_k.gguf` | smaller default | [Cohere Transcribe 03-2026 GGUF](https://huggingface.co/cstr/cohere-transcribe-03-2026-GGUF) |
| Chinese ASR | `qwen3-asr-1.7b-q4_k.gguf` | 1.3 GB | [Qwen3-ASR GGUF](https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF) |
| Language detection | `firered-lid-q4_k.gguf` | default | [FireRed LID GGUF](https://huggingface.co/cstr/firered-lid-GGUF) |

## Skills

- `crispasr-transcription` — Transcribe local audio/video with CrispASR

## MCP tools

| Tool | Description |
|---|---|
| `crispasr_health` | Check CrispASR server health |
| `crispasr_backends` | List available backends |
| `crispasr_detect_language` | Run language detection on a file |
| `crispasr_list_models` | List approved model choices and install status |
| `crispasr_download_models` | Explicitly download approved local models |
| `crispasr_resolve_model_paths` | Return recommended model paths |
| `transcribe_audio` | Transcribe an audio file |
| `transcribe_video` | Transcribe a video file |
| `understand_video` | Transcribe video, capture synced keyframes, and return an agent context |
| `transcribe_folder` | Batch-transcribe a folder |

## Usage

### Through Codex

Ask Codex to transcribe a file:

```text
Transcribe this local video with CrispASR. Use auto language routing and save as SRT.
```

Codex will use the skill or MCP tools automatically.

### From the command line

```powershell
uv run python scripts/transcribe.py sample.mp4 `
  --profile auto --manage-server `
  --models-dir models `
  --format verbose_json
```

## Security

- Media files never leave the local machine
- Only localhost servers by default
- No URL inputs — local files only
- ffmpeg called with argument lists, never shell=True
- No model downloads unless explicitly requested

## License

MIT. See [LICENSE](LICENSE).

### Third-party components

| Component | License | Role |
|---|---|---|
| [CrispASR](https://github.com/CrispStrobe/CrispASR) | MIT | ASR engine |
| [ffmpeg](https://ffmpeg.org/) | LGPL/GPL | Media decoding |
| [Cohere Transcribe](https://huggingface.co/cstr/cohere-transcribe-03-2026-GGUF) | Apache 2.0 | English ASR model |
| [Qwen3-ASR 1.7B](https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF) | Apache 2.0 | Chinese ASR model |
| [FireRed LID](https://huggingface.co/cstr/firered-lid-GGUF) | Apache 2.0 | Language detection model |
