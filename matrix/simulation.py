"""Simulation space for MATRIX."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from .models import SimulationResult
from .storage import Storage


class SimulationSpace:
    def __init__(self, storage: Storage, sandbox_dir: str = ".matrix_sandbox", timeout: int = 120):
        self.storage = storage
        self.sandbox_dir = Path(sandbox_dir)
        self.timeout = timeout
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

    def create_sandbox(self, name: str = None) -> Path:
        name = name or f"sim-{uuid.uuid4().hex[:8]}"
        path = self.sandbox_dir / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def run_command(self, cmd: list[str], cwd: Path = None, timeout: int = None) -> dict:
        timeout = timeout or self.timeout
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8",
                errors="replace", cwd=str(cwd) if cwd else None, timeout=timeout,
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"returncode": -1, "stdout": "", "stderr": "timeout", "success": False}
        except Exception as e:
            return {"returncode": -1, "stdout": "", "stderr": str(e), "success": False}

    def run_task(self, task_id: str, command: list[str], cwd: Path = None) -> SimulationResult:
        sim_id = f"sim-{uuid.uuid4().hex[:8]}"
        start = time.time()
        result = self.run_command(command, cwd=cwd)
        duration = int((time.time() - start) * 1000)
        sim = SimulationResult(
            id=sim_id, task_id=task_id, success=result["success"],
            output=result["stdout"], error=result["stderr"], duration_ms=duration,
        )
        self.storage.save_simulation(sim)
        return sim

    def cleanup(self, name: str = None):
        if name:
            path = self.sandbox_dir / name
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
        else:
            if self.sandbox_dir.exists():
                shutil.rmtree(self.sandbox_dir, ignore_errors=True)
                self.sandbox_dir.mkdir(parents=True, exist_ok=True)

    def git_worktree(self, repo_path: str, branch: str = None) -> Path | None:
        """Create a git worktree for isolated experimentation."""
        sandbox = self.create_sandbox()
        try:
            cmd = ["git", "-C", repo_path, "worktree", "add", str(sandbox)]
            if branch:
                cmd.append(branch)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return sandbox
        except Exception:
            pass
        return None

    def list_sandboxes(self) -> list[str]:
        if not self.sandbox_dir.exists():
            return []
        return [d.name for d in self.sandbox_dir.iterdir() if d.is_dir()]
