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



def test_install_crispasr_flag(monkeypatch, capsys) -> None:
    calls = []

    def fake_install(*, bin_dir=None):
        calls.append(bin_dir)
        from pathlib import Path
        return Path("/fake/crispasr.exe")

    monkeypatch.setattr(
        "crispasr_agent_transcriber.crispasr_manager.install",
        fake_install,
    )
    code = main(["--install-crispasr"])
    captured = capsys.readouterr()
    assert code == 0
    assert "CrispASR installed" in captured.out


def test_crispasr_status_not_installed(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "crispasr_agent_transcriber.crispasr_manager.find_binary",
        lambda **kw: None,
    )
    code = main(["--crispasr-status"])
    captured = capsys.readouterr()
    assert code == 0
    assert "not installed" in captured.out


def test_crispasr_status_installed(monkeypatch, capsys, tmp_path) -> None:
    exe = tmp_path / "crispasr.exe"
    exe.write_bytes(b"fake")

    monkeypatch.setattr(
        "crispasr_agent_transcriber.crispasr_manager.find_binary",
        lambda **kw: exe,
    )
    monkeypatch.setattr(
        "crispasr_agent_transcriber.crispasr_manager.check_for_update",
        lambda **kw: None,
    )
    code = main(["--crispasr-status", "--crispasr-bin-dir", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 0
    assert "Up to date" in captured.out


def test_update_crispasr_flag(monkeypatch, capsys) -> None:
    def fake_update(*, bin_dir=None):
        from pathlib import Path
        return Path("/fake/new-crispasr.exe")

    monkeypatch.setattr(
        "crispasr_agent_transcriber.crispasr_manager.update",
        fake_update,
    )
    code = main(["--update-crispasr"])
    captured = capsys.readouterr()
    assert code == 0
    assert "CrispASR updated" in captured.out