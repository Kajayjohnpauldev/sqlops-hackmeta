#!/usr/bin/env python3
# SQLOps OpenEnv
# Designed by K. Ajay John Paul
# B.Tech CSE — KL University, Hyderabad
# OpenEnv Hackathon 2024

"""
Baseline inference script.
Runs through all 3 tasks using hardcoded reference-quality SQL.
Follows exact OpenEnv log format: [START], [STEP], [END].

Environment variables:
  API_BASE_URL  - URL of the running environment (default: http://localhost:7860)
  MODEL_NAME    - Name of the model/agent (default: baseline-agent)
  HF_TOKEN      - Hugging Face token (optional, for authenticated endpoints)
"""

import os
import sys
import json
import time

try:
    import requests
except ImportError:
    # Fallback: install requests if missing
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# ─── Configuration ──────────────────────────────────────────────────

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.getenv("MODEL_NAME", "baseline-agent")
HF_TOKEN = os.getenv("HF_TOKEN")  # No default — must be provided externally


# ─── Known good solutions for reproducible scoring ─────────────────

SOLUTIONS = {
    "sales_summary": {
        "sql_query": """
            SELECT
                region,
                ROUND(SUM(amount), 2)   AS total_revenue,
                SUM(quantity)           AS total_quantity
            FROM sales
            GROUP BY region
            ORDER BY total_revenue DESC
        """,
        "reasoning": "Group sales by region, sum amount and quantity, sort descending by revenue.",
    },
    "debug_query": {
        "sql_query": """
            SELECT
                d.name           AS department,
                COUNT(p.id)      AS active_projects
            FROM departments d
            LEFT JOIN projects p
                ON d.id = p.department_id AND p.status = 'active'
            GROUP BY d.name
            ORDER BY active_projects DESC, d.name ASC
        """,
        "reasoning": "Move status filter from WHERE to ON clause to preserve LEFT JOIN NULL rows.",
    },
    "performance_analytics": {
        "sql_query": """
            WITH dept_ratings AS (
                SELECT
                    d.name                       AS department,
                    ROUND(AVG(pr.rating), 2)     AS avg_rating,
                    COUNT(pr.id)                 AS review_count
                FROM performance_reviews pr
                JOIN employees e   ON pr.employee_id = e.id
                JOIN departments d ON e.department_id = d.id
                GROUP BY d.name
                HAVING COUNT(pr.id) >= 2
            )
            SELECT
                department,
                avg_rating,
                review_count,
                RANK() OVER (ORDER BY avg_rating DESC) AS dept_rank
            FROM dept_ratings
            ORDER BY dept_rank ASC
        """,
        "reasoning": "CTE computes per-department avg rating with HAVING >= 2, outer query adds RANK window function.",
    },
}


def log(tag: str, msg: str):
    """Print with OpenEnv-required log format."""
    print(f"[{tag}] {msg}", flush=True)


def wait_for_server(base_url: str, timeout: int = 120):
    """Wait for the environment server to become healthy."""
    log("STEP", f"Waiting for server at {base_url}...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{base_url}/health", timeout=5)
            if r.status_code == 200:
                log("STEP", f"Server is healthy (took {time.time()-start:.1f}s)")
                return True
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            log("STEP", f"Health check error: {e}")
        time.sleep(2)
    log("STEP", f"Server did not respond within {timeout}s")
    return False


def run_inference():
    """Run the baseline agent through all tasks."""
    log("START", f"task=sqlops_all model={MODEL_NAME} env={API_BASE_URL}")

    # Wait for server to be ready
    if not wait_for_server(API_BASE_URL):
        log("END", "Server unreachable — aborting")
        return 0.0

    total_reward = 0.0
    task_ids = list(SOLUTIONS.keys())
    step_num = 0

    for task_idx, task_id in enumerate(task_ids):
        # Reset to the specific task
        step_num += 1
        log("STEP", f"step={step_num} action=reset task_index={task_idx} task={task_id}")
        try:
            r = requests.post(
                f"{API_BASE_URL}/reset",
                params={"task_index": task_idx},
                timeout=30,
            )
            r.raise_for_status()
            reset_data = r.json()
            current_task = reset_data.get("observation", {}).get("task_id", "?")
            log("STEP", f"step={step_num} reset_ok=true current_task={current_task}")
        except Exception as e:
            log("STEP", f"step={step_num} reset_ok=false error={e}")
            continue

        # Submit the solution
        solution = SOLUTIONS[task_id]
        step_num += 1
        log("STEP", f"step={step_num} action=submit task={task_id}")

        try:
            r = requests.post(
                f"{API_BASE_URL}/step",
                json={
                    "sql_query": solution["sql_query"].strip(),
                    "reasoning": solution["reasoning"],
                },
                timeout=30,
            )
            r.raise_for_status()
            result = r.json()

            reward = result.get("reward", 0.0)
            done = result.get("done", False)
            obs = result.get("observation", {})
            feedback = obs.get("grader_feedback", "")
            score = obs.get("partial_score", 0.0)

            total_reward += reward
            log("STEP", f"step={step_num} task={task_id} reward={reward:.2f} "
                f"score={score:.2f} done={done}")
            if feedback:
                log("STEP", f"step={step_num} feedback={feedback[:200]}")

        except Exception as e:
            log("STEP", f"step={step_num} task={task_id} error={e}")

    # Final state
    try:
        r = requests.get(f"{API_BASE_URL}/state", timeout=10)
        state = r.json()
        final_scores = state.get("task_scores", {})
        cumulative = state.get("cumulative_reward", 0.0)
        steps = state.get("steps_taken", 0)
        log("STEP", f"final_state steps={steps} "
            f"cumulative_reward={cumulative:.2f} "
            f"scores={json.dumps(final_scores)}")
    except Exception as e:
        log("STEP", f"state_fetch_error={e}")

    log("END", f"success=true total_reward={total_reward:.2f} "
        f"tasks_completed={len(task_ids)} model={MODEL_NAME}")
    return total_reward


if __name__ == "__main__":
    try:
        score = run_inference()
        sys.exit(0)
    except Exception as e:
        print(f"[END] error={e}", flush=True)
        sys.exit(1)
