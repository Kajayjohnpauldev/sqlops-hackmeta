# SQLOps OpenEnv
# Designed by K. Ajay John Paul
# B.Tech CSE — KL University, Hyderabad
# OpenEnv Hackathon 2024

"""
Core environment: step() / reset() / state() API.
Manages task progression, grading, reward history.
"""

import os
import sqlite3
from typing import Optional, List, Dict

from models import SQLOpsAction, SQLOpsObservation, StepResult, SQLOpsState
from server.database import seed_database, get_schema_hint, execute_query, format_result_table
from server.tasks import TASKS, get_task_by_index
from server.graders import grade_sql


class SQLOpsEnvironment:
    """OpenEnv-compliant environment for SQL operations training."""

    def __init__(self):
        self._db: Optional[sqlite3.Connection] = None
        self._current_task_index: int = 0
        self._current_task: Optional[dict] = None
        self._attempt_number: int = 0
        self._steps_taken: int = 0
        self._cumulative_reward: float = 0.0
        self._task_scores: Dict[str, float] = {}
        self._task_attempts: Dict[str, int] = {}
        self._reward_history: List[float] = []
        self._done: bool = False
        self._last_observation: Optional[SQLOpsObservation] = None

        # Auto-initialize
        self._init_db()
        self._load_task(0)

    # ── Private helpers ─────────────────────────────────────────────

    def _init_db(self):
        """Create or re-create the in-memory database."""
        if self._db:
            try:
                self._db.close()
            except Exception:
                pass
        self._db = seed_database()

    def _load_task(self, index: int):
        """Load a task by index and reset attempt counter."""
        self._current_task_index = index
        self._current_task = get_task_by_index(index)
        task_id = self._current_task["task_id"]
        if task_id not in self._task_scores:
            self._task_scores[task_id] = 0.0
        if task_id not in self._task_attempts:
            self._task_attempts[task_id] = 0
        self._attempt_number = self._task_attempts[task_id]

    def _make_observation(
        self,
        query_result: Optional[str] = None,
        error_message: Optional[str] = None,
        partial_score: float = 0.0,
        grader_feedback: str = "",
    ) -> SQLOpsObservation:
        """Build an observation from current state + optional results."""
        t = self._current_task
        obs = SQLOpsObservation(
            task_id=t["task_id"],
            task_description=t["description"],
            schema_hint=get_schema_hint(),
            query_result=query_result,
            error_message=error_message,
            expected_columns=t["expected_columns"],
            attempt_number=self._attempt_number,
            max_attempts=t["max_attempts"],
            partial_score=partial_score,
            grader_feedback=grader_feedback,
            difficulty=t["difficulty"],
        )
        self._last_observation = obs
        return obs

    # ── Public API ──────────────────────────────────────────────────

    def reset(self, task_index: int = 0) -> StepResult:
        """Reset environment to a specific task (0-indexed)."""
        self._init_db()
        self._current_task_index = max(0, min(task_index, len(TASKS) - 1))
        self._steps_taken = 0
        self._cumulative_reward = 0.0
        self._task_scores = {t["task_id"]: 0.0 for t in TASKS}
        self._task_attempts = {t["task_id"]: 0 for t in TASKS}
        self._reward_history = []
        self._done = False

        self._load_task(self._current_task_index)

        obs = self._make_observation(
            grader_feedback="Environment reset. Write your SQL query."
        )
        return StepResult(
            observation=obs,
            reward=0.0,
            done=False,
            cumulative_reward=0.0,
        )

    def step(self, action: SQLOpsAction) -> StepResult:
        """Execute one agent step: run SQL, grade, return reward."""
        if self._done:
            obs = self._make_observation(
                grader_feedback="All tasks completed. Call /reset to start over."
            )
            return StepResult(
                observation=obs,
                reward=0.0,
                done=True,
                cumulative_reward=self._cumulative_reward,
            )

        t = self._current_task
        task_id = t["task_id"]

        # Increment attempt
        self._attempt_number += 1
        self._task_attempts[task_id] = self._attempt_number
        self._steps_taken += 1

        # Execute and grade
        sql = action.sql_query.strip()
        if not sql:
            obs = self._make_observation(
                error_message="Empty query. Please provide a valid SQL SELECT statement.",
                partial_score=0.0,
                grader_feedback="No query submitted.",
            )
            self._reward_history.append(0.0)
            return StepResult(
                observation=obs,
                reward=0.0,
                done=False,
                cumulative_reward=self._cumulative_reward,
            )

        # Grade against reference
        score, feedback = grade_sql(
            conn=self._db,
            agent_sql=sql,
            reference_sql=t["reference_sql"],
            expected_columns=t["expected_columns"],
            check_order=t.get("check_order", False),
        )

        # Track best score for this task
        self._task_scores[task_id] = max(self._task_scores[task_id], score)
        self._cumulative_reward += score
        self._reward_history.append(score)

        # Try to get query results for display
        query_result = None
        error_message = None
        try:
            cols, rows = execute_query(self._db, sql)
            query_result = format_result_table(cols, rows)
        except Exception as e:
            error_message = str(e)

        # Check if we should advance to next task
        task_done = False
        if score >= 1.0:
            task_done = True
            feedback += " Moving to next task."
        elif self._attempt_number >= t["max_attempts"]:
            task_done = True
            feedback += f" Max attempts ({t['max_attempts']}) reached. Moving on."

        if task_done:
            next_index = self._current_task_index + 1
            if next_index < len(TASKS):
                self._load_task(next_index)
                feedback += f" Now on: {self._current_task['title']}"
            else:
                self._done = True
                feedback += " All tasks completed!"

        obs = self._make_observation(
            query_result=query_result,
            error_message=error_message,
            partial_score=score,
            grader_feedback=feedback,
        )

        return StepResult(
            observation=obs,
            reward=score,
            done=self._done,
            cumulative_reward=self._cumulative_reward,
        )

    def state(self) -> SQLOpsState:
        """Return full environment state."""
        return SQLOpsState(
            current_task_index=self._current_task_index,
            current_task_id=self._current_task["task_id"] if self._current_task else "",
            steps_taken=self._steps_taken,
            cumulative_reward=round(self._cumulative_reward, 4),
            task_scores={k: round(v, 4) for k, v in self._task_scores.items()},
            task_attempts=self._task_attempts,
            done=self._done,
            reward_history=[round(r, 4) for r in self._reward_history],
            author="K. Ajay John Paul",
        )

    def get_reward_history(self) -> List[float]:
        """Return full reward history for analytics."""
        return [round(r, 4) for r in self._reward_history]

    def run_query(self, sql: str) -> dict:
        """Run arbitrary SQL for the SQL Lab (no grading)."""
        try:
            cols, rows = execute_query(self._db, sql)
            return {
                "success": True,
                "columns": cols,
                "rows": rows,
                "row_count": len(rows),
                "formatted": format_result_table(cols, rows),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "columns": [],
                "rows": [],
                "row_count": 0,
                "formatted": "",
            }

    def get_reference_sql(self, task_index: int) -> str:
        """Return reference SQL for a task (boss only)."""
        t = get_task_by_index(task_index)
        return t["reference_sql"].strip()
