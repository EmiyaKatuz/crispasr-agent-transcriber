from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import wave
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .errors import MediaError, PathValidationError
from .schemas import MediaInfo

PreprocessMode = Literal["auto", "always", "never"]

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".m4v",
    ".mkv",
    ".webm",
    ".avi",
    ".wmv",
    ".flv",
    ".mpeg",
    ".mpg",
}

AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
    ".opus",
    ".wma",
    ".aiff",
    ".aif",
}


@dataclass
class PreparedMedia:
    original_path: Path
    upload_path: Path
    media_info: MediaInfo
    converted: bool
    temporary_directory: tempfile.TemporaryDirectory[str] | None = None

    def cleanup(self) -> None:
        if self.temporary_directory:
            self.temporary_directory.cleanup()


def validate_local_file(path: str | Path) -> Path:
    raw = str(path)
    lowered = raw.lower()
    if "\x00" in raw:
        raise PathValidationError("Media path contains an invalid NUL byte.")
    if "://" in raw or lowered.startswith(("http:", "https:", "ftp:", "s3:", "gs:", "file:")):
        raise PathValidationError("Only local filesystem paths are accepted.", path=raw)

    resolved = Path(path).expanduser().resolve(strict=True)
    if not resolved.is_file():
        raise PathValidationError("Media path must point to an existing file.", path=str(resolved))
    return resolved


def _run_json_command(command: list[str]) -> dict:
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            shell=False,
        )
    except FileNotFoundError as exc:
        raise MediaError("Required media tool was not found.", command=command[0]) from exc
    except subprocess.CalledProcessError as exc:
        raise MediaError(
            "Media probing failed.",
            command=command,
            stderr=exc.stderr[-1000:],
        ) from exc
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise MediaError("Media probing returned invalid JSON.", command=command) from exc


def _wave_info(path: Path) -> MediaInfo | None:
    if path.suffix.lower() != ".wav":
        return None
    try:
        with wave.open(str(path), "rb") as wav:
            return MediaInfo(
                kind="audio",
                duration_seconds=wav.getnframes() / float(wav.getframerate()),
                sample_rate=wav.getframerate(),
                channels=wav.getnchannels(),
                codec="pcm_s16le" if wav.getsampwidth() == 2 else f"pcm_{wav.getsampwidth() * 8}",
                container="wav",
            )
    except wave.Error:
        return None


def probe_media(path: Path) -> MediaInfo:
    wave_info = _wave_info(path)
    if wave_info:
        return wave_info

    if shutil.which("ffprobe"):
        data = _run_json_command(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(path),
            ]
        )
        streams = data.get("streams", [])
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        fmt = data.get("format", {})
        kind = "video" if video_stream else "audio" if audio_stream else "unknown"
        duration_raw = fmt.get("duration") or (audio_stream or {}).get("duration")
        duration = float(duration_raw) if duration_raw else None
        sample_rate_raw = (audio_stream or {}).get("sample_rate")
        return MediaInfo(
            kind=kind,
            duration_seconds=duration,
            sample_rate=int(sample_rate_raw) if sample_rate_raw else None,
            channels=(audio_stream or {}).get("channels"),
            codec=(audio_stream or {}).get("codec_name"),
            container=fmt.get("format_name"),
        )

    suffix = path.suffix.lower()
    if suffix in VIDEO_EXTENSIONS:
        return MediaInfo(kind="video")
    if suffix in AUDIO_EXTENSIONS:
        return MediaInfo(kind="audio")
    return MediaInfo(kind="unknown")


def needs_preprocess(path: Path, info: MediaInfo, mode: PreprocessMode) -> bool:
    if mode == "always":
        return True
    if mode == "never":
        return False
    if info.kind == "video":
        return True
    if path.suffix.lower() != ".wav":
        return True
    return not (
        info.kind == "audio"
        and info.sample_rate == 16000
        and info.channels == 1
        and (info.codec or "").lower() in {"pcm_s16le", "pcm_16"}
    )


def convert_to_wav(input_path: Path, output_path: Path) -> None:
    if not shutil.which("ffmpeg"):
        raise MediaError("ffmpeg is required to convert media before transcription.")
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, shell=False)
    except subprocess.CalledProcessError as exc:
        raise MediaError(
            "ffmpeg failed to prepare media.",
            command=command,
            stderr=exc.stderr[-1000:],
        ) from exc


@contextmanager
def prepare_media(
    path: str | Path,
    *,
    preprocess: PreprocessMode = "auto",
) -> Iterator[PreparedMedia]:
    original_path = validate_local_file(path)
    info = probe_media(original_path)
    if info.kind == "unknown":
        raise MediaError(
            "Input does not contain a recognizable audio stream.",
            path=str(original_path),
        )

    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    upload_path = original_path
    converted = False
    if needs_preprocess(original_path, info, preprocess):
        temp_dir = tempfile.TemporaryDirectory(prefix="crispasr-agent-")
        upload_path = Path(temp_dir.name) / "prepared.wav"
        convert_to_wav(original_path, upload_path)
        converted = True
        info = probe_media(upload_path)

    prepared = PreparedMedia(
        original_path=original_path,
        upload_path=upload_path,
        media_info=info,
        converted=converted,
        temporary_directory=temp_dir,
    )
    try:
        yield prepared
    finally:
        prepared.cleanup()


def create_probe_windows(
    audio_path: Path,
    *,
    duration_seconds: float | None,
    window_seconds: float = 15.0,
    max_windows: int = 3,
) -> tuple[tempfile.TemporaryDirectory[str], list[Path]]:
    if not shutil.which("ffmpeg"):
        raise MediaError("ffmpeg is required to create language detection samples.")

    temp_dir = tempfile.TemporaryDirectory(prefix="crispasr-agent-lid-")
    wave_info = _wave_info(audio_path)
    duration = duration_seconds if duration_seconds is not None else (
        wave_info.duration_seconds if wave_info else None
    )
    if duration is None or duration <= window_seconds:
        starts = [0.0]
    else:
        raw_starts = [duration * 0.1, duration * 0.5, duration * 0.85]
        starts = [min(max(0.0, start), max(0.0, duration - window_seconds)) for start in raw_starts]
        deduped: list[float] = []
        for start in starts:
            if not any(abs(start - existing) < 1.0 for existing in deduped):
                deduped.append(start)
        starts = deduped[:max_windows]

    paths: list[Path] = []
    for index, start in enumerate(starts):
        out_path = Path(temp_dir.name) / f"probe-{index}.wav"
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{window_seconds:.3f}",
            "-i",
            str(audio_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(out_path),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True, shell=False)
        except subprocess.CalledProcessError as exc:
            temp_dir.cleanup()
            raise MediaError(
                "ffmpeg failed to create a language detection sample.",
                command=command,
                stderr=exc.stderr[-1000:],
            ) from exc
        paths.append(out_path)
    return temp_dir, paths
