"""Main MATRIX orchestrator."""

from __future__ import annotations

from .agents import AgentSpace
from .config import MatrixConfig
from .evaluation import Evaluator
from .knowledge import KnowledgeSpace
from .learning import LearningLoop
from .memory import MemorySpace
from .models import AgentRole, KnowledgeEntry, MemoryFact, Task
from .simulation import SimulationSpace
from .storage import Storage
from .tasks import TaskManager
from .tools import ToolRegistry


class Matrix:
    def __init__(self, config: MatrixConfig = None, root=None):
        self.config = config or MatrixConfig()
        root = root or "."
        self.storage = Storage(self.config.storage.db_path)
        self.tasks = TaskManager(self.storage, tasks_dir=self.config.storage.tasks_dir)
        self.tools = ToolRegistry(tools_dir=self.config.storage.tools_dir, storage=self.storage)
        self.memory = MemorySpace(self.storage)
        self.knowledge = KnowledgeSpace(self.storage, knowledge_dir=self.config.storage.knowledge_dir)
        self.evaluator = Evaluator(self.storage, pass_threshold=self.config.evaluation.pass_threshold)
        self.simulation = SimulationSpace(self.storage, sandbox_dir=self.config.simulation.sandbox_dir, timeout=self.config.simulation.timeout_seconds)
        self.agents = AgentSpace()
        self.learning = LearningLoop(self.storage)

    def close(self):
        self.storage.close()

    def stats(self) -> dict:
        return {
            "config": self.config.dump(),
            "tasks": len(self.tasks.tasks),
            "tools": len(self.tools.tools),
            "knowledge": len(self.knowledge.list()),
            "memory": self.memory.stats(),
            "evaluation": self.evaluator.stats(),
            "learning": {
                "records": len(self.learning.get_history()),
                "success_rate": self.learning.success_rate(),
            },
            "storage": self.storage.stats(),
            "agents": len(self.agents.roles),
        }

    def describe(self) -> str:
        s = self.stats()
        lines = [
            "MATRIX - Artificial Work Environment for AI",
            f"Tasks: {s['tasks']}  Tools: {s['tools']}  Knowledge: {s['knowledge']}",
            f"Memory: {s['memory']['total']} facts ({s['memory']['verified']} verified)",
            f"Evaluations: {s['evaluation']['total_evaluations']} (pass rate {s['evaluation']['pass_rate']:.1f}%)",
            f"Learning records: {s['learning']['records']} (success rate {s['learning']['success_rate']:.1%})",
            f"Agents: {s['agents']}",
        ]
        return "\n".join(lines)
