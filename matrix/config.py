"""Configuration for MATRIX."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StorageConfig:
    db_path: str = "matrix.db"
    knowledge_dir: str = "knowledge"
    tasks_dir: str = "tasks"
    tools_dir: str = "tools"


@dataclass
class SimulationConfig:
    enabled: bool = True
    use_git_worktree: bool = True
    use_docker: bool = False
    timeout_seconds: int = 120
    sandbox_dir: str = ".matrix_sandbox"


@dataclass
class EvaluationConfig:
    pass_threshold: float = 1.0
    max_attempts: int = 3
    track_tokens: bool = True
    track_latency: bool = True


@dataclass
class AgentConfig:
    default_role: str = "developer"
    roles: list[str] = field(default_factory=lambda: [
        "architect", "developer", "debugger", "tester",
        "researcher", "security", "reviewer",
    ])


@dataclass
class MatrixConfig:
    project: str = "default"
    storage: StorageConfig = field(default_factory=StorageConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    @classmethod
    def load(cls, path=None) -> "MatrixConfig":
        data = {}
        if path and Path(path).exists():
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        elif Path("matrix.json").exists():
            data = json.loads(Path("matrix.json").read_text(encoding="utf-8"))
        config = cls()
        for key, value in data.items():
            if not hasattr(config, key):
                continue
            current = getattr(config, key)
            if isinstance(current, (StorageConfig, SimulationConfig, EvaluationConfig, AgentConfig)):
                setattr(config, key, type(current)(**value))
            else:
                setattr(config, key, value)
        # env overrides
        if os.environ.get("MATRIX_DB"):
            config.storage.db_path = os.environ["MATRIX_DB"]
        if os.environ.get("MATRIX_PROJECT"):
            config.project = os.environ["MATRIX_PROJECT"]
        return config

    def dump(self) -> dict:
        return asdict(self)

    def save(self, path):
        Path(path).write_text(json.dumps(self.dump(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
