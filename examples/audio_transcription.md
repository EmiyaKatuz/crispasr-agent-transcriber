# Audio Transcription Examples

English through an already running Cohere server:

```powershell
uv run python scripts/transcribe.py .\meeting.wav --profile english --server-url http://127.0.0.1:8080 --format verbose_json
```

Chinese through managed Qwen3-ASR 1.7B:

```powershell
uv run python scripts/transcribe.py .\lecture.wav --profile chinese --manage-server --model C:\models\qwen3-asr-1.7b-q4_k.gguf --format srt
```
