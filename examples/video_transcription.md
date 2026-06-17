# Video Transcription Examples

The tool extracts audio locally with ffmpeg before sending it to CrispASR.

```powershell
uv run python scripts/transcribe.py .\talk.mp4 --profile auto --lid-model C:\models\crispasr\silero-lid-95-f16.gguf --server-url http://127.0.0.1:8080 --format vtt
```

If auto detection is uncertain, rerun with an explicit profile:

```powershell
uv run python scripts/transcribe.py .\talk.mp4 --profile english --server-url http://127.0.0.1:8080 --format text
```
