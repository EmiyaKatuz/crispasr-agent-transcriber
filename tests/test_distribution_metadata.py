import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_distribution_versions_and_registry_metadata_match() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    plugin = json.loads(
        (ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    registry = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    npm_package = json.loads(
        (ROOT / "npm" / "package.json").read_text(encoding="utf-8")
    )

    version = project["project"]["version"]
    assert plugin["version"] == version
    assert registry["version"] == version
    assert registry["packages"][0]["version"] == version
    assert npm_package["version"] == version
    assert npm_package["name"] == "@emiyakatuz/crispasr-agent-transcriber"
    assert (
        npm_package["bin"]["crispasr-agent-transcriber"]
        == "bin/crispasr-agent-transcriber.js"
    )
    assert (
        project["project"]["scripts"]["crispasr-agent-transcriber"]
        == "crispasr_mcp.server:main"
    )


def test_readme_contains_mcp_registry_ownership_marker() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8-sig")
    assert (
        "<!-- mcp-name: io.github.emiyakatuz/crispasr-agent-transcriber -->"
        in readme
    )
