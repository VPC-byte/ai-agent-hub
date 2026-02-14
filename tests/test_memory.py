from __future__ import annotations

import json

import pytest

from ai_agent_hub.core.memory import ChromaLongTermMemory, MemoryManager, ShortTermMemory


@pytest.mark.asyncio
async def test_long_term_memory_add_and_query(tmp_path) -> None:
    memory = ChromaLongTermMemory(persist_dir=tmp_path / "memory")

    await memory.add("Python supports async and await", metadata={"topic": "python"})
    await memory.add("FastAPI builds async APIs", metadata={"topic": "fastapi"})

    matches = await memory.query("async python", top_k=2)
    assert len(matches) == 2
    assert all(match.score >= -1.0 for match in matches)


def test_short_term_export_json_and_markdown(tmp_path) -> None:
    short = ShortTermMemory()
    short.add("user", "hello")
    short.add("assistant", "world")

    json_path = tmp_path / "history.json"
    md_path = tmp_path / "history.md"

    short.export_json(json_path)
    short.export_markdown(md_path)

    rows = json.loads(json_path.read_text(encoding="utf-8"))
    assert rows[0]["role"] == "user"
    assert "Conversation History" in md_path.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_memory_manager_export_and_recall(tmp_path) -> None:
    short = ShortTermMemory()
    long = ChromaLongTermMemory(persist_dir=tmp_path / "memory")
    manager = MemoryManager(short_term=short, long_term=long)

    manager.add_message("user", "Need notes on retries")
    await manager.add_knowledge("Retries should use exponential backoff", {"source": "docs"})

    matches = await manager.recall("exponential backoff", top_k=1)
    assert len(matches) == 1

    output = tmp_path / "session.json"
    manager.export_history(output, fmt="json")
    assert output.exists()


def test_memory_manager_invalid_export_format(tmp_path) -> None:
    short = ShortTermMemory()
    long = ChromaLongTermMemory(persist_dir=tmp_path / "memory")
    manager = MemoryManager(short_term=short, long_term=long)

    with pytest.raises(ValueError):
        manager.export_history(tmp_path / "x.bin", fmt="binary")
