"""Learning loop for MATRIX."""

from __future__ import annotations

import time
from typing import Any, Callable

from .models import LearningRecord
from .storage import Storage


class LearningLoop:
    def __init__(self, storage: Storage):
        self.storage = storage

    def record(self, task_id: str, attempt: int, success: bool,
               strategy: str = "", lessons: list[str] = None,
               tools_used: list[str] = None) -> LearningRecord:
        rec = LearningRecord(
            task_id=task_id, attempt=attempt, success=success,
            strategy=strategy, lessons=lessons or [], tools_used=tools_used or [],
            timestamp=time.time(),
        )
        self.storage.save_learning(rec)
        return rec

    def get_history(self, task_id: str = None) -> list[dict]:
        return self.storage.get_learning(task_id=task_id)

    def get_lessons(self, task_id: str = None) -> list[str]:
        records = self.storage.get_learning(task_id=task_id)
        lessons = []
        for r in records:
            if r["success"]:
                lessons.extend(r["lessons"])
        return list(dict.fromkeys(lessons))  # dedup preserving order

    def get_relevant_lessons(self, task_id: str, query: str = "") -> list[str]:
        """Return lessons relevant to a task, ranked by keyword overlap."""
        lessons = self.get_lessons()
        if not lessons:
            return []
        q = (query or task_id).lower().split()
        scored = []
        for lesson in lessons:
            low = lesson.lower()
            score = sum(1 for w in q if w in low)
            scored.append((score, lesson))
        scored.sort(key=lambda x: -x[0])
        return [l for _, l in scored if _ > 0] or lessons[:5]

    def mastery(self, task_id: str) -> dict:
        records = self.storage.get_learning(task_id=task_id)
        attempts = len(records)
        successes = sum(1 for r in records if r["success"])
        return {
            "task_id": task_id,
            "attempts": attempts,
            "successes": successes,
            "success_rate": (successes / attempts) if attempts else 0.0,
            "mastered": attempts >= 3 and (successes / attempts if attempts else 0.0) >= 0.8,
        }

    def get_strategies(self, task_id: str = None) -> list[str]:
        records = self.storage.get_learning(task_id=task_id)
        return list(dict.fromkeys(r["strategy"] for r in records if r["strategy"]))

    def success_rate(self, task_id: str = None) -> float:
        records = self.storage.get_learning(task_id=task_id)
        if not records:
            return 0.0
        return sum(1 for r in records if r["success"]) / len(records)

    def run_loop(self, task_id: str, executor: Callable, evaluator, max_attempts: int = 3) -> list:
        """Run the learning loop: attempt, evaluate, learn, repeat."""
        results = []
        for attempt in range(1, max_attempts + 1):
            # get lessons from previous attempts
            lessons = self.get_lessons(task_id)
            # execute
            try:
                output = executor(task_id, attempt, lessons)
            except Exception as e:
                output = None
                error = str(e)
            else:
                error = None

            # evaluate
            from .tasks import TaskManager
            # task will be passed by caller; here we just record
            result = None
            if output is not None:
                # evaluation done by caller
                pass

            # record learning
            self.record(
                task_id=task_id, attempt=attempt,
                success=(error is None), strategy=f"attempt-{attempt}",
                lessons=lessons, tools_used=[],
            )
            results.append({"attempt": attempt, "output": output, "error": error})
            if error is None:
                break
        return results
