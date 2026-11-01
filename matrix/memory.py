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

    def consolidate(self) -> int:
        """Merge near-duplicate facts (same lowercased text) keeping highest confidence."""
        facts = self.storage.get_memory()
        seen = {}
        removed = 0
        for f in facts:
            key = f["fact"].strip().lower()
            if key in seen:
                prev = seen[key]
                if f["confidence"] > prev["confidence"]:
                    self.storage.delete_memory(prev["id"])
                    seen[key] = f
                else:
                    self.storage.delete_memory(f["id"])
                removed += 1
            else:
                seen[key] = f
        return removed

    def decay(self, half_life_days: float = 30.0) -> int:
        """Reduce confidence of facts not verified; remove if below 0.1."""
        import math
        now = time.time()
        facts = self.storage.get_memory()
        removed = 0
        for f in facts:
            age_days = (now - f["created_at"]) / 86400.0
            if f["verified"]:
                continue
            new_conf = f["confidence"] * math.pow(0.5, age_days / half_life_days)
            if new_conf < 0.1:
                self.storage.delete_memory(f["id"])
                removed += 1
            else:
                entry = MemoryFact(
                    id=f["id"], fact=f["fact"], kind=f["kind"], source=f["source"],
                    confidence=new_conf, created_at=f["created_at"],
                    expires_at=f["expires_at"], tags=f["tags"], verified=f["verified"],
                )
                self.storage.save_memory(entry)
        return removed

    def prioritize(self, limit: int = 10) -> list[dict]:
        """Return top facts by confidence then recency."""
        facts = self.storage.get_memory()
        facts.sort(key=lambda f: (-f["confidence"], -f["created_at"]))
        return facts[:limit]

    def stats(self) -> dict:
        all_facts = self.storage.get_memory()
        return {
            "total": len(all_facts),
            "facts": sum(1 for f in all_facts if f["kind"] == "fact"),
            "assumptions": sum(1 for f in all_facts if f["kind"] == "assumption"),
            "stale": sum(1 for f in all_facts if f["expires_at"] > 0 and f["expires_at"] < time.time()),
            "verified": sum(1 for f in all_facts if f["verified"]),
        }
