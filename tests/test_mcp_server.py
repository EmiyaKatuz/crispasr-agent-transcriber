from __future__ import annotations

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_mcp_server_initializes_and_lists_tools() -> None:
    async def run_session() -> set[str]:
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "crispasr_mcp.server"],
        )
        async with (
            stdio_client(parameters) as (read_stream, write_stream),
            ClientSession(read_stream, write_stream) as session,
        ):
            await session.initialize()
            result = await session.list_tools()
            return {tool.name for tool in result.tools}

    tool_names = asyncio.run(run_session())
    assert tool_names == {
        "crispasr_health",
        "crispasr_backends",
        "crispasr_detect_language",
        "crispasr_list_models",
        "crispasr_download_models",
        "crispasr_resolve_model_paths",
        "transcribe_audio",
        "transcribe_video",
        "understand_video",
        "transcribe_folder",
    }
