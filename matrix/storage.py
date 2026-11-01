"""SQLite storage for MATRIX."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    data_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    attempt INTEGER NOT NULL,
    passed INTEGER NOT NULL,
    score REAL NOT NULL,
    data_json TEXT NOT NULL,
    ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS memory (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    fact TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL DEFAULT 0,
    verified INTEGER NOT NULL DEFAULT 0,
    tags TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS knowledge (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT '',
    kind TEXT NOT NULL DEFAULT 'doc',
    tags TEXT NOT NULL DEFAULT '[]',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS learning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    attempt INTEGER NOT NULL,
    success INTEGER NOT NULL,
    strategy TEXT NOT NULL DEFAULT '',
    lessons TEXT NOT NULL DEFAULT '[]',
    tools_used TEXT NOT NULL DEFAULT '[]',
    ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS simulations (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    success INTEGER NOT NULL,
    data_json TEXT NOT NULL,
    ts REAL NOT NULL
);
"""


class Storage:
    def __init__(self, db_path: str = "matrix.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self):
        with self._lock:
            self._conn.close()

    # tasks
    def save_task(self, task):
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO tasks (id, data_json) VALUES (?,?)",
                (task.id, json.dumps(task.as_dict(), ensure_ascii=False)),
            )
            self._conn.commit()

    def get_task(self, task_id):
        with self._lock:
            row = self._conn.execute("SELECT data_json FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            return None
        return json.loads(row["data_json"])

    def list_tasks(self):
        with self._lock:
            rows = self._conn.execute("SELECT data_json FROM tasks ORDER BY id").fetchall()
        return [json.loads(r["data_json"]) for r in rows]

    def delete_task(self, task_id):
        with self._lock:
            self._conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            self._conn.commit()

    # evaluations
    def save_evaluation(self, ev):
        with self._lock:
            self._conn.execute(
                "INSERT INTO evaluations (task_id, attempt, passed, score, data_json, ts) VALUES (?,?,?,?,?,?)",
                (ev.task_id, ev.attempt, 1 if ev.passed else 0, ev.score, json.dumps(ev.as_dict(), ensure_ascii=False), time.time()),
            )
            self._conn.commit()

    def get_evaluations(self, task_id=None):
        with self._lock:
            if task_id:
                rows = self._conn.execute("SELECT data_json FROM evaluations WHERE task_id=? ORDER BY ts", (task_id,)).fetchall()
            else:
                rows = self._conn.execute("SELECT data_json FROM evaluations ORDER BY ts").fetchall()
        return [json.loads(r["data_json"]) for r in rows]

    def stats(self):
        with self._lock:
            tasks = self._conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            evals = self._conn.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0]
            passed = self._conn.execute("SELECT COUNT(*) FROM evaluations WHERE passed=1").fetchone()[0]
            mem = self._conn.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
            know = self._conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
            learn = self._conn.execute("SELECT COUNT(*) FROM learning").fetchone()[0]
        return {
            "tasks": tasks, "evaluations": evals, "passed": passed,
            "pass_rate": (100.0 * passed / evals) if evals else 0.0,
            "memory_facts": mem, "knowledge": know, "learning_records": learn,
        }

    # memory
    def save_memory(self, fact):
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO memory (id, kind, fact, source, confidence, created_at, expires_at, verified, tags) VALUES (?,?,?,?,?,?,?,?,?)",
                (fact.id, fact.kind, fact.fact, fact.source, fact.confidence, fact.created_at, fact.expires_at, 1 if fact.verified else 0, json.dumps(fact.tags)),
            )
            self._conn.commit()

    def get_memory(self, kind=None, tag=None):
        with self._lock:
            if kind:
                rows = self._conn.execute("SELECT * FROM memory WHERE kind=?", (kind,)).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM memory").fetchall()
        result = []
        for r in rows:
            tags = json.loads(r["tags"])
            if tag and tag not in tags:
                continue
            result.append({
                "id": r["id"], "kind": r["kind"], "fact": r["fact"],
                "source": r["source"], "confidence": r["confidence"],
                "created_at": r["created_at"], "expires_at": r["expires_at"],
                "verified": bool(r["verified"]), "tags": tags,
            })
        return result

    def delete_memory(self, fact_id):
        with self._lock:
            self._conn.execute("DELETE FROM memory WHERE id=?", (fact_id,))
            self._conn.commit()

    # knowledge
    def save_knowledge(self, entry):
        now = time.time()
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO knowledge (id, title, content, source, kind, tags, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (entry.id, entry.title, entry.content, entry.source, entry.kind, json.dumps(entry.tags), entry.created_at or now, now),
            )
            self._conn.commit()

    def get_knowledge(self, kind=None, tag=None):
        with self._lock:
            if kind:
                rows = self._conn.execute("SELECT * FROM knowledge WHERE kind=?", (kind,)).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM knowledge").fetchall()
        result = []
        for r in rows:
            tags = json.loads(r["tags"])
            if tag and tag not in tags:
                continue
            result.append({
                "id": r["id"], "title": r["title"], "content": r["content"],
                "source": r["source"], "kind": r["kind"], "tags": tags,
                "created_at": r["created_at"], "updated_at": r["updated_at"],
            })
        return result

    def search_knowledge(self, query):
        q = f"%{query.lower()}%"
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM knowledge WHERE lower(title) LIKE ? OR lower(content) LIKE ? OR lower(tags) LIKE ?",
                (q, q, q),
            ).fetchall()
        return [{"id": r["id"], "title": r["title"], "content": r["content"], "kind": r["kind"], "tags": json.loads(r["tags"])} for r in rows]

    # learning
    def save_learning(self, record):
        with self._lock:
            self._conn.execute(
                "INSERT INTO learning (task_id, attempt, success, strategy, lessons, tools_used, ts) VALUES (?,?,?,?,?,?,?)",
                (record.task_id, record.attempt, 1 if record.success else 0, record.strategy, json.dumps(record.lessons), json.dumps(record.tools_used), record.timestamp or time.time()),
            )
            self._conn.commit()

    def get_learning(self, task_id=None):
        with self._lock:
            if task_id:
                rows = self._conn.execute("SELECT * FROM learning WHERE task_id=? ORDER BY ts", (task_id,)).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM learning ORDER BY ts").fetchall()
        return [{"task_id": r["task_id"], "attempt": r["attempt"], "success": bool(r["success"]), "strategy": r["strategy"], "lessons": json.loads(r["lessons"]), "tools_used": json.loads(r["tools_used"]), "ts": r["ts"]} for r in rows]

    # simulations
    def save_simulation(self, sim):
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO simulations (id, task_id, success, data_json, ts) VALUES (?,?,?,?,?)",
                (sim.id, sim.task_id, 1 if sim.success else 0, json.dumps(sim.as_dict(), ensure_ascii=False), time.time()),
            )
            self._conn.commit()

    def get_simulations(self, task_id=None):
        with self._lock:
            if task_id:
                rows = self._conn.execute("SELECT data_json FROM simulations WHERE task_id=?", (task_id,)).fetchall()
            else:
                rows = self._conn.execute("SELECT data_json FROM simulations").fetchall()
        return [json.loads(r["data_json"]) for r in rows]
