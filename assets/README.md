# CrispASR Transcriber Plugin

A Codex plugin for transcribing local audio or video files through
[CrispASR](https://github.com/CrispStrobe/CrispASR) — entirely on your machine.

## What it does

- Auto-detects English vs Chinese using FireRed LID
- Routes English to Cohere Transcribe, Chinese to Qwen3-ASR 1.7B
- Extracts audio from video with ffmpeg
- Outputs text, verbose JSON, SRT, or VTT
- GPU acceleration: CUDA > Vulkan > CPU
- No cloud uploads, no API keys

## Install

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- [ffmpeg](https://ffmpeg.org/) (in PATH)
- Three model files (see below)

### Install the plugin in Codex

Clone the repository into the personal plugin directory:

```powershell
$pluginRoot = Join-Path $HOME "plugins\crispasr-agent-transcriber"
git clone https://github.com/EmiyaKatuz/crispasr-agent-transcriber.git $pluginRoot
Set-Location $pluginRoot
```

Register it in the Personal marketplace as described in
[Plugin installation](../docs/plugin_install.md), then install it with a Codex
build that supports plugin commands:

```powershell
codex plugin add crispasr-agent-transcriber@personal
```

If the CLI does not expose `codex plugin`, install **CrispASR Transcriber**
from the Personal marketplace in the Codex desktop Plugins view.

### Install CrispASR binary

```powershell
uv sync --extra mcp
uv run python scripts/transcribe.py --install-crispasr
```

This auto-detects your GPU (CUDA/Vulkan/CPU) and downloads the right binary.

### Download models

Place these three GGUF files in `models/`:

| Purpose | File | ~Size | Source |
|---|---|---|---|
| English ASR | `cohere-transcribe.gguf` | 3.9 GB | [Cohere on HuggingFace](https://huggingface.co/cstr) |
| Chinese ASR | `qwen3-asr-1.7b-q4_k.gguf` | 1.3 GB | [Qwen3-ASR GGUF](https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF) |
| Language detection | `firered-lid-q2_k.gguf` | 350 MB | [FireRed LID GGUF](https://huggingface.co/cstr/firered-lid-GGUF) |

## Skills

- `crispasr-transcription` — Transcribe local audio/video with CrispASR

## MCP tools

| Tool | Description |
|---|---|
| `crispasr_health` | Check CrispASR server health |
| `crispasr_backends` | List available backends |
| `crispasr_detect_language` | Run language detection on a file |
| `transcribe_audio` | Transcribe an audio file |
| `transcribe_video` | Transcribe a video file |
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
  --model models\cohere-transcribe.gguf `
  --lid-backend firered --lid-model models\firered-lid-q2_k.gguf `
  --format verbose_json
```

## Security

- Media files never leave the local machine
- Only localhost servers by default
- No URL inputs — local files only
- ffmpeg called with argument lists, never shell=True
- No model downloads unless explicitly enabled

## License

MIT. See [LICENSE](LICENSE).

### Third-party components

| Component | License | Role |
|---|---|---|
| [CrispASR](https://github.com/CrispStrobe/CrispASR) | MIT | ASR engine |
| [ffmpeg](https://ffmpeg.org/) | LGPL/GPL | Media decoding |
| [Cohere Transcribe](https://huggingface.co/cstr) | Cohere license | English ASR model |
| [Qwen3-ASR 1.7B](https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF) | Apache 2.0 | Chinese ASR model |
| [FireRed LID](https://huggingface.co/cstr/firered-lid-GGUF) | Apache 2.0 | Language detection model |
