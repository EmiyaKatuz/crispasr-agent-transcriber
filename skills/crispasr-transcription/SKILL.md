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
- For auto language routing, pass a local LID model path with `--lid-model`.

Example:

```powershell
uv run python skills\crispasr-transcription\scripts\transcribe.py .\file.mp4 --profile auto --lid-model C:\models\crispasr\silero-lid-95-f16.gguf --server-url http://127.0.0.1:8080
```

Reference: `references/crispasr_server.md`.
