import subprocess, sys, os
from pathlib import Path

ENV = dict(os.environ)
ENV["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
ENV["MATRIX_DB"] = str(Path(__file__).resolve().parents[1] / "test_matrix.db")


def test_init():
    p = subprocess.run([sys.executable, "-m", "matrix.cli", "init"], capture_output=True, text=True, env=ENV, cwd=str(Path(__file__).resolve().parents[1]))
    assert p.returncode == 0


def test_stats():
    p = subprocess.run([sys.executable, "-m", "matrix.cli", "stats"], capture_output=True, text=True, env=ENV, cwd=str(Path(__file__).resolve().parents[1]))
    assert p.returncode == 0
    assert "MATRIX" in p.stdout


def test_tasks():
    p = subprocess.run([sys.executable, "-m", "matrix.cli", "tasks"], capture_output=True, text=True, env=ENV, cwd=str(Path(__file__).resolve().parents[1]))
    assert p.returncode == 0
    assert "reverse-string" in p.stdout


def test_tools():
    p = subprocess.run([sys.executable, "-m", "matrix.cli", "tools"], capture_output=True, text=True, env=ENV, cwd=str(Path(__file__).resolve().parents[1]))
    assert p.returncode == 0
    assert "read_file" in p.stdout


def test_agents():
    p = subprocess.run([sys.executable, "-m", "matrix.cli", "agents"], capture_output=True, text=True, env=ENV, cwd=str(Path(__file__).resolve().parents[1]))
    assert p.returncode == 0
    assert "developer" in p.stdout


def test_describe():
    p = subprocess.run([sys.executable, "-m", "matrix.cli", "describe"], capture_output=True, text=True, env=ENV, cwd=str(Path(__file__).resolve().parents[1]))
    assert p.returncode == 0
    assert "MATRIX" in p.stdout
