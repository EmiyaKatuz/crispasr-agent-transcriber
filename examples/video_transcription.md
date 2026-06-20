# Video Transcription Examples

The tool extracts audio locally with ffmpeg before sending it to CrispASR.

Auto mode with managed server (firered LID):

```powershell
uv run python scripts/transcribe.py .\talk.mp4 --profile auto `
  --manage-server `
  --english-model models\cohere-transcribe.gguf `
  --chinese-model models\qwen3-asr-1.7b-q4_k.gguf `
  --lid-backend firered --lid-model models\firered-lid-q2_k.gguf `
  --format vtt
```

If auto detection is uncertain, rerun with an explicit profile:

```powershell
uv run python scripts/transcribe.py .\talk.mp4 --profile english --server-url http://127.0.0.1:8080 --format text
```
