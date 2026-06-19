# Release Notes

## Release checklist

- Package installs with `uv sync --extra dev --extra mcp`.
- Tests pass with generated media fixtures.
- README explains local model paths and the no-default-download rule.
- English uses Cohere.
- Chinese uses Qwen3-ASR 1.7B.
- MCP tools are available behind the optional dependency.
- Plugin and package versions report the same semantic version.
- The npm installer reports the same version and passes `npm test`.
- Plugin validation and Skill validation pass.
- `scripts/build_plugin_bundle.py` creates the Codex plugin ZIP.
- The release ZIP is listed in `SHA256SUMS`.

Tag:

```powershell
git tag v0.3.2
git push origin v0.3.2
```

The Release workflow builds and uploads:

- Python wheel
- Python source distribution
- Codex plugin ZIP
- SHA-256 checksums

After the Release workflow succeeds, run the **Publish npm installer** workflow.
It publishes `@emiyakatuz/crispasr-agent-transcriber` only after confirming the
matching plugin ZIP and checksum assets exist.

For cross-agent installation, publish the same Python version to PyPI or use
the tagged GitHub source with the `uvx` command in
`docs/agent_integrations.md`.
