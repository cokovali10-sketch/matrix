"""Memory space for MATRIX."""

from __future__ import annotations

import time
import uuid
from typing import Any

from .models import MemoryFact
from .storage import Storage


class MemorySpace:
    def __init__(self, storage: Storage):
        self.storage = storage

    def add(self, fact: str, kind: str = "fact", source: str = "", confidence: float = 1.0,
            tags: list[str] = None, verified: bool = False, ttl_days: float = 0) -> MemoryFact:
        fid = f"mem-{uuid.uuid4().hex[:8]}"
        now = time.time()
        expires = now + ttl_days * 86400 if ttl_days > 0 else 0.0
        entry = MemoryFact(
            id=fid, fact=fact, kind=kind, source=source, confidence=confidence,
            created_at=now, expires_at=expires, tags=tags or [], verified=verified,
        )
        self.storage.save_memory(entry)
        return entry

    def get(self, kind=None, tag=None) -> list[dict]:
        return self.storage.get_memory(kind=kind, tag=tag)

    def facts(self) -> list[dict]:
        return self.storage.get_memory(kind="fact")

    def assumptions(self) -> list[dict]:
        return self.storage.get_memory(kind="assumption")

    def stale(self) -> list[dict]:
        now = time.time()
        all_facts = self.storage.get_memory()
        return [f for f in all_facts if f["expires_at"] > 0 and f["expires_at"] < now]

    def search(self, query: str) -> list[dict]:
        q = query.lower()
        return [f for f in self.storage.get_memory() if q in f["fact"].lower() or any(q in t for t in f["tags"])]

    def verify(self, fact_id: str, verified: bool = True):
        facts = self.storage.get_memory()
        for f in facts:
            if f["id"] == fact_id:
                entry = MemoryFact(
                    id=f["id"], fact=f["fact"], kind=f["kind"], source=f["source"],
                    confidence=f["confidence"], created_at=f["created_at"],
                    expires_at=f["expires_at"], tags=f["tags"], verified=verified,
                )
                self.storage.save_memory(entry)
                return entry
        return None

    def remove(self, fact_id: str):
        self.storage.delete_memory(fact_id)

    def stats(self) -> dict:
        all_facts = self.storage.get_memory()
        return {
            "total": len(all_facts),
            "facts": sum(1 for f in all_facts if f["kind"] == "fact"),
            "assumptions": sum(1 for f in all_facts if f["kind"] == "assumption"),
            "stale": sum(1 for f in all_facts if f["expires_at"] > 0 and f["expires_at"] < time.time()),
            "verified": sum(1 for f in all_facts if f["verified"]),
        }
