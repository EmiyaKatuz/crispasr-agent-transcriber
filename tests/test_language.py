from __future__ import annotations

import pytest

from crispasr_agent_transcriber.errors import UncertainLanguageError
from crispasr_agent_transcriber.language import (
    _classify,
    _parse_lid_output,
    _resolve_lid_backend_name,
    run_cli_lid,
)


class TestBackendName:
    def test_firered(self):
        assert _resolve_lid_backend_name("firered") == "firered"

    def test_silero(self):
        assert _resolve_lid_backend_name("silero") == "lid-silero"

    def test_unknown_passthrough(self):
        assert _resolve_lid_backend_name("custom") == "custom"


class TestParseLidOutput:
    def test_matches_iso_code(self):
        assert _parse_lid_output("zh") == "zh"
        assert _parse_lid_output("en") == "en"

    def test_handles_multiline(self):
        raw = "loading model...\nprocessing...\nzh\n"
        assert _parse_lid_output(raw) == "zh"

    def test_returns_none_for_empty(self):
        assert _parse_lid_output("") is None

    def test_handles_punctuation_suffix(self):
        assert _parse_lid_output("Zh?") == "zh"
        assert _parse_lid_output("En?") == "en"


class TestClassify:
    def test_english(self):
        assert _classify("en") == "english"

    def test_chinese(self):
        assert _classify("zh") == "chinese"
        assert _classify("cmn") == "chinese"

    def test_uncertain(self):
        assert _classify("de") == "uncertain"
        assert _classify(None) == "uncertain"


class TestRunCliLid:
    def test_routes_chinese(self, tmp_path, monkeypatch):
        wav = tmp_path / "test.wav"
        wav.write_bytes(b"RIFF....WAVE....")

        def fake_run(*args, **kwargs):
            return type("R", (), {
                "stdout": "zh\n",
                "stderr": "",
                "returncode": 0,
            })()

        monkeypatch.setattr("subprocess.run", fake_run)
        result = run_cli_lid(
            str(wav), lid_model="models/firered-lid-q2_k.gguf"
        )
        assert result.decision == "chinese"

    def test_raises_on_uncertain(self, tmp_path, monkeypatch):
        wav = tmp_path / "test.wav"
        wav.write_bytes(b"RIFF....WAVE....")

        def fake_run(*args, **kwargs):
            return type("R", (), {
                "stdout": "de\n",
                "stderr": "",
                "returncode": 0,
            })()

        monkeypatch.setattr("subprocess.run", fake_run)
        with pytest.raises(UncertainLanguageError):
            run_cli_lid(str(wav), lid_model="models/fake.gguf")