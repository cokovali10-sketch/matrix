"""Agent space for MATRIX."""

from __future__ import annotations

from .models import AgentRole


DEFAULT_ROLES = [
    AgentRole(
        id="architect", name="Architect",
        description="Designs system architecture and makes high-level decisions.",
        system_prompt="You are a software architect. Design clean, scalable architectures. Consider trade-offs, dependencies, and maintainability.",
        tools=["read_file", "search", "plan"],
        capabilities=["design", "architecture", "planning"],
    ),
    AgentRole(
        id="developer", name="Developer",
        description="Implements features and writes code.",
        system_prompt="You are a developer. Write clean, tested, minimal code. Follow existing patterns. Don't over-engineer.",
        tools=["read_file", "edit_file", "write_file", "run_tests", "search"],
        capabilities=["implementation", "coding", "refactoring"],
    ),
    AgentRole(
        id="debugger", name="Debugger",
        description="Finds and fixes bugs systematically.",
        system_prompt="You are a debugger. Reproduce first, then find root cause, then fix. Never guess.",
        tools=["read_file", "search", "run_tests", "run_command"],
        capabilities=["debugging", "root-cause-analysis"],
    ),
    AgentRole(
        id="tester", name="Tester",
        description="Writes and runs tests.",
        system_prompt="You are a tester. Write tests that verify behavior, cover edge cases, and are deterministic.",
        tools=["read_file", "write_file", "run_tests"],
        capabilities=["testing", "quality-assurance"],
    ),
    AgentRole(
        id="researcher", name="Researcher",
        description="Researches documentation and APIs.",
        system_prompt="You are a researcher. Find accurate information, cite sources, summarize clearly.",
        tools=["search", "read_file", "web_search", "read_docs"],
        capabilities=["research", "documentation", "api-study"],
    ),
    AgentRole(
        id="security", name="Security",
        description="Reviews code for security issues.",
        system_prompt="You are a security reviewer. Find vulnerabilities, check for secrets, validate inputs, review auth.",
        tools=["read_file", "search", "scan"],
        capabilities=["security-review", "vulnerability-analysis"],
    ),
    AgentRole(
        id="reviewer", name="Reviewer",
        description="Reviews code quality and correctness.",
        system_prompt="You are a code reviewer. Check correctness, style, tests, and maintainability.",
        tools=["read_file", "search", "run_tests"],
        capabilities=["code-review", "quality"],
    ),
]


class AgentSpace:
    def __init__(self, roles=None):
        self.roles: dict[str, AgentRole] = {}
        self.performance: dict[str, dict] = {}
        for role in (roles or DEFAULT_ROLES):
            self.roles[role.id] = role
            self.performance[role.id] = {"attempts": 0, "successes": 0}

    def record_performance(self, role_id: str, success: bool):
        if role_id not in self.performance:
            self.performance[role_id] = {"attempts": 0, "successes": 0}
        self.performance[role_id]["attempts"] += 1
        if success:
            self.performance[role_id]["successes"] += 1

    def success_rate(self, role_id: str) -> float:
        p = self.performance.get(role_id, {"attempts": 0, "successes": 0})
        return (p["successes"] / p["attempts"]) if p["attempts"] else 0.0

    def recommend_role(self, task_description: str) -> AgentRole | None:
        candidates = self.find_for_task(task_description)
        if not candidates:
            return None
        # prefer role with best success rate among candidates
        candidates.sort(key=lambda r: -self.success_rate(r.id))
        return candidates[0]

    def collaborate(self, task_description: str) -> list[AgentRole]:
        """Return ordered list of roles for a multi-agent task."""
        roles = self.find_for_task(task_description)
        # always include reviewer if not present
        if "reviewer" in self.roles and not any(r.id == "reviewer" for r in roles):
            roles = roles + [self.roles["reviewer"]]
        return roles


    def get(self, role_id: str) -> AgentRole | None:
        return self.roles.get(role_id)

    def list(self) -> list[AgentRole]:
        return list(self.roles.values())

    def register(self, role: AgentRole):
        self.roles[role.id] = role

    def find_for_task(self, task_description: str) -> list[AgentRole]:
        desc = task_description.lower()
        result = []
        for role in self.roles.values():
            if any(cap in desc for cap in role.capabilities):
                result.append(role)
        if not result:
            result = [self.roles.get("developer")]
        return [r for r in result if r is not None]
