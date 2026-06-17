from __future__ import annotations

import json
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

PLATFORM_ASSETS: dict[str, dict[str, list[str]]] = {
    "windows": {
        "AMD64": [
            "crispasr-windows-x86_64-cpu.zip",
            "crispasr-windows-x86_64-cuda.zip",
            "crispasr-windows-x86_64-vulkan.zip",
            "crispasr-windows-x86_64-cpu-legacy.zip",
        ],
        "x86_64": [
            "crispasr-windows-x86_64-cpu.zip",
            "crispasr-windows-x86_64-cuda.zip",
            "crispasr-windows-x86_64-vulkan.zip",
            "crispasr-windows-x86_64-cpu-legacy.zip",
        ],
    },
    "darwin": {
        "arm64": ["crispasr-macos.tar.gz"],
        "aarch64": ["crispasr-macos.tar.gz"],
    },
    "linux": {
        "x86_64": ["crispasr-linux-x86_64.tar.gz"],
        "AMD64": ["crispasr-linux-x86_64.tar.gz"],
        "aarch64": ["crispasr-linux-arm64.tar.gz"],
        "arm64": ["crispasr-linux-arm64.tar.gz"],
    },
}

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
    current_platform = _platform_key()
    machine = platform.machine()
    candidates = PLATFORM_ASSETS.get(current_platform, {})
    candidate_names = candidates.get(machine, [])
    if not candidate_names:
        return None
    published = {a.get("name"): a for a in release.get("assets", [])}
    for name in candidate_names:
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
            details={"platform": _platform_key(), "machine": platform.machine()},
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
        print(f"Downloading CrispASR {release.version} ({release.asset_name}) ...")
        urllib.request.urlretrieve(release.download_url, str(tmp))

        print(f"Extracting to {dest} ...")
        if ext == ".zip":
            shutil.unpack_archive(str(tmp), str(dest))
        else:
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
