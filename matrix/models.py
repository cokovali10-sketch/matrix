"""Core models for MATRIX."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Tool:
    id: str
    name: str
    description: str
    input_schema: dict = field(default_factory=dict)
    output_schema: dict = field(default_factory=dict)
    safety: list[str] = field(default_factory=list)
    example: str = ""
    tags: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "input_schema": self.input_schema, "output_schema": self.output_schema,
            "safety": self.safety, "example": self.example, "tags": self.tags,
        }


@dataclass
class TestCase:
    id: str
    description: str
    input_data: Any = None
    expected: Any = None
    check_type: str = "equals"  # equals | contains | regex | custom
    weight: float = 1.0

    def as_dict(self) -> dict:
        return {
            "id": self.id, "description": self.description,
            "input_data": self.input_data, "expected": self.expected,
            "check_type": self.check_type, "weight": self.weight,
        }


@dataclass
class Task:
    id: str
    title: str
    description: str
    difficulty: str = "medium"  # easy | medium | hard | expert
    category: str = "general"
    constraints: list[str] = field(default_factory=list)
    test_cases: list[TestCase] = field(default_factory=list)
    expected_output: str = ""
    hints: list[str] = field(default_factory=list)
    knowledge_refs: list[str] = field(default_factory=list)
    tool_refs: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    max_attempts: int = 3
    timeout_seconds: int = 120

    def as_dict(self) -> dict:
        return {
            "id": self.id, "title": self.title, "description": self.description,
            "difficulty": self.difficulty, "category": self.category,
            "constraints": self.constraints,
            "test_cases": [tc.as_dict() for tc in self.test_cases],
            "expected_output": self.expected_output, "hints": self.hints,
            "knowledge_refs": self.knowledge_refs, "tool_refs": self.tool_refs,
            "prerequisites": self.prerequisites,
            "max_attempts": self.max_attempts, "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class TestResult:
    test_id: str
    passed: bool
    actual: Any = None
    expected: Any = None
    message: str = ""
    weight: float = 1.0

    def as_dict(self) -> dict:
        return {
            "test_id": self.test_id, "passed": self.passed,
            "actual": self.actual, "expected": self.expected,
            "message": self.message, "weight": self.weight,
        }


@dataclass
class EvaluationResult:
    task_id: str
    attempt: int
    passed: bool
    score: float = 0.0
    test_results: list[TestResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    tokens_used: int = 0
    latency_ms: int = 0
    diff_size: int = 0
    feedback: str = ""

    def as_dict(self) -> dict:
        return {
            "task_id": self.task_id, "attempt": self.attempt,
            "passed": self.passed, "score": self.score,
            "test_results": [tr.as_dict() for tr in self.test_results],
            "errors": self.errors, "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms, "diff_size": self.diff_size,
            "feedback": self.feedback,
        }


@dataclass
class MemoryFact:
    id: str
    fact: str
    kind: str = "fact"  # fact | assumption | stale
    source: str = ""
    confidence: float = 1.0
    created_at: float = 0.0
    expires_at: float = 0.0
    tags: list[str] = field(default_factory=list)
    verified: bool = False

    def as_dict(self) -> dict:
        return {
            "id": self.id, "fact": self.fact, "kind": self.kind,
            "source": self.source, "confidence": self.confidence,
            "created_at": self.created_at, "expires_at": self.expires_at,
            "tags": self.tags, "verified": self.verified,
        }


@dataclass
class KnowledgeEntry:
    id: str
    title: str
    content: str
    source: str = ""
    kind: str = "doc"  # doc | api | principle | instruction
    tags: list[str] = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0

    def as_dict(self) -> dict:
        return {
            "id": self.id, "title": self.title, "content": self.content,
            "source": self.source, "kind": self.kind, "tags": self.tags,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }


@dataclass
class AgentRole:
    id: str
    name: str
    description: str
    system_prompt: str = ""
    tools: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "system_prompt": self.system_prompt, "tools": self.tools,
            "capabilities": self.capabilities,
        }


@dataclass
class SimulationResult:
    id: str
    task_id: str
    success: bool
    output: str = ""
    error: str = ""
    duration_ms: int = 0
    artifacts: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "id": self.id, "task_id": self.task_id, "success": self.success,
            "output": self.output, "error": self.error,
            "duration_ms": self.duration_ms, "artifacts": self.artifacts,
        }


@dataclass
class LearningRecord:
    task_id: str
    attempt: int
    success: bool
    strategy: str = ""
    lessons: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    timestamp: float = 0.0

    def as_dict(self) -> dict:
        return {
            "task_id": self.task_id, "attempt": self.attempt,
            "success": self.success, "strategy": self.strategy,
            "lessons": self.lessons, "tools_used": self.tools_used,
            "timestamp": self.timestamp,
        }
