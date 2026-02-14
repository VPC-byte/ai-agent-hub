"""Generic asynchronous HTTP caller tool."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib import parse, request

from ai_agent_hub.tools.base import BaseTool, ToolResult


class APICallerTool(BaseTool):
    """Call HTTP APIs with configurable method, headers, params, and JSON body."""

    name = "api_caller"
    description = "Make HTTP requests to arbitrary APIs"

    def _call_sync(
        self,
        url: str,
        method: str,
        headers: dict[str, str],
        params: dict[str, Any] | None,
        json_body: dict[str, Any] | None,
        timeout: int,
    ) -> dict[str, Any]:
        method = method.upper().strip() or "GET"
        if params:
            query = parse.urlencode(params, doseq=True)
            delimiter = "&" if "?" in url else "?"
            url = f"{url}{delimiter}{query}"

        data: bytes | None = None
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            headers = {**headers, "Content-Type": "application/json"}

        req = request.Request(url=url, data=data, method=method, headers=headers)
        with request.urlopen(req, timeout=timeout) as response:  # noqa: S310
            body_bytes = response.read()
            body_text = body_bytes.decode("utf-8", errors="replace")
            content_type = response.headers.get("Content-Type", "")
            parsed_body: Any
            if "application/json" in content_type:
                try:
                    parsed_body = json.loads(body_text)
                except json.JSONDecodeError:
                    parsed_body = body_text
            else:
                parsed_body = body_text

            return {
                "status": response.status,
                "headers": dict(response.headers.items()),
                "body": parsed_body,
                "url": response.geturl(),
            }

    async def run(self, **kwargs: Any) -> ToolResult:
        url = kwargs.get("url")
        if not url:
            return ToolResult(success=False, output=None, error="Missing 'url'")

        method = str(kwargs.get("method", "GET"))
        headers = dict(kwargs.get("headers") or {})
        params = kwargs.get("params")
        json_body = kwargs.get("json_body")
        timeout = int(kwargs.get("timeout", 10))

        try:
            output = await asyncio.to_thread(
                self._call_sync,
                str(url),
                method,
                headers,
                params,
                json_body,
                timeout,
            )
            return ToolResult(success=True, output=output)
        except Exception as exc:
            return ToolResult(success=False, output=None, error=str(exc))
