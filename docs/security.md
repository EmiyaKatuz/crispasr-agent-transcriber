# Security

- Media files are local only.
- URLs are rejected as media inputs.
- The default server must be on localhost.
- Remote server URLs require an explicit opt-in flag.
- ffmpeg is called with argument lists and `shell=False`.
- Temporary WAV files are removed after use.
- Model files, media files, transcripts, and generated outputs are ignored by Git.
- Managed server mode requires a local model path unless model auto-download is explicitly allowed.
- Auto language routing requires a local LID model path unless model auto-download is explicitly allowed.
