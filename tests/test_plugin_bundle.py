from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path


def test_build_plugin_bundle(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_plugin_bundle.py"),
            "--output-dir",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )

    bundle = tmp_path / f"crispasr-agent-transcriber-plugin-{manifest['version']}.zip"
    assert bundle.is_file()
    with zipfile.ZipFile(bundle) as archive:
        names = set(archive.namelist())

    prefix = "crispasr-agent-transcriber/"
    assert prefix + ".codex-plugin/plugin.json" in names
    assert prefix + ".mcp.json" in names
    assert prefix + "skills/crispasr-transcription/SKILL.md" in names
    assert prefix + "mcp_server/crispasr_mcp/server.py" in names
    assert not any("models/" in name for name in names)
    assert not any("bin/" in name for name in names)
