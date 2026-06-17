# Project Instructions

This repository builds local-only transcription helpers for Codex and MCP agents.

- Do not upload media to cloud transcription services.
- Prefer the CrispASR HTTP server and `/v1/audio/transcriptions`.
- Do not automate the CrisperWeaver GUI as the main path.
- Keep file access narrow: accept local files only, validate paths, and reject URLs.
- Use ffmpeg with argument lists and `shell=False`.
- Do not commit model files, audio/video files, transcripts, generated outputs, or temp WAVs.
- Do not trigger model downloads during verification. If a local model is missing, stop and tell the user what to download.
- Before reporting back, run the available tests and explain the outcome in plain language.
