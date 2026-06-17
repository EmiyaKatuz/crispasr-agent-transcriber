from __future__ import annotations

from . import tools

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - exercised only without mcp extra.
    raise SystemExit("Install with the MCP extra first: uv sync --extra mcp") from exc

mcp = FastMCP("crispasr-agent-transcriber")

mcp.tool()(tools.crispasr_health)
mcp.tool()(tools.crispasr_backends)
mcp.tool()(tools.crispasr_detect_language)
mcp.tool()(tools.transcribe_audio)
mcp.tool()(tools.transcribe_video)
mcp.tool()(tools.transcribe_folder)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
