# SQLOps Oracle — AI SQL Training Environment

> Designed by **K. Ajay John Paul** | B.Tech CSE | KL University, Hyderabad

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![OpenEnv Compatible](https://img.shields.io/badge/OpenEnv-Compatible-green.svg)](https://openenv.dev)

---

## 🚀 What is SQLOps?

**SQLOps** is a production-grade AI training environment where agents learn to write, debug, and analyze SQL queries against a realistic company operations database. It implements the full [OpenEnv](https://openenv.dev) specification with:

- **3 Progressive Tasks** — Easy → Medium → Hard (retrieval, debugging, analytics)
- **6-Level Partial Credit Grading** — Meaningful reward signals from 0.0 to 1.0
- **Real-time Agent Arena** — WebSocket leaderboard for competitive multi-agent play
- **Interactive SQL Lab** — Full-featured editor with syntax highlighting
- **Boss/Staff Role System** — Admin dashboards vs operator terminals
- **Progressive Web App** — Installable on desktop and mobile

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                   FastAPI Server                 │
│  ┌───────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Auth/RBAC │  │ Env Core │  │ WebSocket    │  │
│  │ Boss/Staff│  │ step()   │  │ Arena Mgr    │  │
│  └───────────┘  │ reset()  │  └──────────────┘  │
│                 │ state()  │                     │
│  ┌──────────┐  └────┬─────┘  ┌──────────────┐  │
│  │ SQL Lab  │       │        │ Analytics    │  │
│  │ Editor   │  ┌────┴─────┐  │ SVG Charts   │  │
│  └──────────┘  │ SQLite   │  └──────────────┘  │
│                │ 6 tables │                     │
│                │ 400+ rows│                     │
│                └──────────┘                     │
└─────────────────────────────────────────────────┘
```

---

## 📋 Tasks

| # | Task ID | Difficulty | Description | Max Attempts |
|---|---------|------------|-------------|:---:|
| 1 | `sales_summary` | 🟢 Easy | Compute total revenue per region with GROUP BY | 5 |
| 2 | `debug_query` | 🟡 Medium | Fix a broken LEFT JOIN that drops NULL rows | 7 |
| 3 | `performance_analytics` | 🔴 Hard | CTE + RANK() window function for dept ratings | 10 |

---

## 🗄️ Database Schema

| Table | Rows | Purpose |
|-------|:----:|---------|
| `departments` | 8 | Company organizational units |
| `employees` | 50 | Full employee profiles across 8 departments |
| `projects` | 15 | Active, completed, and on-hold projects |
| `project_assignments` | 32 | Employee-project role mappings |
| `sales` | ~200 | 15 months of regional sales transactions |
| `performance_reviews` | 30 | Semi-annual employee performance ratings |

---

## 🎮 Web Interface

### Login
**URL:** `http://localhost:7860/login`

### Boss Dashboard (Full Access)
**URL:** `http://localhost:7860/boss`
**Login:** `boss` / `sqlops2024`
**Features:** Overview, Agent Arena, SQL Lab, Analytics, Settings

### Staff Dashboard (Operator Access)
**URL:** `http://localhost:7860/staff`
**Login:** `staff1` / `staff123` OR `staff2` / `staff456`
**Features:** Task Runner, Query Console, Personal Leaderboard

---

## 📱 Progressive Web App

Install SQLOps as a desktop/mobile app:
- **Chrome/Edge:** Click the install icon in the address bar
- **iOS Safari:** Share → "Add to Home Screen"

---

## 🏃 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn server.app:app --host 0.0.0.0 --port 7860

# Open http://localhost:7860 in your browser
```

### Docker

```bash
docker build -t sqlops-env .
docker run -p 7860:7860 sqlops-env
```

### Run Inference

```bash
# Start server in background
uvicorn server.app:app --port 7860 &

# Run baseline agent
python inference.py
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/reset?task_index=0` | Reset environment to task N |
| `POST` | `/step` | Submit a SQL query, get reward |
| `GET` | `/state` | Current environment state |
| `GET` | `/health` | Health check |
| `GET` | `/tasks` | List all tasks |
| `POST` | `/sql/run` | Execute SQL in lab (no grading) |
| `GET` | `/analytics` | Scores and reward history |
| `WS` | `/ws/arena` | Real-time arena events |

### Step Request

```json
{
  "sql_query": "SELECT region, SUM(amount) AS total FROM sales GROUP BY region",
  "reasoning": "Aggregating sales by region"
}
```

### Step Response

```json
{
  "observation": {
    "task_id": "sales_summary",
    "task_description": "...",
    "partial_score": 0.75,
    "grader_feedback": "Close! Missing ORDER BY.",
    "attempt_number": 2,
    "max_attempts": 5
  },
  "reward": 0.75,
  "done": false,
  "cumulative_reward": 1.75
}
```

---

## 📊 Grading System

| Score | Meaning |
|:-----:|---------|
| 0.00 | Query failed to execute |
| 0.15 | Executes but wrong columns AND wrong data |
| 0.30 | Correct column count, wrong names or data |
| 0.50 | Correct columns, partial row overlap |
| 0.75 | Correct columns, >80% row match |
| 1.00 | Perfect match — columns, data, and order |

---

## 🏆 What Makes This Unique

| Feature | Other Teams | SQLOps |
|---------|-------------|--------|
| UI | Static dashboard | PWA installable app |
| Auth | None | Boss + Staff role system |
| SQL Editor | None | Live Monaco-style editor |
| Real-time | None | WebSocket arena leaderboard |
| Task flow | Flat access | Progressive unlock |
| Analytics | None | SVG charts, CSV export |
| Mobile | No | Full PWA, offline capable |

---

## 📁 Project Structure

```
sqlops_env/
├── models.py              # Pydantic typed models
├── __init__.py             # Package exports
├── openenv.yaml            # OpenEnv spec manifest
├── Dockerfile              # Container build
├── requirements.txt        # Python dependencies
├── inference.py            # Baseline agent script
├── manifest.json           # PWA manifest
├── sw.js                   # Service worker
├── README.md               # This file
└── server/
    ├── app.py              # FastAPI + Auth + WebSocket
    ├── environment.py      # Core env (step/reset/state)
    ├── database.py         # SQLite schema + 400+ row seed
    ├── tasks.py            # 3 task definitions
    ├── graders.py          # 6-level partial credit grader
    ├── auth.py             # Boss/Staff session auth
    └── static/
        ├── login.html      # Animated login page
        ├── boss.html       # 5-tab command center
        ├── staff.html      # Focused task runner
        └── icons/          # PWA icons (generated at build)
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Designed by K. Ajay John Paul</strong><br>
  B.Tech CSE — KL University, Hyderabad<br>
  Built for OpenEnv Hackathon 2024
</p>
