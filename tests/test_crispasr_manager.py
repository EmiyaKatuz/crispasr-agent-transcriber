from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from crispasr_agent_transcriber.crispasr_manager import (
    EXE_NAME,
    CrispASRRelease,
    _platform_key,
    _resolve_asset,
    check_for_update,
    ensure_binary,
    find_binary,
    update,
)


class TestPlatformKey:
    def test_platform_key_windows(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setattr("platform.system", lambda: "Windows")
        assert _platform_key() == "windows"

    def test_platform_key_darwin(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "darwin")
        monkeypatch.setattr("platform.system", lambda: "Darwin")
        assert _platform_key() == "darwin"

    def test_platform_key_linux(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.setattr("platform.system", lambda: "Linux")
        assert _platform_key() == "linux"


class TestResolveAsset:
    def test_resolves_windows_x86_64(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setattr("platform.system", lambda: "Windows")
        monkeypatch.setattr("platform.machine", lambda: "AMD64")
        release = {
            "tag_name": "v0.8.0",
            "assets": [
                {
                    "name": "crispasr-windows-x86_64-cpu.zip",
                    "browser_download_url": "https://example.com/crispasr-windows.zip",
                },
            ],
        }
        result = _resolve_asset(release)
        assert result is not None
        assert result.version == "v0.8.0"
        assert result.asset_name == "crispasr-windows-x86_64-cpu.zip"

    def test_returns_none_for_unknown_platform(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "freebsd")
        monkeypatch.setattr("platform.system", lambda: "FreeBSD")
        monkeypatch.setattr("platform.machine", lambda: "x86_64")
        release = {"tag_name": "v0.8.0", "assets": []}
        assert _resolve_asset(release) is None

    def test_returns_none_when_asset_not_in_release(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setattr("platform.system", lambda: "Windows")
        monkeypatch.setattr("platform.machine", lambda: "AMD64")
        release = {
            "tag_name": "v0.8.0",
            "assets": [{"name": "wrong-file.tar.gz"}],
        }
        assert _resolve_asset(release) is None


class TestFindBinary:
    def test_finds_on_path(self, tmp_path, monkeypatch):
        exe = tmp_path / EXE_NAME
        exe.write_bytes(b"fake")
        monkeypatch.setattr(
            "shutil.which",
            lambda name, **kw: str(exe) if name == EXE_NAME else None,
        )
        result = find_binary(bin_dir=tmp_path / "nonexistent")
        assert result is not None
        assert str(result) == str(exe)

    def test_finds_in_bin_dir(self, tmp_path):
        exe = tmp_path / EXE_NAME
        exe.write_bytes(b"fake")
        result = find_binary(bin_dir=tmp_path)
        assert result == exe

    def test_returns_none_when_missing(self, tmp_path):
        assert find_binary(bin_dir=tmp_path) is None


class TestEnsureBinary:
    def test_returns_existing_without_install(self, tmp_path):
        exe = tmp_path / EXE_NAME
        exe.write_bytes(b"fake")
        result = ensure_binary(bin_dir=tmp_path, auto_install=False)
        assert result == exe

    def test_returns_none_when_missing_and_no_auto_install(self, tmp_path):
        result = ensure_binary(bin_dir=tmp_path, auto_install=False)
        assert result is None

    def test_auto_installs_when_missing(self, tmp_path, monkeypatch):
        exe = tmp_path / EXE_NAME

        def fake_install(*, bin_dir=None):
            exe.write_bytes(b"fake")
            return exe

        monkeypatch.setattr(
            "crispasr_agent_transcriber.crispasr_manager.install",
            fake_install,
        )
        result = ensure_binary(bin_dir=tmp_path, auto_install=True)
        assert result == exe


class TestCheckForUpdate:
    def test_no_update_when_not_installed(self, tmp_path):
        result = check_for_update(bin_dir=tmp_path)
        assert result is None

    def test_no_update_when_same_version(self, tmp_path, monkeypatch):
        exe = tmp_path / EXE_NAME
        exe.write_bytes(b"fake")

        def fake_run(*args, **kwargs):
            return subprocess.CompletedProcess(args, 0, stdout="v0.8.0")

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(
            "crispasr_agent_transcriber.crispasr_manager.get_latest_release",
            lambda: CrispASRRelease("v0.8.0", "", ""),
        )
        result = check_for_update(bin_dir=tmp_path)
        assert result is None

    def test_update_available(self, tmp_path, monkeypatch):
        exe = tmp_path / EXE_NAME
        exe.write_bytes(b"fake")

        def fake_run(*args, **kwargs):
            return subprocess.CompletedProcess(args, 0, stdout="v0.7.0")

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(
            "crispasr_agent_transcriber.crispasr_manager.get_latest_release",
            lambda: CrispASRRelease(
                "v0.8.0", "https://example.com/dl", "asset.zip"
            ),
        )
        result = check_for_update(bin_dir=tmp_path)
        assert result is not None
        assert result.version == "v0.8.0"


class TestUpdate:
    def test_calls_install(self, monkeypatch):
        called_with = []

        def fake_install(*, bin_dir=None):
            called_with.append(bin_dir)
            return Path("/fake/crispasr.exe")

        monkeypatch.setattr(
            "crispasr_agent_transcriber.crispasr_manager.install",
            fake_install,
        )
        result = update(bin_dir=Path("/custom"))
        assert result == Path("/fake/crispasr.exe")
        assert called_with == [Path("/custom")]