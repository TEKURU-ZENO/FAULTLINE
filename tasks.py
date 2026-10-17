#!/usr/bin/env python3
"""
FAULTLINE Task Runner.
Cross-platform task runner providing unified commands on Windows, macOS, and Linux.
Usage:
    python tasks.py up
    python tasks.py seed
    python tasks.py test-queries
    python tasks.py test-sim
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

def run_cmd(cmd: list[str]) -> int:
    print(f"\n[RUN] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print(f"[FAIL] Command exited with code {result.returncode}")
    return result.returncode

def up():
    """Start FalkorDB container."""
    return run_cmd(["docker", "compose", "up", "-d"])

def down():
    """Stop FalkorDB container."""
    return run_cmd(["docker", "compose", "down"])

def status():
    """Check FalkorDB container status."""
    return run_cmd(["docker", "compose", "ps"])

def seed():
    """Seed the 28-node Astronomy Shop topology into FalkorDB."""
    return run_cmd([sys.executable, "graph/seed_topology.py"])

def test_queries():
    """Run verification suite for all 10 core Cypher queries."""
    return run_cmd([sys.executable, "graph/test_queries.py"])

def test_sim():
    """Run simulator verification test."""
    return run_cmd([sys.executable, "-m", "pytest", "sim/test_sim.py", "-v"])

def test_race():
    """Test concurrent hypothesis claim race condition (Query 9)."""
    return run_cmd([sys.executable, "graph/test_claim_race.py"])

def check_vector():
    """Check vector distance vs similarity direction in FalkorDB."""
    return run_cmd([sys.executable, "graph/check_vector_metric.py"])

def api():
    """Start FastAPI streaming backend."""
    return run_cmd([sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"])

def web():
    """Start Next.js frontend dashboard on port 3001."""
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    web_dir = ROOT / "web"
    print(f"\n[RUN] {npm_cmd} run dev (in {web_dir})")
    res = subprocess.run([npm_cmd, "run", "dev"], cwd=str(web_dir))
    return res.returncode

def test_agents():
    """Run multi-agent incident commander cold vs warm fast-path test."""
    return run_cmd([sys.executable, "agents/test_agents.py"])

TASKS = {
    "up": up,
    "down": down,
    "status": status,
    "seed": seed,
    "test-queries": test_queries,
    "test-sim": test_sim,
    "test-race": test_race,
    "check-vector": check_vector,
    "api": api,
    "web": web,
    "test-agents": test_agents,
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in TASKS:
        print("Available tasks:")
        for name in TASKS:
            print(f"  python tasks.py {name}")
        sys.exit(1)
    
    task_func = TASKS[sys.argv[1]]
    code = task_func()
    sys.exit(code or 0)

if __name__ == "__main__":
    main()
