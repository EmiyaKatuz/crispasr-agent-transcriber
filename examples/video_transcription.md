# Video Transcription Examples

The tool extracts audio locally with ffmpeg before sending it to CrispASR.

Auto mode with managed server (firered LID):

```powershell
uv run python scripts/transcribe.py .\talk.mp4 --profile auto `
  --manage-server `
  --models-dir models `
  --format vtt
```

If auto detection is uncertain, rerun with an explicit profile:

```powershell
uv run python scripts/transcribe.py .\talk.mp4 --profile english --server-url http://127.0.0.1:8080 --format text
```
