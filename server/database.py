# SQLOps OpenEnv
# Designed by K. Ajay John Paul
# B.Tech CSE — KL University, Hyderabad
# OpenEnv Hackathon 2024

"""
SQLite database: TechCorp Operations DB.
6 tables, 400+ deterministic rows, realistic enterprise data.
"""

import sqlite3
import os

# ─── Schema DDL ─────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    budget REAL NOT NULL,
    location TEXT NOT NULL,
    manager_id INTEGER
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    hire_date TEXT NOT NULL,
    salary REAL NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(id),
    manager_id INTEGER REFERENCES employees(id),
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(id),
    start_date TEXT NOT NULL,
    end_date TEXT,
    budget REAL NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('active','completed','on_hold','cancelled'))
);

CREATE TABLE IF NOT EXISTS project_assignments (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    role TEXT NOT NULL,
    hours_allocated REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    product_name TEXT NOT NULL,
    amount REAL NOT NULL,
    sale_date TEXT NOT NULL,
    region TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS performance_reviews (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    review_date TEXT NOT NULL,
    rating REAL NOT NULL CHECK(rating >= 1.0 AND rating <= 5.0),
    reviewer_id INTEGER NOT NULL REFERENCES employees(id),
    comments TEXT
);
"""

# ─── Seed Data ──────────────────────────────────────────────────────────

DEPARTMENTS = [
    (1, "Engineering",      2500000, "San Francisco", 1),
    (2, "Sales",            1800000, "New York",      9),
    (3, "Marketing",        1200000, "New York",      16),
    (4, "Human Resources",   800000, "Chicago",       22),
    (5, "Finance",           950000, "Chicago",       27),
    (6, "Operations",       1100000, "San Francisco", 33),
    (7, "Product",          1500000, "Seattle",       39),
    (8, "Legal",             700000, "Chicago",       46),
]

EMPLOYEES = [
    # Engineering (dept 1) — 8 employees, 1 inactive
    ( 1, "Sarah",    "Chen",       "sarah.chen@techcorp.com",       "2020-03-15", 185000, 1, None, 1),
    ( 2, "David",    "Kim",        "david.kim@techcorp.com",        "2021-06-01", 145000, 1, 1,    1),
    ( 3, "Emily",    "Rodriguez",  "emily.rodriguez@techcorp.com",  "2020-09-20", 155000, 1, 1,    1),
    ( 4, "James",    "Wilson",     "james.wilson@techcorp.com",     "2022-01-10", 130000, 1, 1,    1),
    ( 5, "Priya",    "Patel",      "priya.patel@techcorp.com",      "2023-04-15", 140000, 1, 1,    1),
    ( 6, "Alex",     "Thompson",   "alex.thompson@techcorp.com",    "2024-02-01", 125000, 1, 1,    1),
    ( 7, "Maria",    "Garcia",     "maria.garcia@techcorp.com",     "2024-07-15", 135000, 1, 1,    1),
    ( 8, "Robert",   "Chang",      "robert.chang@techcorp.com",     "2021-11-30", 120000, 1, 1,    0),
    # Sales (dept 2) — 7 employees, all active
    ( 9, "Michael",  "Johnson",    "michael.johnson@techcorp.com",  "2019-08-01", 130000, 2, None, 1),
    (10, "Lisa",     "Wang",       "lisa.wang@techcorp.com",        "2022-03-15",  95000, 2, 9,    1),
    (11, "Chris",    "Brown",      "chris.brown@techcorp.com",      "2023-06-01",  88000, 2, 9,    1),
    (12, "Jennifer", "Davis",      "jennifer.davis@techcorp.com",   "2024-01-15",  85000, 2, 9,    1),
    (13, "Mark",     "Anderson",   "mark.anderson@techcorp.com",    "2024-09-01",  78000, 2, 9,    1),
    (14, "Sophia",   "Martinez",   "sophia.martinez@techcorp.com",  "2023-11-20",  72000, 2, 9,    1),
    (15, "Tom",      "Wilson",     "tom.wilson@techcorp.com",       "2025-01-10",  65000, 2, 9,    1),
    # Marketing (dept 3) — 6 employees, 1 inactive
    (16, "Amanda",   "Foster",     "amanda.foster@techcorp.com",    "2020-02-01", 135000, 3, None, 1),
    (17, "Ryan",     "Lee",        "ryan.lee@techcorp.com",         "2022-07-15", 110000, 3, 16,   1),
    (18, "Jessica",  "Taylor",     "jessica.taylor@techcorp.com",   "2023-09-01",  95000, 3, 16,   1),
    (19, "Daniel",   "Park",       "daniel.park@techcorp.com",      "2024-03-15",  88000, 3, 16,   1),
    (20, "Michelle", "Green",      "michelle.green@techcorp.com",   "2024-08-01",  72000, 3, 16,   1),
    (21, "Kevin",    "White",      "kevin.white@techcorp.com",      "2025-02-01",  80000, 3, 16,   0),
    # Human Resources (dept 4) — 5 employees, all active
    (22, "Laura",    "Mitchell",   "laura.mitchell@techcorp.com",   "2019-06-15", 115000, 4, None, 1),
    (23, "Brian",    "Cooper",     "brian.cooper@techcorp.com",     "2021-08-01",  90000, 4, 22,   1),
    (24, "Amy",      "Nelson",     "amy.nelson@techcorp.com",       "2023-01-15",  85000, 4, 22,   1),
    (25, "Steven",   "Carter",     "steven.carter@techcorp.com",    "2024-05-01",  72000, 4, 22,   1),
    (26, "Nicole",   "Adams",      "nicole.adams@techcorp.com",     "2024-10-15",  60000, 4, 22,   1),
    # Finance (dept 5) — 6 employees, all active
    (27, "Patricia", "Morgan",     "patricia.morgan@techcorp.com",  "2019-12-01", 150000, 5, None, 1),
    (28, "Andrew",   "Ross",       "andrew.ross@techcorp.com",      "2020-10-15", 115000, 5, 27,   1),
    (29, "Elizabeth","Clark",       "elizabeth.clark@techcorp.com",  "2022-04-01", 108000, 5, 27,   1),
    (30, "Thomas",   "Baker",      "thomas.baker@techcorp.com",     "2023-07-20",  95000, 5, 27,   1),
    (31, "Catherine","Reed",       "catherine.reed@techcorp.com",   "2024-02-15",  90000, 5, 27,   1),
    (32, "William",  "Turner",     "william.turner@techcorp.com",   "2024-11-01",  85000, 5, 27,   1),
    # Operations (dept 6) — 6 employees, 1 inactive
    (33, "Richard",  "Harris",     "richard.harris@techcorp.com",   "2020-01-15", 115000, 6, None, 1),
    (34, "Karen",    "Scott",      "karen.scott@techcorp.com",      "2021-05-01",  92000, 6, 33,   1),
    (35, "Paul",     "Evans",      "paul.evans@techcorp.com",       "2022-08-15",  85000, 6, 33,   1),
    (36, "Nancy",    "Moore",      "nancy.moore@techcorp.com",      "2023-03-01",  68000, 6, 33,   1),
    (37, "George",   "Hill",       "george.hill@techcorp.com",      "2024-06-15",  62000, 6, 33,   1),
    (38, "Barbara",  "Young",      "barbara.young@techcorp.com",    "2025-01-15",  66000, 6, 33,   0),
    # Product (dept 7) — 7 employees, all active
    (39, "Christopher","Lewis",    "christopher.lewis@techcorp.com","2019-04-01", 165000, 7, None, 1),
    (40, "Angela",   "Wright",     "angela.wright@techcorp.com",    "2021-02-15", 125000, 7, 39,   1),
    (41, "Matthew",  "Roberts",    "matthew.roberts@techcorp.com",  "2022-06-01", 118000, 7, 39,   1),
    (42, "Stephanie","Hall",       "stephanie.hall@techcorp.com",   "2023-10-15", 112000, 7, 39,   1),
    (43, "Jason",    "King",       "jason.king@techcorp.com",       "2024-04-01", 108000, 7, 39,   1),
    (44, "Rebecca",  "Allen",      "rebecca.allen@techcorp.com",    "2024-08-15", 100000, 7, 39,   1),
    (45, "Eric",     "Brooks",     "eric.brooks@techcorp.com",      "2025-03-01",  95000, 7, 39,   1),
    # Legal (dept 8) — 5 employees, all active
    (46, "Diana",    "Campbell",   "diana.campbell@techcorp.com",   "2019-01-15", 155000, 8, None, 1),
    (47, "Jonathan", "Bell",       "jonathan.bell@techcorp.com",    "2020-07-01", 115000, 8, 46,   1),
    (48, "Victoria", "Hayes",      "victoria.hayes@techcorp.com",   "2022-09-15", 108000, 8, 46,   1),
    (49, "Samuel",   "Murphy",     "samuel.murphy@techcorp.com",    "2023-12-01",  98000, 8, 46,   1),
    (50, "Rachel",   "Price",      "rachel.price@techcorp.com",     "2024-07-01",  85000, 8, 46,   1),
]

PROJECTS = [
    ( 1, "Cloud Migration",       1, "2024-01-01", "2024-12-31", 500000, "active"),
    ( 2, "Mobile App v2",         1, "2024-03-01", "2025-06-30", 350000, "active"),
    ( 3, "Data Pipeline",         1, "2023-06-01", "2024-03-31", 200000, "completed"),
    ( 4, "Q4 Sales Campaign",     2, "2024-10-01", "2024-12-31", 150000, "active"),
    ( 5, "Brand Refresh",         3, "2024-05-01", "2024-11-30", 100000, "completed"),
    ( 6, "Social Media Strategy", 3, "2024-09-01", "2025-03-31",  80000, "active"),
    ( 7, "HR Portal",             4, "2024-02-01", "2024-08-31", 120000, "completed"),
    ( 8, "Compliance Audit",      5, "2024-01-15", "2024-06-30",  75000, "completed"),
    ( 9, "Cost Optimization",     6, "2024-04-01", "2025-01-31",  90000, "active"),
    (10, "Product Roadmap 2025",  7, "2024-07-01", "2025-06-30", 200000, "active"),
    (11, "API Platform",          1, "2025-01-01", "2025-12-31", 400000, "active"),
    (12, "Customer Portal",       7, "2024-11-01", "2025-04-30", 180000, "active"),
    (13, "Legal Compliance",      8, "2024-03-01", "2024-09-30",  60000, "completed"),
    (14, "Revenue Forecast",      5, "2024-08-01", "2025-02-28",  95000, "on_hold"),
    (15, "Office Relocation",     6, "2025-03-01", "2025-08-31", 250000, "active"),
]

PROJECT_ASSIGNMENTS = [
    ( 1,  1,  1, "Tech Lead",          40),
    ( 2,  2,  1, "Backend Developer",  30),
    ( 3,  3,  2, "Frontend Developer", 25),
    ( 4,  4,  2, "Backend Developer",  30),
    ( 5,  5,  1, "DevOps Engineer",    20),
    ( 6,  6,  1, "Junior Developer",   35),
    ( 7,  7, 11, "Senior Developer",   40),
    ( 8,  2, 11, "Architecture Lead",  15),
    ( 9,  3,  3, "Data Engineer",      30),
    (10,  9,  4, "Campaign Manager",   25),
    (11, 10,  4, "Sales Lead",         20),
    (12, 11,  4, "Analyst",            15),
    (13, 16,  5, "Creative Director",  20),
    (14, 17,  6, "Content Lead",       30),
    (15, 18,  6, "Social Manager",     25),
    (16, 19,  6, "Content Creator",    20),
    (17, 22,  7, "Project Lead",       30),
    (18, 23,  7, "HR Specialist",      25),
    (19, 27,  8, "Finance Lead",       20),
    (20, 29,  8, "Auditor",            25),
    (21, 33,  9, "Operations Lead",    35),
    (22, 34,  9, "Process Analyst",    25),
    (23, 35, 15, "Logistics Lead",     30),
    (24, 39, 10, "Product Lead",       35),
    (25, 40, 10, "UX Designer",        25),
    (26, 41, 12, "Full Stack Dev",     30),
    (27, 42, 12, "UI Designer",        25),
    (28, 46, 13, "Legal Lead",         25),
    (29, 47, 13, "Paralegal",          30),
    (30, 48, 13, "Compliance Officer", 20),
    (31, 43, 10, "PM Associate",       20),
    (32, 44, 12, "QA Engineer",        25),
]

# Deterministic sales data across 15 months (2024-01 → 2025-03)
PRODUCTS = ["Enterprise License", "Pro Subscription", "Consulting Package",
            "Training Bundle", "Support Plan"]
REGIONS  = ["North America", "Europe", "Asia Pacific", "Latin America"]

# Monthly targets for realistic growth pattern
_MONTHLY_TARGETS = [
    ("2024-01", 45000), ("2024-02", 52000), ("2024-03", 48000),
    ("2024-04", 56000), ("2024-05", 63000), ("2024-06", 58000),
    ("2024-07", 67000), ("2024-08", 72000), ("2024-09", 79000),
    ("2024-10", 86000), ("2024-11", 93000), ("2024-12", 88000),
    ("2025-01", 75000), ("2025-02", 82000), ("2025-03", 96000),
]

def _generate_sales():
    """Generate ~200 deterministic sales records."""
    sales = []
    sale_id = 1
    sales_employees = [9, 10, 11, 12, 13, 14, 15]  # Sales dept

    for month_str, target in _MONTHLY_TARGETS:
        year, month = month_str.split("-")
        num_sales = max(10, target // 5000)
        base_amount = target / num_sales

        for i in range(num_sales):
            emp_id = sales_employees[i % len(sales_employees)]
            product = PRODUCTS[i % len(PRODUCTS)]
            region = REGIONS[i % len(REGIONS)]
            day = min(1 + i * 2, 28)
            # Vary amounts deterministically
            multiplier = 0.6 + 0.8 * ((i * 7 + sale_id) % 10) / 10
            amount = round(base_amount * multiplier, 2)
            quantity = 1 + (i + sale_id) % 5
            sales.append((sale_id, emp_id, product, amount, f"{year}-{month}-{day:02d}",
                          region, quantity))
            sale_id += 1

    return sales

SALES = _generate_sales()

PERFORMANCE_REVIEWS = [
    # (id, emp_id, review_date, rating, reviewer_id, comments)
    ( 1,  1, "2024-06-15", 4.8, 39, "Exceptional technical leadership on Cloud Migration."),
    ( 2,  2, "2024-06-15", 4.2, 1,  "Strong backend skills, great team player."),
    ( 3,  3, "2024-06-15", 4.5, 1,  "Excellent frontend work on Mobile App v2."),
    ( 4,  4, "2024-06-15", 3.8, 1,  "Solid contributor, needs more initiative on architecture."),
    ( 5,  5, "2024-06-15", 4.0, 1,  "Great progress in first year, strong potential."),
    ( 6,  6, "2024-06-15", 3.5, 1,  "Good start, ramping up quickly on cloud tools."),
    ( 7,  9, "2024-06-15", 4.6, 39, "Top sales performer, Q4 campaign was outstanding."),
    ( 8, 10, "2024-06-15", 4.0,  9, "Consistent pipeline management and client relations."),
    ( 9, 11, "2024-06-15", 3.7,  9, "Good hunter mentality, needs better follow-through."),
    (10, 12, "2024-06-15", 3.5,  9, "Shows promise in enterprise segment."),
    (11, 14, "2024-06-15", 3.9,  9, "Solid mid-market results, expanding territory."),
    (12, 16, "2024-06-15", 4.3, 39, "Brand refresh was well-executed and on time."),
    (13, 17, "2024-06-15", 4.1, 16, "Creative content strategy driving engagement."),
    (14, 18, "2024-06-15", 3.6, 16, "Good social media instincts, improve reporting."),
    (15, 22, "2024-06-15", 4.4, 39, "HR portal launch was seamless, great stakeholder mgmt."),
    (16, 23, "2024-06-15", 3.8, 22, "Reliable HR ops, growing into policy design."),
    (17, 27, "2024-06-15", 4.5, 39, "Compliance audit completed ahead of schedule."),
    (18, 28, "2024-06-15", 4.0, 27, "Strong financial modeling and forecasting."),
    (19, 29, "2024-06-15", 3.9, 27, "Thorough audit work, meticulous documentation."),
    (20, 33, "2024-06-15", 4.2, 39, "Cost optimization initiative saving 15% of OpEx."),
    (21, 34, "2024-06-15", 3.8, 33, "Good process analysis, improving throughput."),
    (22, 39, "2024-06-15", 4.7, 39, "Visionary product roadmap, excellent cross-team collab."),
    (23, 40, "2024-06-15", 4.1, 39, "Strong UX research driving measurable improvements."),
    (24, 41, "2024-06-15", 3.9, 39, "Reliable full-stack delivery on Customer Portal."),
    (25, 46, "2024-06-15", 4.6, 39, "Excellent legal compliance framework established."),
    (26, 47, "2024-06-15", 4.0, 46, "Thorough contract review process."),
    (27, 48, "2024-06-15", 3.7, 46, "Good compliance monitoring, building expertise."),
    (28,  7, "2024-12-15", 3.9,  1, "Quick learner, contributing to API Platform."),
    (29, 42, "2024-12-15", 4.2, 39, "Outstanding UI design on Customer Portal."),
    (30, 49, "2024-12-15", 3.6, 46, "Developing well in regulatory research."),
]


# ─── Database Creation ──────────────────────────────────────────────────

def seed_database(db_path: str = ":memory:") -> sqlite3.Connection:
    """Create the TechCorp DB, seed all tables, return connection."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=OFF")  # OFF during bulk insert

    conn.executescript(SCHEMA_SQL)

    conn.executemany(
        "INSERT INTO departments VALUES (?,?,?,?,?)", DEPARTMENTS)
    conn.executemany(
        "INSERT INTO employees VALUES (?,?,?,?,?,?,?,?,?)", EMPLOYEES)
    conn.executemany(
        "INSERT INTO projects VALUES (?,?,?,?,?,?,?)", PROJECTS)
    conn.executemany(
        "INSERT INTO project_assignments VALUES (?,?,?,?,?)", PROJECT_ASSIGNMENTS)
    conn.executemany(
        "INSERT INTO sales VALUES (?,?,?,?,?,?,?)", SALES)
    conn.executemany(
        "INSERT INTO performance_reviews VALUES (?,?,?,?,?,?)", PERFORMANCE_REVIEWS)

    conn.execute("PRAGMA foreign_keys=ON")
    conn.commit()
    return conn


def get_schema_hint() -> str:
    """Return human-readable CREATE TABLE statements for the agent."""
    return SCHEMA_SQL.strip()


def execute_query(conn: sqlite3.Connection, sql: str):
    """Execute SQL and return (columns, rows) or raise on error."""
    cursor = conn.execute(sql)
    if cursor.description is None:
        return [], []
    columns = [desc[0] for desc in cursor.description]
    rows = [list(row) for row in cursor.fetchall()]
    return columns, rows


def format_result_table(columns: list, rows: list, max_rows: int = 50) -> str:
    """Pretty-print query results as an ASCII table."""
    if not columns:
        return "(no results)"
    display_rows = rows[:max_rows]
    col_widths = [max(len(str(c)), *(len(str(r[i])) for r in display_rows))
                  for i, c in enumerate(columns)]
    # Clamp column widths
    col_widths = [min(w, 30) for w in col_widths]

    header = " | ".join(str(c).ljust(col_widths[i]) for i, c in enumerate(columns))
    sep = "-+-".join("-" * w for w in col_widths)
    lines = [header, sep]
    for row in display_rows:
        line = " | ".join(str(row[i])[:30].ljust(col_widths[i])
                          for i in range(len(columns)))
        lines.append(line)
    if len(rows) > max_rows:
        lines.append(f"... ({len(rows) - max_rows} more rows)")
    return "\n".join(lines)


if __name__ == "__main__":
    # Quick smoke test
    conn = seed_database()
    for table in ["departments", "employees", "projects", "project_assignments",
                  "sales", "performance_reviews"]:
        cols, rows = execute_query(conn, f"SELECT COUNT(*) AS cnt FROM {table}")
        print(f"{table}: {rows[0][0]} rows")
    conn.close()
    print("✓ Database seeded successfully")
