from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .errors import MediaError
from .media import probe_media, validate_local_file
from .schemas import MediaInfo, ResponseFormat, TranscriptionResult
from .workflow import run_transcription


@dataclass
class VideoUnderstandingResult:
    manifest_path: Path
    agent_context_path: Path
    transcript_path: Path
    metadata_path: Path
    keyframes: list[dict[str, Any]]
    agent_payload: dict[str, Any]


def _safe_stem(path: Path) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", path.stem).strip("._")
    return stem or "video"


def _seconds(value: Any) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    if isinstance(value, list | tuple) and value:
        return _seconds(value[0])
    return None


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def extract_transcript_text(raw_response: Any, fallback: str) -> str:
    if isinstance(raw_response, dict):
        text = raw_response.get("text")
        if isinstance(text, str):
            return text
    return fallback


def extract_segments(raw_response: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_response, dict):
        return []

    raw_segments = raw_response.get("segments")
    if not isinstance(raw_segments, list):
        raw_segments = raw_response.get("chunks")
    if not isinstance(raw_segments, list):
        return []

    segments: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_segments):
        if not isinstance(raw, dict):
            continue
        timestamp = raw.get("timestamp")
        start = _seconds(_first_present(raw.get("start"), raw.get("start_time"), timestamp))
        end = _seconds(_first_present(raw.get("end"), raw.get("end_time")))
        if end is None and isinstance(timestamp, list | tuple) and len(timestamp) > 1:
            end = _seconds(timestamp[1])
        text = raw.get("text")
        segments.append(
            {
                "index": index,
                "start": start,
                "end": end,
                "text": text.strip() if isinstance(text, str) else "",
            }
        )
    return segments


def _clip_timestamp(timestamp: float, duration_seconds: float | None) -> float:
    if duration_seconds is None or duration_seconds <= 0:
        return max(0.0, timestamp)
    return max(0.0, min(timestamp, max(0.0, duration_seconds - 0.05)))


def build_keyframe_plan(
    *,
    segments: list[dict[str, Any]],
    media_info: MediaInfo,
    interval_seconds: float = 30.0,
    max_keyframes: int = 12,
) -> list[dict[str, Any]]:
    if max_keyframes < 1:
        raise MediaError("max_keyframes must be at least 1.", max_keyframes=max_keyframes)
    if interval_seconds <= 0:
        raise MediaError("keyframe interval must be positive.", interval_seconds=interval_seconds)

    candidates: list[dict[str, Any]] = []
    for segment in segments:
        start = segment.get("start")
        end = segment.get("end")
        if not isinstance(start, int | float):
            continue
        timestamp = float(start)
        if isinstance(end, int | float) and end > start:
            timestamp = float(start + (end - start) / 2)
        candidates.append(
            {
                "timestamp_seconds": _clip_timestamp(timestamp, media_info.duration_seconds),
                "segment_index": segment.get("index"),
                "segment_start": start,
                "segment_end": end,
                "segment_text": segment.get("text", ""),
            }
        )

    if not candidates:
        duration = media_info.duration_seconds
        if duration is None or duration <= 0:
            timestamps = [0.0]
        else:
            timestamps = []
            current = 0.0
            while current < duration and len(timestamps) < max_keyframes:
                timestamps.append(_clip_timestamp(current, duration))
                current += interval_seconds
            if not timestamps:
                timestamps = [0.0]
        candidates = [
            {
                "timestamp_seconds": timestamp,
                "segment_index": None,
                "segment_start": None,
                "segment_end": None,
                "segment_text": "",
            }
            for timestamp in timestamps
        ]

    if len(candidates) <= max_keyframes:
        selected = candidates
    elif max_keyframes == 1:
        selected = [candidates[0]]
    else:
        selected = [
            candidates[round(index * (len(candidates) - 1) / (max_keyframes - 1))]
            for index in range(max_keyframes)
        ]

    for index, item in enumerate(selected, start=1):
        item["index"] = index
    return selected


def capture_keyframes(
    *,
    video_path: Path,
    output_dir: Path,
    plan: list[dict[str, Any]],
    ffmpeg_bin: str = "ffmpeg",
) -> list[dict[str, Any]]:
    if shutil.which(ffmpeg_bin) is None and not Path(ffmpeg_bin).is_file():
        raise MediaError("ffmpeg is required to capture video keyframes.", ffmpeg=ffmpeg_bin)

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = _safe_stem(video_path)
    frames: list[dict[str, Any]] = []
    for item in plan:
        timestamp = float(item["timestamp_seconds"])
        image_path = output_dir / f"{safe_stem}.frame_{item['index']:04d}_{timestamp:09.3f}.jpg"
        command = [
            ffmpeg_bin,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(image_path),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True, shell=False)
        except subprocess.CalledProcessError as exc:
            raise MediaError(
                "ffmpeg failed to capture a video keyframe.",
                command=command,
                stderr=exc.stderr[-1000:],
            ) from exc
        frames.append(
            {
                **item,
                "path": str(image_path),
            }
        )
    return frames


def _truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
    if max_chars < 1 or len(text) <= max_chars:
        return text, False
    return text[:max_chars], True


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_agent_payload(
    *,
    manifest_path: Path,
    agent_context_path: Path,
    transcript_path: Path,
    metadata_path: Path,
    transcript_text: str,
    segments: list[dict[str, Any]],
    keyframes: list[dict[str, Any]],
    media_info: MediaInfo,
    max_return_text_chars: int,
) -> dict[str, Any]:
    returned_text, truncated = _truncate_text(transcript_text, max_return_text_chars)
    return {
        "type": "crispasr_video_understanding",
        "manifest_path": str(manifest_path),
        "agent_context_path": str(agent_context_path),
        "transcript_path": str(transcript_path),
        "metadata_path": str(metadata_path),
        "duration_seconds": media_info.duration_seconds,
        "transcript_text": returned_text,
        "transcript_truncated": truncated,
        "segments": segments[:80],
        "segments_truncated": len(segments) > 80,
        "keyframes": keyframes,
    }


def run_video_understanding(
    input_path: str | Path,
    *,
    out_dir: str | Path = "outputs",
    keyframe_interval_seconds: float = 30.0,
    max_keyframes: int = 12,
    max_return_text_chars: int = 4000,
    ffmpeg_bin: str = "ffmpeg",
    profile_name: str = "auto",
    response_format: ResponseFormat = "verbose_json",
    **transcription_options: Any,
) -> VideoUnderstandingResult:
    video_path = validate_local_file(input_path)
    media_info = probe_media(video_path)
    if media_info.kind != "video":
        raise MediaError("Video understanding requires a local video file.", path=str(video_path))

    result: TranscriptionResult = run_transcription(
        video_path,
        profile_name=profile_name,
        response_format=response_format,
        out_dir=out_dir,
        **transcription_options,
    )

    segments = extract_segments(result.raw_response)
    transcript_text = extract_transcript_text(result.raw_response, result.text)
    plan = build_keyframe_plan(
        segments=segments,
        media_info=media_info,
        interval_seconds=keyframe_interval_seconds,
        max_keyframes=max_keyframes,
    )

    output_dir = Path(out_dir)
    stem = _safe_stem(video_path)
    keyframe_dir = output_dir / f"{stem}.keyframes"
    keyframes = capture_keyframes(
        video_path=video_path,
        output_dir=keyframe_dir,
        plan=plan,
        ffmpeg_bin=ffmpeg_bin,
    )

    manifest_path = output_dir / f"{stem}.video_understanding.json"
    agent_context_path = output_dir / f"{stem}.agent_context.json"
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "source": {
            "path": str(video_path),
            "duration_seconds": media_info.duration_seconds,
            "container": media_info.container,
            "codec": media_info.codec,
        },
        "transcription": {
            "transcript_path": str(result.output_path),
            "metadata_path": str(result.metadata_path),
            "profile": result.profile,
            "backend": result.backend,
            "server_url": result.server_url,
            "response_format": result.response_format,
            "text": transcript_text,
            "segments": segments,
            "language_detection": (
                result.language_detection.to_dict() if result.language_detection else None
            ),
        },
        "keyframes": keyframes,
    }
    _write_json(manifest_path, manifest)

    agent_payload = build_agent_payload(
        manifest_path=manifest_path,
        agent_context_path=agent_context_path,
        transcript_path=result.output_path,
        metadata_path=result.metadata_path,
        transcript_text=transcript_text,
        segments=segments,
        keyframes=keyframes,
        media_info=media_info,
        max_return_text_chars=max_return_text_chars,
    )
    _write_json(agent_context_path, agent_payload)
    return VideoUnderstandingResult(
        manifest_path=manifest_path,
        agent_context_path=agent_context_path,
        transcript_path=result.output_path,
        metadata_path=result.metadata_path,
        keyframes=keyframes,
        agent_payload=agent_payload,
    )
