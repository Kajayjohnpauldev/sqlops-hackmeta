# SQLOps OpenEnv
# Designed by K. Ajay John Paul
# B.Tech CSE — KL University, Hyderabad
# OpenEnv Hackathon 2024

"""
FastAPI application — the nerve center.
Routes: OpenEnv API + Auth + WebSocket Arena + Static pages.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from fastapi import (
    FastAPI, HTTPException, Depends, Request, Response,
    WebSocket, WebSocketDisconnect, Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure parent directory is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import SQLOpsAction, StepResult, SQLOpsState
from server.environment import SQLOpsEnvironment
from server.auth import (
    USERS, SESSIONS, create_session, get_session, delete_session,
    require_role, require_any_auth, get_active_sessions_for_role,
)
from server.tasks import TASKS


# ─── App Setup ──────────────────────────────────────────────────────

app = FastAPI(
    title="SQLOps Oracle",
    description="AI SQL Training Environment — Designed by K. Ajay John Paul",
    version="1.0.0",
)
app.state.start_time = time.time()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Environment instance
env = SQLOpsEnvironment()


# ═══════════════════════════════════════════════════════════════════
# WEBSOCKET ARENA — real-time leaderboard
# ═══════════════════════════════════════════════════════════════════

class ArenaManager:
    """Manages WebSocket connections for the live agent arena."""

    def __init__(self):
        self.connections: List[WebSocket] = []
        self.events: list = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)
        # Send last 20 events to catch up
        for evt in self.events[-20:]:
            try:
                await ws.send_text(json.dumps(evt))
            except Exception:
                pass

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, data: dict):
        self.events.append(data)
        if len(self.events) > 500:
            self.events = self.events[-500:]
        dead = []
        for ws in self.connections:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

arena = ArenaManager()


@app.websocket("/ws/arena")
async def websocket_arena(websocket: WebSocket):
    await arena.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        arena.disconnect(websocket)


# ═══════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    fp = STATIC_DIR / "login.html"
    if fp.exists():
        return HTMLResponse(fp.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Login page not found</h1>", status_code=404)


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/auth/login")
async def do_login(request: Request):
    # Support both JSON and form data
    content_type = request.headers.get("content-type", "")
    if "json" in content_type:
        data = await request.json()
        username = data.get("username", "")
        password = data.get("password", "")
    else:
        form = await request.form()
        username = str(form.get("username", ""))
        password = str(form.get("password", ""))

    user = USERS.get(username)
    if not user or user["password"] != password:
        return JSONResponse({"error": "Invalid credentials"}, status_code=401)

    session_id = create_session(username)
    redirect_url = "/boss" if user["role"] == "boss" else "/staff"

    resp = JSONResponse({
        "redirect": redirect_url,
        "role": user["role"],
        "display_name": user["display_name"],
    })
    resp.set_cookie(
        "sqlops_session", session_id,
        httponly=True, max_age=86400, samesite="lax",
    )
    return resp


@app.post("/auth/logout")
async def do_logout(request: Request):
    session_id = request.cookies.get("sqlops_session")
    if session_id:
        delete_session(session_id)
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("sqlops_session")
    return resp


@app.get("/auth/me")
async def auth_me(session=Depends(require_any_auth)):
    return JSONResponse(session)


# ═══════════════════════════════════════════════════════════════════
# ROLE DASHBOARDS
# ═══════════════════════════════════════════════════════════════════

@app.get("/boss", response_class=HTMLResponse)
async def boss_dashboard(session=Depends(require_role("boss"))):
    fp = STATIC_DIR / "boss.html"
    if fp.exists():
        return HTMLResponse(fp.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Boss dashboard not found</h1>", status_code=404)


@app.get("/staff", response_class=HTMLResponse)
async def staff_dashboard(session=Depends(require_any_auth)):
    fp = STATIC_DIR / "staff.html"
    if fp.exists():
        return HTMLResponse(fp.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Staff dashboard not found</h1>", status_code=404)


@app.get("/report", response_class=HTMLResponse)
async def report_page():
    fp = STATIC_DIR / "report.html"
    if fp.exists():
        return HTMLResponse(fp.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Report not found</h1>", status_code=404)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    session_id = request.cookies.get("sqlops_session")
    if session_id:
        sess = get_session(session_id)
        if sess:
            return RedirectResponse(
                "/boss" if sess["role"] == "boss" else "/staff"
            )
    return RedirectResponse("/login")


# ═══════════════════════════════════════════════════════════════════
# OPENENV CORE API — step / reset / state
# ═══════════════════════════════════════════════════════════════════

@app.post("/reset")
async def reset_env(task_index: int = Query(0, ge=0, le=2)):
    result = env.reset(task_index=task_index)
    await arena.broadcast({
        "event": "reset",
        "task": result.observation.task_id,
        "timestamp": datetime.utcnow().isoformat(),
    })
    return result.model_dump()


@app.post("/step")
async def step_env(action: SQLOpsAction):
    result = env.step(action)
    # Broadcast to arena
    await arena.broadcast({
        "event": "step",
        "task": result.observation.task_id,
        "reward": result.reward,
        "done": result.done,
        "score": result.observation.partial_score,
        "step": env._steps_taken,
        "attempt": result.observation.attempt_number,
        "feedback": result.observation.grader_feedback[:100],
        "timestamp": datetime.utcnow().isoformat(),
    })
    return result.model_dump()


@app.get("/state")
async def get_state():
    return env.state().model_dump()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "env": "sqlops",
        "version": "1.0.0",
        "author": "K. Ajay John Paul",
        "uptime": round(time.time() - app.state.start_time, 1),
    }


# ═══════════════════════════════════════════════════════════════════
# EXTENDED API — tasks, analytics, SQL lab, admin
# ═══════════════════════════════════════════════════════════════════

@app.get("/tasks")
async def get_tasks():
    return [
        {
            "task_id": t["task_id"],
            "title": t["title"],
            "difficulty": t["difficulty"],
            "description": t["description"],
            "expected_columns": t["expected_columns"],
            "max_attempts": t["max_attempts"],
            "hint": t.get("hint", ""),
            "schema_tables": t.get("schema_tables", []),
        }
        for t in TASKS
    ]


class SQLLabRequest(BaseModel):
    sql: str


@app.post("/sql/run")
async def sql_lab_run(req: SQLLabRequest):
    """Run arbitrary SQL in the SQL Lab (no grading)."""
    return env.run_query(req.sql)


@app.get("/sql/reference/{task_index}")
async def sql_reference(task_index: int, session=Depends(require_role("boss"))):
    """Get reference SQL for a task (boss only)."""
    try:
        return {"sql": env.get_reference_sql(task_index)}
    except IndexError:
        raise HTTPException(404, "Task not found")


@app.get("/analytics")
async def analytics():
    s = env.state()
    return {
        "task_scores": s.task_scores,
        "task_attempts": s.task_attempts,
        "total_steps": s.steps_taken,
        "cumulative_reward": s.cumulative_reward,
        "reward_history": s.reward_history,
        "done": s.done,
    }


@app.get("/admin/info")
async def admin_info(session=Depends(require_role("boss"))):
    return {
        "db_tables": 6,
        "python_version": sys.version.split()[0],
        "uptime_seconds": round(time.time() - app.state.start_time, 1),
        "active_ws_connections": len(arena.connections),
        "active_sessions": len(SESSIONS),
        "total_steps": env._steps_taken,
        "author": "K. Ajay John Paul",
        "institution": "KL University, Hyderabad",
    }


@app.get("/admin/sessions")
async def admin_sessions(session=Depends(require_role("boss"))):
    return [
        {"session_id": sid[:8] + "...", **{k: v for k, v in s.items()}}
        for sid, s in SESSIONS.items()
        if get_session(sid)
    ]


@app.post("/admin/reset-all")
async def admin_reset_all(session=Depends(require_role("boss"))):
    result = env.reset(task_index=0)
    await arena.broadcast({
        "event": "admin_reset",
        "timestamp": datetime.utcnow().isoformat(),
    })
    return {"status": "reset", "message": "All tasks reset by boss"}


# ═══════════════════════════════════════════════════════════════════
# PWA FILES
# ═══════════════════════════════════════════════════════════════════

ROOT_DIR = Path(__file__).resolve().parent.parent

@app.get("/manifest.json")
async def manifest():
    fp = ROOT_DIR / "manifest.json"
    if fp.exists():
        return JSONResponse(json.loads(fp.read_text(encoding="utf-8")))
    return JSONResponse({
        "name": "SQLOps Oracle",
        "short_name": "SQLOps",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#030508",
        "theme_color": "#00D4FF",
    })


@app.get("/sw.js")
async def service_worker():
    fp = ROOT_DIR / "sw.js"
    if fp.exists():
        return FileResponse(str(fp), media_type="application/javascript")
    return Response("// no service worker", media_type="application/javascript")
