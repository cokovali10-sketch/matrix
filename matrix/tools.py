"""Tool registry for MATRIX."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Tool


class ToolRegistry:
    def __init__(self, tools_dir=None, storage=None):
        self.tools_dir = Path(tools_dir) if tools_dir else None
        self.storage = storage
        self.tools: dict[str, Tool] = {}
        self.usage: dict[str, int] = {}
        if tools_dir:
            self._load(tools_dir)

    def record_usage(self, tool_id: str):
        self.usage[tool_id] = self.usage.get(tool_id, 0) + 1

    def recommend(self, task_description: str, limit: int = 5) -> list[Tool]:
        q = task_description.lower()
        scored = []
        for t in self.tools.values():
            haystack = " ".join([t.id, t.name, t.description] + t.tags).lower()
            score = sum(1 for w in q.split() if w in haystack)
            score += self.usage.get(t.id, 0) * 0.1
            if score > 0:
                scored.append((score, t))
        scored.sort(key=lambda x: -x[0])
        return [t for _, t in scored[:limit]]

    def chain(self, tool_ids: list[str], initial_input: Any = None) -> list[Any]:
        """Execute a sequence of tools, passing output of one as input to next."""
        results = [initial_input]
        for tid in tool_ids:
            tool = self.get(tid)
            if tool is None:
                results.append({"error": f"unknown tool {tid}"})
                break
            self.record_usage(tid)
            results.append({"tool": tid, "input": results[-1]})
        return results


    def _load(self, tools_dir):
        d = Path(tools_dir)
        if not d.exists():
            return
        for path in sorted(d.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            tool = Tool(
                id=data.get("id", path.stem),
                name=data.get("name", path.stem),
                description=data.get("description", ""),
                input_schema=data.get("input_schema", {}),
                output_schema=data.get("output_schema", {}),
                safety=data.get("safety", []),
                example=data.get("example", ""),
                tags=data.get("tags", []),
            )
            self.tools[tool.id] = tool

    def register(self, tool: Tool):
        self.tools[tool.id] = tool

    def get(self, tool_id: str) -> Tool | None:
        return self.tools.get(tool_id)

    def list(self, tag=None) -> list[Tool]:
        if tag:
            return [t for t in self.tools.values() if tag in t.tags]
        return list(self.tools.values())

    def search(self, query: str) -> list[Tool]:
        q = query.lower()
        return [t for t in self.tools.values() if q in t.id.lower() or q in t.name.lower() or q in t.description.lower() or any(q in tag for tag in t.tags)]

    def as_dicts(self) -> list[dict]:
        return [t.as_dict() for t in self.tools.values()]
