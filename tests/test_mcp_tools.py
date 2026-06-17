from __future__ import annotations

import wave

from crispasr_mcp import tools

from crispasr_agent_transcriber.errors import ServerError


def _make_wav(path, duration_seconds=1.0) -> None:
    """Create a minimal valid 16 kHz mono WAV file for testing."""
    sample_rate = 16000
    n_frames = int(sample_rate * duration_seconds)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(b"\x00\x00" * n_frames)


class TestCrispasrHealth:
    def test_returns_error_when_server_unreachable(self):
        result = tools.crispasr_health(server_url="http://127.0.0.1:19999")
        assert result["ok"] is False
        assert "error" in result


class TestCrispasrBackends:
    def test_returns_error_when_server_unreachable(self):
        result = tools.crispasr_backends(server_url="http://127.0.0.1:19999")
        assert result["ok"] is False
        assert "error" in result


class TestCrispasrDetectLanguage:
    def test_returns_error_for_missing_file(self):
        result = tools.crispasr_detect_language(
            "nonexistent_file.wav",
            lid_model="models/fake.gguf",
        )
        assert result["ok"] is False
        assert "error" in result

    def test_runs_lid_and_returns_detection(self, tmp_path, monkeypatch):
        wav = tmp_path / "test.wav"
        _make_wav(wav)

        def fake_run(*args, **kwargs):
            return type("R", (), {
                "stdout": "zh\n",
                "stderr": "",
                "returncode": 0,
            })()

        monkeypatch.setattr(
            "crispasr_agent_transcriber.language.subprocess.run", fake_run
        )
        result = tools.crispasr_detect_language(
            str(wav),
            lid_model="models/firered-lid-q2_k.gguf",
            lid_backend="firered",
        )
        assert result["ok"] is True
        detection = result["language_detection"]
        assert detection["decision"] == "chinese"
        assert detection["detected_language"] == "zh"


class TestTranscribeAudio:
    def test_returns_error_for_missing_file(self):
        result = tools.transcribe_audio("nonexistent.mp3")
        assert result["ok"] is False
        assert "error" in result

    def test_returns_error_when_no_server_and_no_managed(self, tmp_path):
        wav = tmp_path / "sample.wav"
        _make_wav(wav)

        result = tools.transcribe_audio(str(wav), profile="english")
        assert result["ok"] is False
        error = result["error"]
        assert error["code"] == "crispasr_server_error"


class TestTranscribeVideo:
    def test_returns_error_for_missing_file(self):
        result = tools.transcribe_video("nonexistent.mp4")
        assert result["ok"] is False
        assert "error" in result


class TestTranscribeFolder:
    def test_rejects_nonexistent_folder(self):
        result = tools.transcribe_folder("nonexistent_folder")
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_folder"

    def test_skips_non_media_files(self, tmp_path):
        (tmp_path / "readme.txt").write_text("hello")
        result = tools.transcribe_folder(str(tmp_path))
        assert result["ok"] is True
        assert result["results"] == []


class TestErrorPayload:
    def test_formats_transcriber_error(self):
        exc = ServerError("test message", code="crispasr_server_error")
        payload = tools._error_payload(exc)
        assert payload["ok"] is False
        assert payload["error"]["code"] == "crispasr_server_error"
        assert "test message" in payload["error"]["message"]

    def test_formats_generic_exception(self):
        exc = RuntimeError("something broke")
        payload = tools._error_payload(exc)
        assert payload["ok"] is False
        assert payload["error"]["code"] == "internal_error"
        assert "something broke" in payload["error"]["message"]