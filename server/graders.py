# SQLOps OpenEnv
# Designed by K. Ajay John Paul
# B.Tech CSE — KL University, Hyderabad
# OpenEnv Hackathon 2024

"""
6-level partial-credit SQL grader.
Compares agent SQL output against reference SQL output.

Scoring tiers:
  0.00 — query failed to execute
  0.15 — executes but wrong columns AND wrong data
  0.30 — correct column count, wrong names or wrong data
  0.50 — correct columns, partial row overlap
  0.75 — correct columns, > 80% row match
  1.00 — perfect match (columns + data + optional order)
"""

import sqlite3
from typing import Tuple, List


def _normalize_value(v) -> str:
    """Normalize a cell value for comparison."""
    if v is None:
        return "NULL"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v).strip().lower()


def _normalize_col(c: str) -> str:
    """Normalize column name."""
    return c.strip().lower().replace(" ", "_")


def _rows_to_set(rows: List[list]) -> set:
    """Convert rows to a set of tuples for order-independent comparison."""
    return set(tuple(_normalize_value(v) for v in row) for row in rows)


def _rows_to_list(rows: List[list]) -> list:
    """Convert rows to list of normalized tuples for ordered comparison."""
    return [tuple(_normalize_value(v) for v in row) for row in rows]


def grade_sql(
    conn: sqlite3.Connection,
    agent_sql: str,
    reference_sql: str,
    expected_columns: List[str],
    check_order: bool = False,
) -> Tuple[float, str]:
    """
    Grade the agent's SQL against the reference.

    Returns:
        (score, feedback) where score is float 0.0–1.0
    """
    # ── Step 1: Execute agent query ──────────────────────────────
    try:
        cursor = conn.execute(agent_sql)
        if cursor.description is None:
            return 0.0, "Query returned no results. Use a SELECT statement."
        agent_cols = [desc[0] for desc in cursor.description]
        agent_rows = [list(row) for row in cursor.fetchall()]
    except Exception as e:
        return 0.0, f"SQL Error: {str(e)}"

    # ── Step 2: Execute reference query ─────────────────────────
    try:
        cursor = conn.execute(reference_sql)
        ref_cols = [desc[0] for desc in cursor.description]
        ref_rows = [list(row) for row in cursor.fetchall()]
    except Exception as e:
        return 0.0, f"Internal grader error: {str(e)}"

    # ── Step 3: Column comparison ───────────────────────────────
    agent_cols_norm = [_normalize_col(c) for c in agent_cols]
    ref_cols_norm = [_normalize_col(c) for c in ref_cols]
    expected_norm = [_normalize_col(c) for c in expected_columns]

    # Check column count
    if len(agent_cols) != len(ref_cols):
        return 0.15, (
            f"Wrong number of columns: got {len(agent_cols)}, expected {len(ref_cols)}. "
            f"Expected columns: {', '.join(expected_columns)}"
        )

    # Check column names match expected
    cols_match = agent_cols_norm == expected_norm or agent_cols_norm == ref_cols_norm
    if not cols_match:
        # Fuzzy check — allow any order if names are a subset
        if set(agent_cols_norm) == set(expected_norm):
            cols_match = True  # Right names, possibly different order (we'll check data next)
        else:
            return 0.30, (
                f"Column names don't match. Got: {', '.join(agent_cols)}. "
                f"Expected: {', '.join(expected_columns)}"
            )

    # ── Step 4: Data comparison ─────────────────────────────────
    if len(agent_rows) == 0 and len(ref_rows) == 0:
        return 1.0, "Perfect — both queries returned empty result sets."

    if len(agent_rows) == 0:
        return 0.30, f"Query returned 0 rows, expected {len(ref_rows)} rows."

    # Compare as sets (order-independent first)
    agent_set = _rows_to_set(agent_rows)
    ref_set = _rows_to_set(ref_rows)

    overlap = agent_set & ref_set
    overlap_ratio = len(overlap) / max(len(ref_set), 1)
    extra_rows = len(agent_set - ref_set)

    # ── Step 5: Order check (if required) ───────────────────────
    order_ok = True
    if check_order and overlap_ratio >= 0.8:
        agent_list = _rows_to_list(agent_rows)
        ref_list = _rows_to_list(ref_rows)
        order_ok = agent_list == ref_list

    # ── Step 6: Score assignment ────────────────────────────────
    if overlap_ratio == 1.0 and extra_rows == 0:
        if check_order and not order_ok:
            return 0.75, (
                "All data correct but in wrong order. "
                "Check your ORDER BY clause."
            )
        return 1.0, "Perfect match! All columns and data are correct."

    if overlap_ratio >= 0.8:
        detail = f"{len(overlap)}/{len(ref_set)} rows match"
        if extra_rows > 0:
            detail += f", {extra_rows} extra rows"
        return 0.75, f"Close! {detail}. Check edge cases or filters."

    if overlap_ratio >= 0.4:
        return 0.50, (
            f"Partial match: {len(overlap)}/{len(ref_set)} rows overlap. "
            f"Check your JOINs, WHERE conditions, and GROUP BY."
        )

    return 0.30, (
        f"Low overlap: only {len(overlap)}/{len(ref_set)} rows match. "
        f"Review your query logic. Expected {len(ref_set)} rows, got {len(agent_rows)}."
    )
