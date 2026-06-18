# Release Notes

## v0.3 checklist

- Package installs with `uv sync --extra dev --extra mcp`.
- Tests pass with generated media fixtures.
- README explains local model paths and the no-default-download rule.
- English uses Cohere.
- Chinese uses Qwen3-ASR 1.7B.
- MCP tools are available behind the optional dependency.
- Plugin and package versions both report `0.3.0`.
- Plugin validation and Skill validation pass.

Tag:

```powershell
git tag v0.3.0
git push origin v0.3.0
```
