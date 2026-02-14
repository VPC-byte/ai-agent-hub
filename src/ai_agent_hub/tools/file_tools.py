"""File reader and writer tools."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from ai_agent_hub.tools.base import BaseTool, ToolResult


class FileReaderTool(BaseTool):
    """Read text files from disk."""

    name = "file_reader"
    description = "Read text content from a file path"

    def __init__(self, workspace: Path | None = None) -> None:
        self.workspace = workspace or Path.cwd()

    def _resolve(self, path: str) -> Path:
        resolved = (self.workspace / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
        return resolved

    async def run(self, **kwargs: Any) -> ToolResult:
        path = kwargs.get("path")
        if not path:
            return ToolResult(success=False, output=None, error="Missing 'path'")

        file_path = self._resolve(str(path))
        try:
            content = await asyncio.to_thread(file_path.read_text, encoding="utf-8")
            return ToolResult(success=True, output=content, metadata={"path": str(file_path)})
        except Exception as exc:
            return ToolResult(success=False, output=None, error=str(exc), metadata={"path": str(file_path)})


class FileWriterTool(BaseTool):
    """Write text files to disk."""

    name = "file_writer"
    description = "Write text content to a file path"

    def __init__(self, workspace: Path | None = None) -> None:
        self.workspace = workspace or Path.cwd()

    def _resolve(self, path: str) -> Path:
        resolved = (self.workspace / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
        return resolved

    async def run(self, **kwargs: Any) -> ToolResult:
        path = kwargs.get("path")
        content = kwargs.get("content")
        append = bool(kwargs.get("append", False))

        if not path:
            return ToolResult(success=False, output=None, error="Missing 'path'")
        if content is None:
            return ToolResult(success=False, output=None, error="Missing 'content'")

        file_path = self._resolve(str(path))
        mode = "a" if append else "w"

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            def _write() -> int:
                with file_path.open(mode, encoding="utf-8") as handle:
                    written = handle.write(str(content))
                return written

            chars_written = await asyncio.to_thread(_write)
            return ToolResult(
                success=True,
                output={"chars_written": chars_written, "path": str(file_path)},
            )
        except Exception as exc:
            return ToolResult(success=False, output=None, error=str(exc), metadata={"path": str(file_path)})
