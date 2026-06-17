from __future__ import annotations

from crispasr_agent_transcriber.cli import main

from .helpers import write_tone_wav


def test_managed_server_refuses_implicit_model_download(tmp_path, capsys) -> None:
    wav_path = write_tone_wav(tmp_path / "tone.wav")
    code = main([str(wav_path), "--profile", "english", "--manage-server"])
    captured = capsys.readouterr()
    assert code == 2
    assert "local model path" in captured.err
    assert "--allow-model-auto-download" in captured.err


def test_auto_profile_refuses_implicit_lid_model_download(tmp_path, capsys) -> None:
    wav_path = write_tone_wav(tmp_path / "tone.wav")
    code = main([str(wav_path), "--profile", "auto", "--server-url", "http://127.0.0.1:8080"])
    captured = capsys.readouterr()
    assert code == 2
    assert "local language detection model path" in captured.err
    assert "--lid-model" in captured.err
