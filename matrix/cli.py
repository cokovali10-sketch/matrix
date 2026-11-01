"""CLI for MATRIX."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import Matrix


def _matrix(args) -> Matrix:
    return Matrix()


def cmd_init(args) -> int:
    from .config import MatrixConfig
    config = MatrixConfig()
    config.save(args.path or "matrix.json")
    print(f"wrote {args.path or 'matrix.json'}")
    return 0


def cmd_stats(args) -> int:
    m = _matrix(args)
    print(m.describe())
    import json
    print(json.dumps(m.stats(), indent=2, default=str))
    m.close()
    return 0


def cmd_tasks(args) -> int:
    m = _matrix(args)
    tasks = m.tasks.list(difficulty=args.difficulty, category=args.category)
    if not tasks:
        print("No tasks.")
        return 0
    for t in tasks:
        print(f"{t.id:<30} [{t.difficulty:<7}] {t.title}")
    m.close()
    return 0


def cmd_task_show(args) -> int:
    m = _matrix(args)
    task = m.tasks.get(args.id)
    if not task:
        print(f"Not found: {args.id}")
        m.close()
        return 1
    print(json.dumps(task.as_dict(), indent=2, ensure_ascii=False, default=str))
    m.close()
    return 0


def cmd_tools(args) -> int:
    m = _matrix(args)
    for t in m.tools.list(tag=args.tag):
        print(f"{t.id:<25} {t.name:<20} {t.description[:60]}")
    m.close()
    return 0


def cmd_memory_add(args) -> int:
    m = _matrix(args)
    fact = m.memory.add(args.fact, kind=args.kind, source=args.source, confidence=args.confidence, tags=args.tags or [])
    print(f"added: {fact.id}")
    m.close()
    return 0


def cmd_memory_list(args) -> int:
    m = _matrix(args)
    facts = m.memory.get(kind=args.kind, tag=args.tag)
    for f in facts:
        print(f"{f['id']:<12} [{f['kind']:<10}] (conf={f['confidence']:.2f}) {f['fact'][:80]}")
    m.close()
    return 0


def cmd_memory_search(args) -> int:
    m = _matrix(args)
    facts = m.memory.search(args.query)
    for f in facts:
        print(f"{f['id']:<12} [{f['kind']:<10}] {f['fact'][:80]}")
    m.close()
    return 0


def cmd_knowledge_add(args) -> int:
    m = _matrix(args)
    from .models import KnowledgeEntry
    import time
    content = Path(args.file).read_text(encoding="utf-8") if args.file else args.content
    entry = KnowledgeEntry(
        id=args.id, title=args.title, content=content,
        source=args.source or "", kind=args.kind,
        tags=args.tags or [], created_at=time.time(), updated_at=time.time(),
    )
    m.knowledge.add(entry)
    print(f"added knowledge: {args.id}")
    m.close()
    return 0


def cmd_knowledge_search(args) -> int:
    m = _matrix(args)
    results = m.knowledge.search(args.query)
    for r in results:
        print(f"{r['id']:<20} {r['title']}")
    m.close()
    return 0


def cmd_agents(args) -> int:
    m = _matrix(args)
    for r in m.agents.list():
        print(f"{r.id:<12} {r.name:<12} {r.description}")
    m.close()
    return 0


def cmd_simulate(args) -> int:
    m = _matrix(args)
    cmd = args.command
    result = m.simulation.run_command(cmd, timeout=args.timeout)
    print(f"returncode: {result['returncode']}")
    if result["stdout"]:
        print("stdout:")
        print(result["stdout"][:2000])
    if result["stderr"]:
        print("stderr:")
        print(result["stderr"][:2000])
    m.close()
    return 0 if result["success"] else 1


def cmd_eval(args) -> int:
    m = _matrix(args)
    print("Evaluation stats:")
    print(m.evaluator.stats())
    m.close()
    return 0


def cmd_learn(args) -> int:
    m = _matrix(args)
    print("Learning records:")
    for r in m.learning.get_history():
        print(f"  {r['task_id']} attempt={r['attempt']} success={r['success']} strategy={r['strategy']}")
    print(f"Success rate: {m.learning.success_rate():.1%}")
    m.close()
    return 0


def cmd_describe(args) -> int:
    m = _matrix(args)
    print(m.describe())
    m.close()
    return 0


def cmd_interactive(args) -> int:
    m = _matrix(args)
    print("MATRIX interactive. Commands: tasks, tools, memory, agents, stats, quit")
    while True:
        try:
            line = input("matrix> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in ("quit", "exit", "q"):
            break
        if line == "tasks":
            for t in m.tasks.list():
                print(f"{t.id:<30} [{t.difficulty:<7}] {t.title}")
        elif line == "tools":
            for t in m.tools.list():
                print(f"{t.id:<25} {t.name}")
        elif line == "agents":
            for r in m.agents.list():
                print(f"{r.id:<12} {r.name}")
        elif line == "stats":
            print(m.describe())
        elif line == "memory":
            for f in m.memory.get():
                print(f"{f['id']:<12} {f['fact'][:60]}")
        elif line.startswith("recommend"):
            t = m.tasks.recommend_next(m.learning)
            print(t.id if t else "none")
        else:
            print("unknown command")
    m.close()
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="matrix", description="MATRIX - AI work environment")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create matrix.json")
    p.add_argument("--path", default="matrix.json")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("stats", help="show stats")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("describe", help="describe MATRIX")
    p.set_defaults(func=cmd_describe)

    p = sub.add_parser("tasks", help="list tasks")
    p.add_argument("--difficulty", default=None)
    p.add_argument("--category", default=None)
    p.set_defaults(func=cmd_tasks)

    p = sub.add_parser("task", help="show a task")
    p.add_argument("id")
    p.set_defaults(func=cmd_task_show)

    p = sub.add_parser("tools", help="list tools")
    p.add_argument("--tag", default=None)
    p.set_defaults(func=cmd_tools)

    p = sub.add_parser("memory", help="memory operations")
    mem_sub = p.add_subparsers(dest="mem_action", required=True)
    pa = mem_sub.add_parser("add")
    pa.add_argument("fact")
    pa.add_argument("--kind", default="fact", choices=["fact", "assumption", "stale"])
    pa.add_argument("--source", default="")
    pa.add_argument("--confidence", type=float, default=1.0)
    pa.add_argument("--tags", nargs="*", default=[])
    pa.set_defaults(func=cmd_memory_add)
    pa = mem_sub.add_parser("list")
    pa.add_argument("--kind", default=None)
    pa.add_argument("--tag", default=None)
    pa.set_defaults(func=cmd_memory_list)
    pa = mem_sub.add_parser("search")
    pa.add_argument("query")
    pa.set_defaults(func=cmd_memory_search)

    p = sub.add_parser("knowledge", help="knowledge operations")
    k_sub = p.add_subparsers(dest="know_action", required=True)
    pa = k_sub.add_parser("add")
    pa.add_argument("id")
    pa.add_argument("title")
    pa.add_argument("--file", default=None)
    pa.add_argument("--content", default="")
    pa.add_argument("--source", default="")
    pa.add_argument("--kind", default="doc")
    pa.add_argument("--tags", nargs="*", default=[])
    pa.set_defaults(func=cmd_knowledge_add)
    pa = k_sub.add_parser("search")
    pa.add_argument("query")
    pa.set_defaults(func=cmd_knowledge_search)

    p = sub.add_parser("agents", help="list agent roles")
    p.set_defaults(func=cmd_agents)

    p = sub.add_parser("simulate", help="run a command in sandbox")
    p.add_argument("command", nargs="+")
    p.add_argument("--timeout", type=int, default=120)
    p.set_defaults(func=cmd_simulate)

    p = sub.add_parser("eval", help="evaluation stats")
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser("learn", help="learning records")
    p.set_defaults(func=cmd_learn)

    p = sub.add_parser("interactive", help="interactive REPL")
    p.set_defaults(func=cmd_interactive)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
