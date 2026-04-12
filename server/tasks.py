# SQLOps OpenEnv
# Designed by K. Ajay John Paul
# B.Tech CSE — KL University, Hyderabad
# OpenEnv Hackathon 2024

"""
Task definitions: 3 tasks × ~3 challenges each.
Easy  → Data retrieval (SELECT / JOIN / GROUP BY)
Medium → Query debugging (find & fix broken SQL)
Hard  → Advanced analytics (CTE / window functions / subqueries)
"""

TASKS = [
    # ──────────────────────────────────────────────────────────
    # TASK 1 — EASY: Sales & Employee Data Retrieval
    # ──────────────────────────────────────────────────────────
    {
        "task_id": "sales_summary",
        "difficulty": "easy",
        "max_attempts": 5,
        "title": "Sales & Employee Data Retrieval",
        "description": (
            "Write a SQL query to compute the total revenue per sales region, "
            "sorted from highest to lowest revenue. "
            "Include columns: region, total_revenue, total_quantity."
        ),
        "expected_columns": ["region", "total_revenue", "total_quantity"],
        "reference_sql": """
            SELECT
                region,
                ROUND(SUM(amount), 2)   AS total_revenue,
                SUM(quantity)           AS total_quantity
            FROM sales
            GROUP BY region
            ORDER BY total_revenue DESC
        """,
        "check_order": True,
        "hint": "Use SUM() with GROUP BY on the sales table. ORDER BY the total descending.",
        "schema_tables": ["sales"],
    },

    # ──────────────────────────────────────────────────────────
    # TASK 2 — MEDIUM: Debug a Broken Multi-JOIN Query
    # ──────────────────────────────────────────────────────────
    {
        "task_id": "debug_query",
        "difficulty": "medium",
        "max_attempts": 7,
        "title": "Debug a Broken Multi-JOIN Query",
        "description": (
            "The following query is SUPPOSED to show ALL departments with their "
            "count of ACTIVE projects (including departments with 0 active projects), "
            "sorted by active project count descending then department name ascending.\n\n"
            "BROKEN QUERY:\n"
            "SELECT d.name AS department, COUNT(p.id) AS active_projects\n"
            "FROM departments d\n"
            "LEFT JOIN projects p ON d.id = p.department_id\n"
            "WHERE p.status = 'active'\n"
            "GROUP BY d.name\n"
            "ORDER BY active_projects DESC, d.name ASC\n\n"
            "The bug: the WHERE clause on p.status converts the LEFT JOIN into an "
            "INNER JOIN, dropping departments with 0 active projects.\n\n"
            "Fix the query so ALL 8 departments appear (with 0 for those without "
            "active projects)."
        ),
        "expected_columns": ["department", "active_projects"],
        "reference_sql": """
            SELECT
                d.name           AS department,
                COUNT(p.id)      AS active_projects
            FROM departments d
            LEFT JOIN projects p
                ON d.id = p.department_id AND p.status = 'active'
            GROUP BY d.name
            ORDER BY active_projects DESC, d.name ASC
        """,
        "check_order": True,
        "hint": (
            "Move the status filter from WHERE into the ON clause of the LEFT JOIN. "
            "That way departments without matching projects still appear with COUNT = 0."
        ),
        "schema_tables": ["departments", "projects"],
    },

    # ──────────────────────────────────────────────────────────
    # TASK 3 — HARD: Advanced CTE & Window Function Analytics
    # ──────────────────────────────────────────────────────────
    {
        "task_id": "performance_analytics",
        "difficulty": "hard",
        "max_attempts": 10,
        "title": "CTE + Window Function Performance Analytics",
        "description": (
            "Write a SQL query using CTEs and/or window functions to find:\n"
            "  1. Each department's AVERAGE performance rating\n"
            "  2. The department's RANK by average rating (highest = rank 1)\n"
            "  3. Only include departments where at least 2 reviews exist\n\n"
            "Return columns: department, avg_rating (rounded to 2 decimals), "
            "review_count, dept_rank.\n"
            "Order by dept_rank ascending."
        ),
        "expected_columns": ["department", "avg_rating", "review_count", "dept_rank"],
        "reference_sql": """
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
        "check_order": True,
        "hint": (
            "Use a CTE to compute AVG(rating) and COUNT per department (with HAVING >= 2), "
            "then apply RANK() OVER (ORDER BY avg_rating DESC) in the outer query."
        ),
        "schema_tables": ["performance_reviews", "employees", "departments"],
    },
]


def get_task(task_id: str) -> dict:
    """Look up a task by its ID. Raises KeyError if not found."""
    for t in TASKS:
        if t["task_id"] == task_id:
            return t
    raise KeyError(f"Unknown task_id: {task_id}")


def get_task_by_index(index: int) -> dict:
    """Get task by 0-based index."""
    if 0 <= index < len(TASKS):
        return TASKS[index]
    raise IndexError(f"Task index {index} out of range (0–{len(TASKS)-1})")
