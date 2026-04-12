# SQLOps OpenEnv
# Designed by K. Ajay John Paul
# B.Tech CSE — KL University, Hyderabad
# OpenEnv Hackathon 2024

"""Typed Pydantic models for SQLOps environment."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class SQLOpsAction(BaseModel):
    """Action the agent sends — a SQL query + optional reasoning."""
    sql_query: str = Field(..., description="Valid SQL SELECT statement")
    reasoning: str = Field("", description="Optional reasoning trace from the agent")


class SQLOpsObservation(BaseModel):
    """What the agent sees after each step."""
    task_id: str = Field(..., description="Current task identifier")
    task_description: str = Field(..., description="Human-readable task description")
    schema_hint: str = Field("", description="CREATE TABLE statements for reference")
    query_result: Optional[str] = Field(None, description="Formatted query output rows")
    error_message: Optional[str] = Field(None, description="SQL error if query failed")
    expected_columns: List[str] = Field(default_factory=list, description="Expected column names")
    attempt_number: int = Field(0, description="Current attempt (1-indexed)")
    max_attempts: int = Field(5, description="Maximum allowed attempts for this task")
    partial_score: float = Field(0.0, description="Partial credit score 0.0–1.0")
    grader_feedback: str = Field("", description="Detailed grading feedback")
    difficulty: str = Field("easy", description="Task difficulty: easy | medium | hard")


class StepResult(BaseModel):
    """Returned by /step and /reset — wraps observation + reward + done."""
    observation: SQLOpsObservation
    reward: float = Field(0.0, ge=0.0, le=1.0, description="Reward signal 0.0–1.0")
    done: bool = Field(False, description="True when episode ends")
    cumulative_reward: float = Field(0.0, description="Sum of all rewards this episode")


class SQLOpsState(BaseModel):
    """Full environment state for GET /state."""
    current_task_index: int = Field(0, description="Index of current task (0–2)")
    current_task_id: str = Field("", description="Current task ID")
    steps_taken: int = Field(0, description="Total steps across all tasks")
    cumulative_reward: float = Field(0.0, description="Sum of all step rewards")
    task_scores: Dict[str, float] = Field(default_factory=dict, description="Best score per task")
    task_attempts: Dict[str, int] = Field(default_factory=dict, description="Attempts per task")
    done: bool = Field(False, description="True when all tasks completed")
    reward_history: List[float] = Field(default_factory=list, description="All rewards in order")
    author: str = Field("K. Ajay John Paul", description="Environment author")
