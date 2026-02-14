"""DuckDuckGo web search tool."""

from __future__ import annotations

import asyncio
import html
import re
from typing import Any
from urllib import parse, request

from ai_agent_hub.tools.base import BaseTool, ToolResult


class DuckDuckGoSearchTool(BaseTool):
    """Search the web using DuckDuckGo HTML endpoint."""

    name = "web_search"
    description = "Search web results via DuckDuckGo and return sources"

    def _search_sync(self, query: str, max_results: int) -> list[dict[str, str]]:
        encoded = parse.urlencode({"q": query})
        url = f"https://duckduckgo.com/html/?{encoded}"
        req = request.Request(url, headers={"User-Agent": "ai-agent-hub/0.1"})

        with request.urlopen(req, timeout=10) as response:  # noqa: S310
            body = response.read().decode("utf-8", errors="replace")

        results: list[dict[str, str]] = []
        pattern = re.compile(
            r'<a rel="nofollow" class="result__a" href="(?P<href>[^"]+)">(?P<title>.*?)</a>',
            re.IGNORECASE | re.DOTALL,
        )
        for match in pattern.finditer(body):
            title = re.sub(r"\s+", " ", html.unescape(match.group("title"))).strip()
            href = html.unescape(match.group("href")).strip()
            results.append({"title": title, "url": href})
            if len(results) >= max_results:
                break

        return results

    async def run(self, **kwargs: Any) -> ToolResult:
        query = str(kwargs.get("query", "")).strip()
        max_results = int(kwargs.get("max_results", 5))
        timeout_seconds = float(kwargs.get("timeout", 6.0))
        if not query:
            return ToolResult(success=False, output=None, error="Missing 'query'")

        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(self._search_sync, query, max_results),
                timeout=timeout_seconds,
            )
            return ToolResult(success=True, output=results, metadata={"query": query})
        except Exception as exc:
            return ToolResult(success=False, output=None, error=str(exc), metadata={"query": query})
