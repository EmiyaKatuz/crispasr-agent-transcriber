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
- The npm installer accepts plugin code only from the documented GitHub Release URL.
- The downloaded plugin ZIP must match the release's SHA-256 checksum before extraction.
- ZIP paths are validated before extraction to prevent writes outside the staging directory.
- Installer subprocesses use argument lists with `shell=false`.
- Updates replace managed code only and preserve `models/`, `bin/`, and `outputs/`.
- Normal uninstall preserves local data; destructive removal requires `--purge-data`.
