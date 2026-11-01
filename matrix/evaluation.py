"""Evaluation space for MATRIX."""

from __future__ import annotations

import re
import time
from typing import Any, Callable

from .models import EvaluationResult, Task, TestResult, TestCase
from .storage import Storage


class Evaluator:
    def __init__(self, storage: Storage, pass_threshold: float = 1.0):
        self.storage = storage
        self.pass_threshold = pass_threshold

    def evaluate(self, task: Task, actual_output: Any, attempt: int = 1,
                tokens_used: int = 0, latency_ms: int = 0, diff_size: int = 0,
                custom_checker: Callable = None) -> EvaluationResult:
        test_results = []
        total_weight = 0.0
        passed_weight = 0.0

        for tc in task.test_cases:
            tr = self._run_test(tc, actual_output, custom_checker)
            test_results.append(tr)
            total_weight += tc.weight
            if tr.passed:
                passed_weight += tc.weight

        # also check expected_output if provided
        if task.expected_output and not task.test_cases:
            passed = str(actual_output).strip() == str(task.expected_output).strip()
            test_results.append(TestResult(
                test_id="expected_output", passed=passed,
                actual=actual_output, expected=task.expected_output,
            ))
            total_weight = 1.0
            passed_weight = 1.0 if passed else 0.0

        if total_weight == 0:
            score = 1.0 if actual_output is not None else 0.0
            passed = score >= self.pass_threshold
        else:
            score = passed_weight / total_weight
            passed = score >= self.pass_threshold

        errors = [tr.message for tr in test_results if not tr.passed and tr.message]
        feedback = self._feedback(task, test_results, passed)

        result = EvaluationResult(
            task_id=task.id, attempt=attempt, passed=passed, score=score,
            test_results=test_results, errors=errors, tokens_used=tokens_used,
            latency_ms=latency_ms, diff_size=diff_size, feedback=feedback,
        )
        self.storage.save_evaluation(result)
        return result

    def _run_test(self, tc: TestCase, actual: Any, custom_checker=None) -> TestResult:
        passed = False
        message = ""
        try:
            if custom_checker is not None:
                passed = bool(custom_checker(tc, actual))
            elif tc.check_type == "equals":
                passed = (actual == tc.expected)
                if not passed:
                    message = f"expected {tc.expected!r}, got {actual!r}"
            elif tc.check_type == "contains":
                passed = str(tc.expected) in str(actual)
                if not passed:
                    message = f"{tc.expected!r} not in output"
            elif tc.check_type == "regex":
                passed = bool(re.search(str(tc.expected), str(actual)))
                if not passed:
                    message = f"regex {tc.expected!r} did not match"
            elif tc.check_type == "not_contains":
                passed = str(tc.expected) not in str(actual)
                if not passed:
                    message = f"forbidden {tc.expected!r} found in output"
            elif tc.check_type == "truthy":
                passed = bool(actual)
            else:
                message = f"unknown check_type: {tc.check_type}"
        except Exception as e:
            passed = False
            message = f"checker error: {e}"
        return TestResult(
            test_id=tc.id, passed=passed, actual=actual,
            expected=tc.expected, message=message, weight=tc.weight,
        )

    def _feedback(self, task: Task, results: list[TestResult], passed: bool) -> str:
        if passed:
            return f"All tests passed. Task '{task.id}' complete."
        failed = [r for r in results if not r.passed]
        lines = [f"Task '{task.id}' failed ({len(failed)}/{len(results)} tests):"]
        for r in failed:
            lines.append(f"  - {r.test_id}: {r.message}")
        if task.hints:
            lines.append("Hints:")
            for h in task.hints:
                lines.append(f"  - {h}")
        return "\n".join(lines)

    def history(self, task_id: str = None) -> list[dict]:
        evals = self.storage.get_evaluations(task_id=task_id) if False else self.storage.get_evaluations()
        if task_id:
            evals = [e for e in evals if e["task_id"] == task_id]
        return sorted(evals, key=lambda e: e.get("attempt", 0))

    def trend(self, task_id: str) -> dict:
        evals = self.history(task_id)
        if not evals:
            return {"task_id": task_id, "attempts": 0, "improving": False, "scores": []}
        scores = [e["score"] for e in evals]
        improving = len(scores) >= 2 and scores[-1] > scores[0]
        return {"task_id": task_id, "attempts": len(scores),
                "improving": improving, "scores": scores,
                "best": max(scores), "latest": scores[-1]}

    def compare_strategies(self, strategy_a: str, strategy_b: str) -> dict:
        evals = self.storage.get_evaluations()
        a = [e for e in evals if strategy_a in str(e.get("feedback", ""))]
        b = [e for e in evals if strategy_b in str(e.get("feedback", ""))]
        def rate(x):
            return (sum(1 for e in x if e.get("passed")) / len(x)) if x else 0.0
        return {"strategy_a": strategy_a, "rate_a": rate(a), "n_a": len(a),
                "strategy_b": strategy_b, "rate_b": rate(b), "n_b": len(b)}

    def stats(self) -> dict:
        evals = self.storage.get_evaluations()
        total = len(evals)
        passed = sum(1 for e in evals if e["passed"])
        return {
            "total_evaluations": total,
            "passed": passed,
            "pass_rate": (100.0 * passed / total) if total else 0.0,
            "avg_score": (sum(e["score"] for e in evals) / total) if total else 0.0,
        }
