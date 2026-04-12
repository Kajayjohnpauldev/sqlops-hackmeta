"""Quick smoke test for SQLOps."""
import sys
sys.path.insert(0, '.')

print("=" * 50)
print("SQLOps Smoke Test")
print("=" * 50)

# Test 1: Database
print("\n[1] Testing database...")
from server.database import seed_database, execute_query
conn = seed_database()
tables = ['departments','employees','projects','project_assignments','sales','performance_reviews']
for t in tables:
    cols, rows = execute_query(conn, f"SELECT COUNT(*) FROM {t}")
    print(f"  {t}: {rows[0][0]} rows")
print("  ✓ Database OK")

# Test 2: Grader
print("\n[2] Testing grader...")
from server.graders import grade_sql
score, fb = grade_sql(
    conn,
    "SELECT region, ROUND(SUM(amount),2) AS total_revenue, SUM(quantity) AS total_quantity FROM sales GROUP BY region ORDER BY total_revenue DESC",
    "SELECT region, ROUND(SUM(amount),2) AS total_revenue, SUM(quantity) AS total_quantity FROM sales GROUP BY region ORDER BY total_revenue DESC",
    ["region", "total_revenue", "total_quantity"],
    check_order=True
)
print(f"  Perfect match score: {score} — {fb}")
assert score == 1.0, f"Expected 1.0, got {score}"

score2, fb2 = grade_sql(
    conn,
    "SELECT region FROM sales GROUP BY region",
    "SELECT region, ROUND(SUM(amount),2) AS total_revenue, SUM(quantity) AS total_quantity FROM sales GROUP BY region ORDER BY total_revenue DESC",
    ["region", "total_revenue", "total_quantity"],
    check_order=True
)
print(f"  Wrong columns score: {score2} — {fb2}")
assert score2 < 1.0
print("  ✓ Grader OK")

# Test 3: Environment
print("\n[3] Testing environment...")
from server.environment import SQLOpsEnvironment
env = SQLOpsEnvironment()
state = env.state()
print(f"  Initial state: task={state.current_task_id}, steps={state.steps_taken}")

from models import SQLOpsAction
result = env.step(SQLOpsAction(
    sql_query="SELECT region, ROUND(SUM(amount),2) AS total_revenue, SUM(quantity) AS total_quantity FROM sales GROUP BY region ORDER BY total_revenue DESC",
    reasoning="test"
))
print(f"  Step result: reward={result.reward}, score={result.observation.partial_score}")
print(f"  Feedback: {result.observation.grader_feedback[:80]}")
print("  ✓ Environment OK")

# Test 4: Tasks
print("\n[4] Testing tasks...")
from server.tasks import TASKS
for t in TASKS:
    print(f"  {t['task_id']} ({t['difficulty']}): {t['title']}")
print("  ✓ Tasks OK")

# Test 5: Auth
print("\n[5] Testing auth...")
from server.auth import USERS, create_session, get_session
sid = create_session("boss")
sess = get_session(sid)
print(f"  Boss session: {sess['display_name']} ({sess['role']})")
sid2 = create_session("staff1")
sess2 = get_session(sid2)
print(f"  Staff session: {sess2['display_name']} ({sess2['role']})")
print("  ✓ Auth OK")

print("\n" + "=" * 50)
print("ALL TESTS PASSED ✓")
print("=" * 50)
conn.close()
