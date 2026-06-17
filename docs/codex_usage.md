# Codex Usage

Use `scripts/transcribe.py` from this repository.

Auto-route a file through the matching local backend:

```powershell
uv run python scripts/transcribe.py .\meeting.mp4 --profile auto --manage-server `
  --model models\cohere-transcribe.gguf `
  --lid-backend firered --lid-model models\firered-lid-q2_k.gguf `
  --format verbose_json
```

Force Chinese if the file is mostly Mandarin or Cantonese:

```powershell
uv run python scripts/transcribe.py .\lecture.wav --profile chinese --manage-server --model models\qwen3-asr-1.7b-q4_k.gguf
```

Force English:

```powershell
uv run python scripts/transcribe.py .\podcast.mp3 --profile english --manage-server --model models\cohere-transcribe.gguf --format srt
```

The transcript path and metadata path are printed after a successful run.