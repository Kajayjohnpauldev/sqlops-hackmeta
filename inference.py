#!/usr/bin/env python3
# SQLOps OpenEnv
# Designed by K. Ajay John Paul
# B.Tech CSE — KL University, Hyderabad
# OpenEnv Hackathon 2024

"""
Baseline inference script.
Runs through all 3 tasks using hardcoded reference-quality SQL.
Follows exact OpenEnv log format: [START], [STEP], [END].
"""

import os
import sys
import json
import time
import requests

# ─── Configuration ──────────────────────────────────────────────────

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:7860")
TASK_NAME = os.getenv("TASK_NAME", "all")


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


def run_inference():
    """Run the baseline agent through all tasks."""
    log("START", f"SQLOps Baseline Inference — {BASE_URL}")
    total_reward = 0.0
    task_ids = list(SOLUTIONS.keys())

    if TASK_NAME != "all" and TASK_NAME in SOLUTIONS:
        task_ids = [TASK_NAME]

    for task_idx, task_id in enumerate(task_ids):
        # Reset to the specific task
        log("STEP", f"Resetting to task {task_idx}: {task_id}")
        try:
            r = requests.post(f"{BASE_URL}/reset", params={"task_index": task_idx}, timeout=30)
            r.raise_for_status()
            reset_data = r.json()
            log("STEP", f"Reset OK — current task: {reset_data.get('observation', {}).get('task_id', '?')}")
        except Exception as e:
            log("STEP", f"Reset failed: {e}")
            continue

        # Submit the solution
        solution = SOLUTIONS[task_id]
        log("STEP", f"Submitting solution for {task_id}")

        try:
            r = requests.post(
                f"{BASE_URL}/step",
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
            log("STEP", f"task={task_id} reward={reward:.2f} score={score:.2f} done={done}")
            log("STEP", f"feedback: {feedback[:120]}")

        except Exception as e:
            log("STEP", f"Step failed for {task_id}: {e}")

    # Final state
    try:
        r = requests.get(f"{BASE_URL}/state", timeout=10)
        state = r.json()
        log("STEP", f"Final state: steps={state.get('steps_taken', 0)} "
            f"cumulative_reward={state.get('cumulative_reward', 0.0):.2f} "
            f"scores={json.dumps(state.get('task_scores', {}))}")
    except Exception:
        pass

    log("END", f"Total reward: {total_reward:.2f}")
    return total_reward


if __name__ == "__main__":
    score = run_inference()
    sys.exit(0 if score > 0 else 1)
