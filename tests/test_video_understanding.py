from __future__ import annotations

import json
from pathlib import Path

import pytest

from crispasr_agent_transcriber.errors import MediaError
from crispasr_agent_transcriber.schemas import MediaInfo, TranscriptionResult
from crispasr_agent_transcriber.video_understanding import (
    build_keyframe_plan,
    extract_segments,
    run_video_understanding,
)


def test_extract_segments_from_verbose_json() -> None:
    segments = extract_segments(
        {
            "text": "hello world",
            "segments": [
                {"start": 0, "end": 2.0, "text": "hello"},
                {"start": "2.0", "end": "4.0", "text": "world"},
            ],
        }
    )

    assert segments == [
        {"index": 0, "start": 0.0, "end": 2.0, "text": "hello"},
        {"index": 1, "start": 2.0, "end": 4.0, "text": "world"},
    ]


def test_keyframe_plan_uses_segment_midpoints() -> None:
    plan = build_keyframe_plan(
        segments=[
            {"index": 0, "start": 0.0, "end": 2.0, "text": "intro"},
            {"index": 1, "start": 2.0, "end": 6.0, "text": "demo"},
        ],
        media_info=MediaInfo(kind="video", duration_seconds=10.0),
        max_keyframes=2,
    )

    assert [item["timestamp_seconds"] for item in plan] == [1.0, 4.0]
    assert plan[0]["segment_text"] == "intro"


def test_keyframe_plan_requires_positive_values() -> None:
    with pytest.raises(MediaError):
        build_keyframe_plan(
            segments=[],
            media_info=MediaInfo(kind="video", duration_seconds=10.0),
            max_keyframes=0,
        )


def test_run_video_understanding_persists_manifest(tmp_path: Path, monkeypatch) -> None:
    video = tmp_path / "demo video.mp4"
    video.write_bytes(b"fake")
    transcript = tmp_path / "out" / "demo video.json"
    metadata = tmp_path / "out" / "demo video.metadata.json"

    raw = {
        "text": "agent ready transcript",
        "segments": [{"start": 0.0, "end": 2.0, "text": "agent ready transcript"}],
    }

    def fake_run_transcription(*_args, **_kwargs):
        transcript.parent.mkdir(parents=True, exist_ok=True)
        transcript.write_text(json.dumps(raw), encoding="utf-8")
        metadata.write_text("{}", encoding="utf-8")
        return TranscriptionResult(
            text=json.dumps(raw),
            output_path=transcript,
            metadata_path=metadata,
            response_format="verbose_json",
            profile="english",
            backend="cohere",
            server_url="http://127.0.0.1:8080",
            raw_response=raw,
        )

    def fake_capture_keyframes(*, video_path, output_dir, plan, ffmpeg_bin):
        output_dir.mkdir(parents=True, exist_ok=True)
        image = output_dir / "frame.jpg"
        image.write_bytes(b"jpg")
        return [{**plan[0], "path": str(image)}]

    monkeypatch.setattr(
        "crispasr_agent_transcriber.video_understanding.probe_media",
        lambda path: MediaInfo(kind="video", duration_seconds=4.0, container="mov,mp4"),
    )
    monkeypatch.setattr(
        "crispasr_agent_transcriber.video_understanding.run_transcription",
        fake_run_transcription,
    )
    monkeypatch.setattr(
        "crispasr_agent_transcriber.video_understanding.capture_keyframes",
        fake_capture_keyframes,
    )

    result = run_video_understanding(
        video,
        out_dir=tmp_path / "out",
        profile_name="english",
        max_return_text_chars=5,
    )

    assert result.manifest_path.is_file()
    assert result.agent_context_path.is_file()
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["transcription"]["text"] == "agent ready transcript"
    assert len(manifest["keyframes"]) == 1
    assert result.agent_payload["transcript_text"] == "agent"
    assert result.agent_payload["transcript_truncated"] is True
