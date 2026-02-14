from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from ai_agent_hub.tools.api_caller import APICallerTool
from ai_agent_hub.tools.calculator import CalculatorTool
from ai_agent_hub.tools.file_tools import FileReaderTool, FileWriterTool
from ai_agent_hub.tools.python_executor import PythonExecutorTool
from ai_agent_hub.tools.web_search import DuckDuckGoSearchTool


@pytest.mark.asyncio
async def test_calculator_tool_success_and_failure() -> None:
    tool = CalculatorTool()

    ok = await tool.run(expression="2 + 3 * 4")
    assert ok.success is True
    assert ok.output == 14.0

    bad = await tool.run(expression="__import__('os').system('echo hi')")
    assert bad.success is False


@pytest.mark.asyncio
async def test_file_reader_writer_tools(tmp_path) -> None:
    writer = FileWriterTool(workspace=tmp_path)
    reader = FileReaderTool(workspace=tmp_path)

    write_result = await writer.run(path="notes/test.txt", content="hello")
    assert write_result.success is True

    read_result = await reader.run(path="notes/test.txt")
    assert read_result.success is True
    assert read_result.output == "hello"


@pytest.mark.asyncio
async def test_python_executor_blocks_import() -> None:
    tool = PythonExecutorTool()

    ok = await tool.run(code="x = 3\nprint(x)")
    assert ok.success is True
    assert "3" in ok.output["stdout"]

    blocked = await tool.run(code="import os\nprint('x')")
    assert blocked.success is False
    assert "not allowed" in (blocked.error or "")


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = json.dumps({"status": "ok"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A003
        return


@pytest.mark.asyncio
async def test_api_caller_tool_local_server() -> None:
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        port = server.server_address[1]
        tool = APICallerTool()
        result = await tool.run(url=f"http://127.0.0.1:{port}/health", method="GET")
        assert result.success is True
        assert result.output["status"] == 200
        assert result.output["body"]["status"] == "ok"
    finally:
        server.shutdown()
        thread.join(timeout=2)


@pytest.mark.asyncio
async def test_web_search_validation_and_mock(monkeypatch) -> None:
    tool = DuckDuckGoSearchTool()

    missing = await tool.run()
    assert missing.success is False

    async def _patched_run(**kwargs):
        return kwargs

    def _fake_search(query: str, max_results: int):
        return [{"title": "Result", "url": "https://example.com"}]

    monkeypatch.setattr(tool, "_search_sync", _fake_search)
    result = await tool.run(query="agentic ai", max_results=1)
    assert result.success is True
    assert result.output[0]["url"] == "https://example.com"
