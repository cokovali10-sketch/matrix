"""Plugin system for MATRIX (Phase 5)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


class PluginManager:
    def __init__(self, plugins_dir=None):
        self.plugins_dir = Path(plugins_dir) if plugins_dir else None
        self.plugins: dict[str, Any] = {}
        if plugins_dir:
            self.load_all(plugins_dir)

    def load_all(self, plugins_dir):
        d = Path(plugins_dir)
        if not d.exists():
            return
        for path in sorted(d.glob("*.py")):
            self.load(path)

    def load(self, path):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception:
            return None
        register = getattr(mod, "register", None)
        if callable(register):
            self.plugins[path.stem] = register
        return mod

    def run(self, name: str, *args, **kwargs):
        if name in self.plugins:
            return self.plugins[name](*args, **kwargs)
        raise KeyError(f"plugin not found: {name}")

    def list(self) -> list[str]:
        return sorted(self.plugins.keys())
