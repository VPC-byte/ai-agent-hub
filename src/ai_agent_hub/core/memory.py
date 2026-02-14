"""Short-term and long-term memory implementations."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ai_agent_hub.core.models import Message


@dataclass(slots=True)
class MemoryMatch:
    """A long-term memory retrieval result."""

    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class ShortTermMemory:
    """Conversation-focused in-memory message store."""

    def __init__(self) -> None:
        self._messages: list[Message] = []

    def add(self, role: str, content: str) -> Message:
        """Store one conversation message."""
        message = Message(role=role, content=content)
        self._messages.append(message)
        return message

    def history(self) -> list[Message]:
        """Return message history as a copy."""
        return list(self._messages)

    def clear(self) -> None:
        """Clear all short-term messages."""
        self._messages.clear()

    def export_json(self, output_path: Path) -> None:
        """Export message history to JSON file."""
        rows = [asdict(message) for message in self._messages]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    def export_markdown(self, output_path: Path) -> None:
        """Export conversation to Markdown transcript."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# Conversation History", ""]
        for message in self._messages:
            lines.append(f"## {message.role.title()} ({message.timestamp})")
            lines.append("")
            lines.append(message.content)
            lines.append("")
        output_path.write_text("\n".join(lines), encoding="utf-8")


class ChromaLongTermMemory:
    """Long-term semantic memory using ChromaDB with a deterministic embedding fallback."""

    def __init__(self, persist_dir: Path, collection_name: str = "agent_knowledge") -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._persist_dir = persist_dir
        self._collection_name = collection_name
        self._memory_fallback: list[tuple[str, list[float], dict[str, Any]]] = []
        self._chroma_collection: Any | None = None
        self._initialize_chroma()

    def _initialize_chroma(self) -> None:
        """Initialize ChromaDB collection if dependency is available."""
        try:
            import chromadb  # type: ignore[import-not-found]

            self._persist_dir.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(self._persist_dir))
            self._chroma_collection = client.get_or_create_collection(name=self._collection_name)
        except Exception as exc:  # pragma: no cover - env dependent
            self._logger.warning("ChromaDB unavailable, using in-memory fallback: %s", exc)
            self._chroma_collection = None

    @staticmethod
    def _embed(text: str, dims: int = 64) -> list[float]:
        """Generate deterministic lightweight embedding vector from text."""
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for idx in range(dims):
            byte = digest[idx % len(digest)]
            values.append((byte / 255.0) * 2.0 - 1.0)
        return values

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity score."""
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _add_sync(self, text: str, metadata: dict[str, Any] | None = None) -> str:
        doc_id = str(uuid.uuid4())
        metadata = metadata or {}
        embedding = self._embed(text)

        if self._chroma_collection is not None:
            self._chroma_collection.add(
                ids=[doc_id],
                documents=[text],
                metadatas=[metadata],
                embeddings=[embedding],
            )
        else:
            self._memory_fallback.append((text, embedding, metadata))
        return doc_id

    async def add(self, text: str, metadata: dict[str, Any] | None = None) -> str:
        """Add one document to long-term memory."""
        return await asyncio.to_thread(self._add_sync, text, metadata)

    def _query_sync(self, query_text: str, top_k: int = 3) -> list[MemoryMatch]:
        query_embedding = self._embed(query_text)

        if self._chroma_collection is not None:
            result = self._chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "distances", "metadatas"],
            )
            docs = result.get("documents", [[]])[0]
            distances = result.get("distances", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            matches: list[MemoryMatch] = []
            for text, distance, metadata in zip(docs, distances, metadatas, strict=False):
                # Chroma distance is lower-is-better; convert to score where higher is better.
                score = 1.0 / (1.0 + float(distance))
                matches.append(MemoryMatch(text=text, score=score, metadata=metadata or {}))
            return matches

        matches = [
            MemoryMatch(text=text, score=self._cosine_similarity(query_embedding, emb), metadata=metadata)
            for text, emb, metadata in self._memory_fallback
        ]
        return sorted(matches, key=lambda item: item.score, reverse=True)[:top_k]

    async def query(self, query_text: str, top_k: int = 3) -> list[MemoryMatch]:
        """Retrieve semantically relevant memory matches."""
        return await asyncio.to_thread(self._query_sync, query_text, top_k)


class MemoryManager:
    """Unified memory facade for short-term and long-term memory."""

    def __init__(self, short_term: ShortTermMemory, long_term: ChromaLongTermMemory) -> None:
        self.short_term = short_term
        self.long_term = long_term

    def add_message(self, role: str, content: str) -> Message:
        """Append one message to short-term memory."""
        return self.short_term.add(role=role, content=content)

    async def add_knowledge(self, text: str, metadata: dict[str, Any] | None = None) -> str:
        """Store durable knowledge in long-term memory."""
        return await self.long_term.add(text=text, metadata=metadata)

    async def recall(self, query_text: str, top_k: int = 3) -> list[MemoryMatch]:
        """Query long-term memory."""
        return await self.long_term.query(query_text=query_text, top_k=top_k)

    def export_history(self, output_path: Path, fmt: str = "json") -> None:
        """Export short-term memory history in JSON or Markdown format."""
        fmt_normalized = fmt.lower().strip()
        if fmt_normalized == "json":
            self.short_term.export_json(output_path)
            return
        if fmt_normalized in {"md", "markdown"}:
            self.short_term.export_markdown(output_path)
            return
        raise ValueError(f"Unsupported export format: {fmt}")
