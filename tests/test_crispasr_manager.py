from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from crispasr_agent_transcriber.crispasr_manager import (
    EXE_NAME,
    CrispASRRelease,
    _build_asset_candidates,
    _detect_cuda,
    _detect_vulkan,
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


class TestDetectCuda:
    def test_detects_nvidia_smi(self, monkeypatch):
        def fake_run(*args, **kwargs):
            return subprocess.CompletedProcess(args, 0, stdout="Driver Version: 550")

        monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/nvidia-smi")
        monkeypatch.setattr(subprocess, "run", fake_run)
        assert _detect_cuda() is True

    def test_detects_cuda_path_env(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda name: None)
        monkeypatch.setenv("CUDA_PATH", "C:\\cuda\\v12.4")
        assert _detect_cuda() is True

    def test_no_cuda(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda name: None)
        monkeypatch.delenv("CUDA_PATH", raising=False)
        monkeypatch.delenv("CUDA_HOME", raising=False)
        monkeypatch.setenv("PATH", "/usr/bin:/bin")
        assert _detect_cuda() is False


class TestDetectVulkan:
    def test_detects_vulkaninfo(self, monkeypatch):
        def fake_run(*args, **kwargs):
            return subprocess.CompletedProcess(args, 0, stdout="Vulkan 1.3")

        monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/vulkaninfo")
        monkeypatch.setattr(subprocess, "run", fake_run)
        assert _detect_vulkan() is True

    def test_detects_vulkan_sdk_env(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda name: None)
        monkeypatch.setenv("VULKAN_SDK", "C:\\VulkanSDK\\1.3")
        assert _detect_vulkan() is True

    def test_no_vulkan(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda name: None)
        monkeypatch.delenv("VULKAN_SDK", raising=False)
        assert _detect_vulkan() is False


class TestBuildAssetCandidates:
    def test_cuda_first_on_windows_with_gpu(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setattr("platform.system", lambda: "Windows")
        monkeypatch.setattr(
            "crispasr_agent_transcriber.crispasr_manager._detect_cuda",
            lambda: True,
        )
        monkeypatch.setattr(
            "crispasr_agent_transcriber.crispasr_manager._detect_vulkan",
            lambda: False,
        )
        candidates = _build_asset_candidates()
        assert candidates[0] == "crispasr-windows-x86_64-cuda.zip"
        assert "crispasr-windows-x86_64-cpu.zip" in candidates
        assert "crispasr-windows-x86_64-cpu-legacy.zip" in candidates

    def test_cpu_only_on_windows_without_gpu(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setattr("platform.system", lambda: "Windows")
        monkeypatch.setattr(
            "crispasr_agent_transcriber.crispasr_manager._detect_cuda",
            lambda: False,
        )
        monkeypatch.setattr(
            "crispasr_agent_transcriber.crispasr_manager._detect_vulkan",
            lambda: False,
        )
        candidates = _build_asset_candidates()
        assert candidates[0] == "crispasr-windows-x86_64-cpu.zip"

    def test_macos_returns_universal(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "darwin")
        monkeypatch.setattr("platform.system", lambda: "Darwin")
        candidates = _build_asset_candidates()
        assert candidates == ["crispasr-macos.tar.gz"]


class TestResolveAsset:
    def test_matches_first_candidate(self, monkeypatch):
        monkeypatch.setattr(
            "crispasr_agent_transcriber.crispasr_manager._build_asset_candidates",
            lambda: [
                "crispasr-windows-x86_64-cuda.zip",
                "crispasr-windows-x86_64-cpu.zip",
            ],
        )
        release = {
            "tag_name": "v0.8.0",
            "assets": [
                {
                    "name": "crispasr-windows-x86_64-cpu.zip",
                    "browser_download_url": "https://example.com/cpu.zip",
                },
                {
                    "name": "crispasr-windows-x86_64-cuda.zip",
                    "browser_download_url": "https://example.com/cuda.zip",
                },
            ],
        }
        result = _resolve_asset(release)
        assert result is not None
        assert result.asset_name == "crispasr-windows-x86_64-cuda.zip"
        assert result.version == "v0.8.0"

    def test_falls_back_when_first_missing(self, monkeypatch):
        monkeypatch.setattr(
            "crispasr_agent_transcriber.crispasr_manager._build_asset_candidates",
            lambda: [
                "crispasr-windows-x86_64-cuda.zip",
                "crispasr-windows-x86_64-cpu.zip",
            ],
        )
        release = {
            "tag_name": "v0.8.0",
            "assets": [
                {
                    "name": "crispasr-windows-x86_64-cpu.zip",
                    "browser_download_url": "https://example.com/cpu.zip",
                },
            ],
        }
        result = _resolve_asset(release)
        assert result is not None
        assert result.asset_name == "crispasr-windows-x86_64-cpu.zip"

    def test_returns_none_when_no_candidates_match(self, monkeypatch):
        monkeypatch.setattr(
            "crispasr_agent_transcriber.crispasr_manager._build_asset_candidates",
            lambda: ["crispasr-windows-x86_64-cuda.zip"],
        )
        release = {"tag_name": "v0.8.0", "assets": []}
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