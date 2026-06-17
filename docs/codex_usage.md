# Codex Usage

Use `scripts/transcribe.py` from this repository.

Auto-route a file through the matching local backend:

```powershell
uv run python scripts/transcribe.py .\meeting.mp4 --profile auto --server-url http://127.0.0.1:8080 --format verbose_json
```

To avoid model downloads, auto routing also needs a local language detection model:

```powershell
--lid-model C:\models\crispasr\silero-lid-95-f16.gguf
```

Force Chinese if the file is mostly Mandarin or Cantonese:

```powershell
uv run python scripts/transcribe.py .\lecture.wav --profile chinese --manage-server --model C:\models\qwen3-asr-1.7b-q4_k.gguf
```

The transcript path and metadata path are printed after a successful run.
