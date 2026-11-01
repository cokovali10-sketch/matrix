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
        if tools_dir:
            self._load(tools_dir)

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
