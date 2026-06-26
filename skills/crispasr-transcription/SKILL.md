---
name: crispasr-transcription
description: Transcribe or understand local audio/video files with CrispASR using local models only. Use when Codex needs to detect English or Chinese speech, transcribe media, create text/subtitle output, capture synchronized video keyframes, or operate the bundled local CrispASR MCP tools.
---

# CrispASR Transcription

Use this skill when the user asks to transcribe local audio or video through CrispASR.

Rules:

- Never upload media to cloud services.
- Use `scripts/transcribe.py`.
- Use `--profile auto` unless the user specifies English or Chinese.
- Do not let CrispASR auto-download models unless the user explicitly asks for that.
- Prefer `--models-dir models` after the recommended model bundle is installed.
- If models are missing and the user wants downloads, use `--download-models` or the MCP `crispasr_download_models` tool.
- For managed auto mode without `--models-dir`, pass both `--english-model` and `--chinese-model`.
- For an explicit profile, pass its local model path with `--model`.
- For auto language routing, pass `--lid-backend firered` and `--lid-model`.
- Use MCP `understand_video` when the user asks for video understanding, keyframes, screenshots, visual context, or agent-readable video analysis.
- The firered LID backend is the default and recommended option; whisper is available as a fallback.

Example (auto mode with firered LID):

```powershell
uv run python scripts/transcribe.py .\file.mp4 --profile auto --manage-server `
  --models-dir models
```

Example (english profile with manual server):

```powershell
uv run python scripts/transcribe.py .\file.wav --profile english `
  --server-url http://127.0.0.1:8080
```

## Model files

Download the recommended GGUF bundle with `--download-models`, or use these
filenames:

| Purpose | File | Source |
|---|---|---|
| English ASR | `cohere-transcribe-q4_k.gguf` | [Cohere Transcribe 03-2026 GGUF](https://huggingface.co/cstr/cohere-transcribe-03-2026-GGUF) |
| Chinese ASR | `qwen3-asr-1.7b-q4_k.gguf` | [Qwen3-ASR GGUF](https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF) |
| Language detection | `firered-lid-q4_k.gguf` | [FireRed LID GGUF](https://huggingface.co/cstr/firered-lid-GGUF) |

Reference: `references/crispasr_server.md`.
