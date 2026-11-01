import pytest
from matrix import Matrix


def test_init():
    m = Matrix()
    assert m is not None
    m.close()


def test_stats():
    m = Matrix()
    s = m.stats()
    assert "tasks" in s
    assert "tools" in s
    assert "memory" in s
    m.close()


def test_describe():
    m = Matrix()
    d = m.describe()
    assert "MATRIX" in d
    m.close()


def test_tasks_loaded():
    m = Matrix()
    tasks = m.tasks.list()
    assert len(tasks) >= 3
    m.close()


def test_task_get():
    m = Matrix()
    t = m.tasks.get("reverse-string")
    assert t is not None
    assert t.title == "Reverse a string"
    assert len(t.test_cases) == 4
    m.close()


def test_task_search():
    m = Matrix()
    results = m.tasks.search("fizz")
    assert len(results) >= 1
    m.close()


def test_tools_loaded():
    m = Matrix()
    tools = m.tools.list()
    assert len(tools) >= 3
    m.close()


def test_tool_get():
    m = Matrix()
    t = m.tools.get("read_file")
    assert t is not None
    assert t.name == "Read file"
    m.close()


def test_memory_add():
    m = Matrix()
    fact = m.memory.add("Python uses 0-based indexing", kind="fact", source="experience", tags=["python"])
    assert fact.id.startswith("mem-")
    facts = m.memory.get(kind="fact")
    assert len(facts) >= 1
    m.close()


def test_memory_search():
    m = Matrix()
    m.memory.add("Always run tests before commit", kind="fact", tags=["testing"])
    results = m.memory.search("tests")
    assert len(results) >= 1
    m.close()


def test_memory_stats():
    m = Matrix()
    m.memory.add("fact1", kind="fact")
    m.memory.add("assumption1", kind="assumption")
    stats = m.memory.stats()
    assert stats["total"] >= 2
    assert stats["facts"] >= 1
    assert stats["assumptions"] >= 1
    m.close()


def test_knowledge_add_and_search():
    m = Matrix()
    from matrix.models import KnowledgeEntry
    entry = KnowledgeEntry(id="test-k", title="Test Knowledge", content="This is a test", kind="doc", tags=["test"])
    m.knowledge.add(entry)
    results = m.knowledge.search("test")
    assert len(results) >= 1
    m.close()


def test_agents():
    m = Matrix()
    roles = m.agents.list()
    assert len(roles) == 7
    dev = m.agents.get("developer")
    assert dev is not None
    assert "implementation" in dev.capabilities
    m.close()


def test_simulation():
    m = Matrix()
    result = m.simulation.run_command(["python", "-c", "print('hello')"])
    assert result["success"] is True
    assert "hello" in result["stdout"]
    m.close()


def test_evaluation():
    m = Matrix()
    task = m.tasks.get("fizzbuzz")
    result = m.evaluator.evaluate(task, "FizzBuzz", attempt=1)
    assert result.task_id == "fizzbuzz"
    assert result.score >= 0
    m.close()


def test_learning():
    m = Matrix()
    rec = m.learning.record("fizzbuzz", 1, True, strategy="direct", lessons=["use modulo"])
    assert rec.success is True
    history = m.learning.get_history("fizzbuzz")
    assert len(history) >= 1
    lessons = m.learning.get_lessons("fizzbuzz")
    assert "use modulo" in lessons
    m.close()


def test_storage_stats():
    m = Matrix()
    s = m.storage.stats()
    assert "tasks" in s
    assert "evaluations" in s
    m.close()
