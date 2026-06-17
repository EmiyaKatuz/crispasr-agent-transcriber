from __future__ import annotations

import shutil
import subprocess

import pytest

from crispasr_agent_transcriber.errors import PathValidationError
from crispasr_agent_transcriber.media import prepare_media, validate_local_file

from .helpers import write_tone_wav


def test_validate_local_file_rejects_urls() -> None:
    with pytest.raises(PathValidationError):
        validate_local_file("https://example.com/audio.wav")


def test_clean_wav_does_not_convert(tmp_path) -> None:
    wav_path = write_tone_wav(tmp_path / "tone.wav")
    with prepare_media(wav_path) as prepared:
        assert prepared.upload_path == wav_path
        assert prepared.converted is False
        assert prepared.media_info.sample_rate == 16000
        assert prepared.media_info.channels == 1


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_video_is_converted_to_temporary_wav(tmp_path) -> None:
    video_path = tmp_path / "clip.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=16x16:duration=0.5",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=0.5",
            "-shortest",
            "-pix_fmt",
            "yuv420p",
            str(video_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    with prepare_media(video_path) as prepared:
        assert prepared.converted is True
        assert prepared.upload_path.suffix == ".wav"
        assert prepared.upload_path.exists()
