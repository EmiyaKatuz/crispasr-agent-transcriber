from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

PLUGIN_NAME = "crispasr-agent-transcriber"
PLUGIN_ENTRIES = (
    ".codex-plugin",
    ".mcp.json",
    "AGENTS.md",
    "LICENSE",
    "README.md",
    "assets",
    "docs",
    "mcp_server",
    "pyproject.toml",
    "scripts",
    "skills",
    "src",
    "uv.lock",
)
IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def _iter_bundle_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for entry in PLUGIN_ENTRIES:
        path = root / entry
        if path.is_file():
            files.append(path)
            continue
        if path.is_dir():
            for candidate in path.rglob("*"):
                if not candidate.is_file():
                    continue
                relative = candidate.relative_to(root)
                if any(part in IGNORED_PARTS for part in relative.parts):
                    continue
                if candidate.suffix.lower() in IGNORED_SUFFIXES:
                    continue
                files.append(candidate)
    return sorted(set(files), key=lambda item: item.as_posix())


def build_bundle(root: Path, output_dir: Path) -> Path:
    manifest_path = root / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("name") != PLUGIN_NAME:
        raise ValueError("Plugin manifest name does not match the bundle name.")
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("Plugin manifest version is missing.")

    required = {
        manifest_path,
        root / ".mcp.json",
        root / "skills" / "crispasr-transcription" / "SKILL.md",
        root / "pyproject.toml",
    }
    missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required plugin files: {', '.join(missing)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{PLUGIN_NAME}-plugin-{version}.zip"
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source_path in _iter_bundle_files(root):
            relative = source_path.relative_to(root).as_posix()
            archive_path = f"{PLUGIN_NAME}/{relative}"
            info = zipfile.ZipInfo(archive_path, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source_path.read_bytes())
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Codex plugin ZIP bundle.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: <repository>/dist).",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output_dir = args.output_dir.resolve() if args.output_dir else root / "dist"
    output_path = build_bundle(root, output_dir)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
