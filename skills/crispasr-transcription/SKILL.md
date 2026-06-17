---
name: crispasr-transcription
description: Transcribe local audio or video with CrispASR using local models only.
---

# CrispASR Transcription

Use this skill when the user asks to transcribe local audio or video through CrispASR.

Rules:

- Never upload media to cloud services.
- Use `scripts/transcribe.py`.
- Use `--profile auto` unless the user specifies English or Chinese.
- Do not let CrispASR auto-download models unless the user explicitly asks for that.
- For managed server mode, pass a local model path with `--model`.
- For auto language routing, pass `--lid-backend firered` and `--lid-model`.
- The firered LID backend is the default and recommended option; whisper is available as a fallback.

Example (auto mode with firered LID):

```powershell
uv run python scripts/transcribe.py .\file.mp4 --profile auto --manage-server `
  --model models\cohere-transcribe.gguf `
  --lid-backend firered --lid-model models\firered-lid-q2_k.gguf
```

Example (english profile with manual server):

```powershell
uv run python scripts/transcribe.py .\file.wav --profile english `
  --server-url http://127.0.0.1:8080
```

## Model files

Download these three GGUF files:

| Purpose | File | Source |
|---|---|---|
| English ASR | `cohere-transcribe.gguf` | [Cohere on HuggingFace](https://huggingface.co/cstr) |
| Chinese ASR | `qwen3-asr-1.7b-q4_k.gguf` | [Qwen3-ASR GGUF](https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF) |
| Language detection | `firered-lid-q2_k.gguf` | [FireRed LID GGUF](https://huggingface.co/cstr/firered-lid-GGUF) |

Reference: `references/crispasr_server.md`.