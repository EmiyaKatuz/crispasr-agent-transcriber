from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .errors import TranscriberError

BIN_DIR = Path(__file__).resolve().parents[2] / "bin"

CRISPASR_REPO = "CrispStrobe/CrispASR"
CRISPASR_RELEASES_API = f"https://api.github.com/repos/{CRISPASR_REPO}/releases"

EXE_NAME = "crispasr.exe" if sys.platform == "win32" else "crispasr"


@dataclass
class CrispASRRelease:
    version: str
    download_url: str
    asset_name: str


def _platform_key() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    if system == "darwin":
        return "darwin"
    return "linux"


def _detect_cuda() -> bool:
    if shutil.which("nvidia-smi"):
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass
    if os.environ.get("CUDA_PATH") or os.environ.get("CUDA_HOME"):
        return True
    path_lower = os.environ.get("PATH", "").lower()
    return any(
        seg in path_lower
        for seg in ("cuda\\v1", "cuda/v1", "cuda\\bin", "cuda/bin")
    )


def _detect_vulkan() -> bool:
    if shutil.which("vulkaninfo"):
        try:
            result = subprocess.run(
                ["vulkaninfo", "--summary"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass
    return bool(os.environ.get("VULKAN_SDK"))



def _build_asset_candidates() -> list[str]:
    current_platform = _platform_key()

    if current_platform == "windows":
        variants: list[str] = []
        cuda = _detect_cuda()
        vulkan = _detect_vulkan()
        if cuda:
            variants.append("crispasr-windows-x86_64-cuda.zip")
        if vulkan and not cuda:
            variants.append("crispasr-windows-x86_64-vulkan.zip")
        variants.extend([
            "crispasr-windows-x86_64-cpu.zip",
            "crispasr-windows-x86_64-cpu-legacy.zip",
        ])
        return variants

    if current_platform == "linux":
        variants = []
        cuda = _detect_cuda()
        vulkan = _detect_vulkan()
        if cuda:
            variants.extend([
                "crispasr-linux-x86_64-cuda.tar.gz",
                "crispasr-linux-x86_64-cuda13.tar.gz",
            ])
        if vulkan and not cuda:
            variants.append("crispasr-linux-x86_64-vulkan.tar.gz")
        variants.extend([
            "crispasr-linux-x86_64-avx512.tar.gz",
            "crispasr-linux-x86_64.tar.gz",
        ])
        return variants

    if current_platform == "darwin":
        return ["crispasr-macos.tar.gz"]

    return []


def _fetch_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return json.loads(response.read())
    except Exception as exc:
        raise TranscriberError(
            "Failed to fetch CrispASR release information.",
            code="crispasr_release_fetch_failed",
            details={"url": url, "error": str(exc)},
        ) from exc


def _resolve_asset(release: dict) -> CrispASRRelease | None:
    candidates = _build_asset_candidates()
    if not candidates:
        return None
    published = {a.get("name"): a for a in release.get("assets", [])}
    for name in candidates:
        asset = published.get(name)
        if asset is not None:
            return CrispASRRelease(
                version=release["tag_name"],
                download_url=asset["browser_download_url"],
                asset_name=name,
            )
    return None


def get_latest_release() -> CrispASRRelease:
    data = _fetch_json(f"{CRISPASR_RELEASES_API}/latest")
    release = _resolve_asset(data)
    if release is None:
        raise TranscriberError(
            "No pre-built CrispASR binary found for this platform.",
            code="crispasr_no_platform_binary",
            details={
                "platform": _platform_key(),
                "machine": platform.machine(),
                "candidates": _build_asset_candidates(),
            },
        )
    return release


def find_binary(*, bin_dir: Path | None = None) -> Path | None:
    bin_path = bin_dir or BIN_DIR
    local = bin_path / EXE_NAME
    if local.is_file():
        return local
    which = shutil.which(EXE_NAME)
    if which:
        return Path(which)
    return None


def _install_from_release(release: CrispASRRelease, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    ext = ".zip" if release.asset_name.endswith(".zip") else ".tar.gz"
    tmp = Path(tempfile.gettempdir()) / f"crispasr-download{ext}"
    try:
        variant_label = "CPU"
        if "cuda" in release.asset_name:
            variant_label = "CUDA"
        elif "vulkan" in release.asset_name:
            variant_label = "Vulkan"
        print(
            f"Downloading CrispASR {release.version} "
            f"({release.asset_name}) [{variant_label}] ..."
        )
        urllib.request.urlretrieve(release.download_url, str(tmp))

        print(f"Extracting to {dest} ...")
        shutil.unpack_archive(str(tmp), str(dest))

        # For tar.gz, the binary is typically inside a subfolder
        exe = dest / EXE_NAME
        if not exe.is_file():
            for candidate in dest.rglob(EXE_NAME):
                shutil.move(str(candidate), str(exe))
                break
    finally:
        if tmp.exists():
            tmp.unlink()

    if not (dest / EXE_NAME).is_file():
        raise TranscriberError(
            "CrispASR binary was not found after extraction.",
            code="crispasr_extraction_failed",
        )
    return dest / EXE_NAME


def install(*, bin_dir: Path | None = None) -> Path:
    release = get_latest_release()
    variant_label = "CPU"
    if "cuda" in release.asset_name:
        variant_label = "CUDA"
    elif "vulkan" in release.asset_name:
        variant_label = "Vulkan"
    print(f"Selected variant: {variant_label}")
    return _install_from_release(release, bin_dir or BIN_DIR)


def installed_version(*, bin_dir: Path | None = None) -> str | None:
    binary = find_binary(bin_dir=bin_dir)
    if binary is None:
        return None
    try:
        result = subprocess.run(
            [str(binary), "--version"],
            capture_output=True,
            text=True,
            shell=False,
            timeout=15,
        )
        if result.returncode == 0:
            return result.stdout.strip() or result.stderr.strip()[:60]
    except Exception:
        pass
    return "unknown"


def check_for_update(*, bin_dir: Path | None = None) -> CrispASRRelease | None:
    binary = find_binary(bin_dir=bin_dir)
    if binary is None:
        return None
    try:
        latest = get_latest_release()
    except TranscriberError:
        return None
    current = installed_version(bin_dir=bin_dir)
    if current and latest.version in (current, f"v{current}"):
        return None
    return latest


def update(*, bin_dir: Path | None = None) -> Path:
    return install(bin_dir=bin_dir)


def ensure_binary(
    *,
    bin_dir: Path | None = None,
    auto_install: bool = False,
) -> Path | None:
    binary = find_binary(bin_dir=bin_dir)
    if binary:
        return binary
    if not auto_install:
        return None
    return install(bin_dir=bin_dir)