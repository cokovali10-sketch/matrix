"""Task management for MATRIX."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Task, TestCase
from .storage import Storage


class TaskManager:
    def __init__(self, storage: Storage, tasks_dir=None):
        self.storage = storage
        self.tasks_dir = Path(tasks_dir) if tasks_dir else None
        self.tasks: dict[str, Task] = {}
        if tasks_dir:
            self._load(tasks_dir)
        self._load_from_storage()

    def _load(self, tasks_dir):
        d = Path(tasks_dir)
        if not d.exists():
            return
        for path in sorted(d.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            task = self._from_dict(data)
            self.tasks[task.id] = task
            self.storage.save_task(task)

    def _load_from_storage(self):
        for data in self.storage.list_tasks():
            task = self._from_dict(data)
            self.tasks[task.id] = task

    def _from_dict(self, data: dict) -> Task:
        test_cases = [TestCase(**tc) for tc in data.get("test_cases", [])]
        return Task(
            id=data["id"],
            title=data.get("title", data["id"]),
            description=data.get("description", ""),
            difficulty=data.get("difficulty", "medium"),
            category=data.get("category", "general"),
            constraints=data.get("constraints", []),
            test_cases=test_cases,
            expected_output=data.get("expected_output", ""),
            hints=data.get("hints", []),
            knowledge_refs=data.get("knowledge_refs", []),
            tool_refs=data.get("tool_refs", []),
            prerequisites=data.get("prerequisites", []),
            max_attempts=data.get("max_attempts", 3),
            timeout_seconds=data.get("timeout_seconds", 120),
        )

    def get(self, task_id: str) -> Task | None:
        return self.tasks.get(task_id)

    def list(self, difficulty=None, category=None) -> list[Task]:
        result = list(self.tasks.values())
        if difficulty:
            result = [t for t in result if t.difficulty == difficulty]
        if category:
            result = [t for t in result if t.category == category]
        return result

    def available(self, completed: set[str] = None) -> list[Task]:
        """Tasks whose prerequisites are all completed."""
        completed = completed or set()
        return [t for t in self.tasks.values()
                if all(p in completed for p in t.prerequisites)]

    def adapt_difficulty(self, task_id: str, learning_loop) -> str:
        """Return recommended difficulty for next task based on performance."""
        m = learning_loop.mastery(task_id) if hasattr(learning_loop, "mastery") else {"success_rate": 0.0}
        rate = m.get("success_rate", 0.0)
        if rate >= 0.9:
            return "hard"
        if rate >= 0.6:
            return "medium"
        return "easy"

    def add(self, task: Task):
        self.tasks[task.id] = task
        self.storage.save_task(task)

    def remove(self, task_id: str):
        self.tasks.pop(task_id, None)
        self.storage.delete_task(task_id)

    def search(self, query: str) -> list[Task]:
        q = query.lower()
        return [t for t in self.tasks.values() if q in t.id.lower() or q in t.title.lower() or q in t.description.lower() or q in t.category.lower()]

    def to_dict(self, task: Task) -> dict:
        return task.as_dict()


    def recommend_next(self, learning_loop=None, category=None):
        order = {"easy": 0, "medium": 1, "hard": 2, "expert": 3}
        candidates = self.list(category=category)
        if learning_loop is not None:
            mastered = set()
            for t in candidates:
                if learning_loop.success_rate(t.id) >= 0.8:
                    mastered.add(t.id)
            candidates = [t for t in candidates if t.id not in mastered]
        if not candidates:
            return None
        candidates.sort(key=lambda t: (order.get(t.difficulty, 1), t.id))
        return candidates[0]
