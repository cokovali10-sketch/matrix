"""Knowledge space for MATRIX."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .models import KnowledgeEntry
from .storage import Storage


class KnowledgeSpace:
    def __init__(self, storage: Storage, knowledge_dir=None):
        self.storage = storage
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir else None
        if knowledge_dir:
            self._load(knowledge_dir)

    def _load(self, knowledge_dir):
        d = Path(knowledge_dir)
        if not d.exists():
            return
        for path in sorted(d.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            # simple: title from first heading, content = rest
            lines = text.splitlines()
            title = path.stem
            content = text
            if lines and lines[0].startswith("#"):
                title = lines[0].lstrip("#").strip()
                content = "\n".join(lines[1:]).strip()
            entry = KnowledgeEntry(
                id=path.stem, title=title, content=content,
                source=str(path), kind="doc", tags=[],
                created_at=time.time(), updated_at=time.time(),
            )
            self.storage.save_knowledge(entry)

    def add(self, entry: KnowledgeEntry):
        if not entry.created_at:
            entry.created_at = time.time()
        entry.updated_at = time.time()
        self.storage.save_knowledge(entry)

    def get(self, entry_id: str) -> dict | None:
        for k in self.storage.get_knowledge():
            if k["id"] == entry_id:
                return k
        return None

    def list(self, kind=None, tag=None) -> list[dict]:
        return self.storage.get_knowledge(kind=kind, tag=tag)

    def search(self, query: str) -> list[dict]:
        return self.storage.search_knowledge(query)

    def update(self, entry_id: str, content: str):
        existing = self.get(entry_id)
        if existing:
            entry = KnowledgeEntry(
                id=existing["id"], title=existing["title"], content=content,
                source=existing["source"], kind=existing["kind"],
                tags=existing["tags"], created_at=existing["created_at"],
                updated_at=time.time(),
            )
            self.storage.save_knowledge(entry)
