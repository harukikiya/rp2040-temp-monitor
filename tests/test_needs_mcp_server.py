"""needs_mcp_server.py のテスト - MCP プロトコル越しにツールを呼ぶ。

Client にサーバーのインスタンスを渡すと、プロセスを起動せずメモリ上で接続できる。
Claude Code と同じ流れ（ツール一覧の取得 → 呼び出し）を、JSON-RPC の往復込みで確かめる。
"""
from __future__ import annotations

from pathlib import Path

import pytest
from mcp.client import Client
from mcp.server.mcpserver import MCPServer

from needs_mcp_server import build_server

FIXTURE: Path = Path(__file__).parent / "fixtures" / "needs_mini.json"

pytestmark = pytest.mark.anyio

@pytest.fixture
def anyio_backend() -> str:
    """非同期テストを asyncio で動かす（指定しないと trio でも走る）。"""
    return "asyncio"

@pytest.fixture
def server() -> MCPServer:
    """fixture の needs.json を読むサーバー。鮮度チェックはしない。"""
    return build_server(FIXTURE)

async def test_four_read_only_tools_are_listed(server: MCPServer) -> None:
    async with Client(server) as client:
        result = await client.list_tools()
    assert {t.name for t in result.tools} == {
        "get_need", "search_needs", "trace", "status_report",
    }
    assert all(t.annotations and t.annotations.read_only_hint for t in result.tools)

async def test_literal_becomes_enum_in_input_schema(server: MCPServer) -> None:
    async with Client(server) as client:
        result = await client.list_tools()
    search = next(t for t in result.tools if t.name == "search_needs")
    need_type = search.input_schema["properties"]["need_type"]
    assert {"enum": ["sysreq", "arc", "swreq", "swverif"], "type": "string"} in need_type["anyOf"]

async def test_get_need_returns_structured_content(server: MCPServer) -> None:
    async with Client(server) as client:
        result = await client.call_tool("get_need", {"need_id": "SWR_001"})
    assert not result.is_error
    assert result.structured_content is not None
    assert result.structured_content["source"] == "docs/common/20_software_requirements.md:12"

async def test_unknown_id_reaches_the_model_as_tool_error(server: MCPServer) -> None:
    async with Client(server) as client:
        result = await client.call_tool("get_need", {"need_id": "SWR_004"})
    assert result.is_error
    assert "近い ID: SWR_003" in result.content[0].text

async def test_invalid_enum_is_rejected_before_the_tool_runs(server: MCPServer) -> None:
    async with Client(server) as client:
        result = await client.call_tool("search_needs", {"need_type": "swr"})
    assert result.is_error
    assert "swverif" in result.content[0].text
