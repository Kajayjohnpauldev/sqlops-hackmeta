# SQLOps OpenEnv
# Designed by K. Ajay John Paul
# B.Tech CSE — KL University, Hyderabad
# OpenEnv Hackathon 2024

"""
Pure-Python session authentication.
Boss (admin) and Staff (operator) with different access levels.
No external auth packages — just dicts and UUIDs.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Request, HTTPException

# ─── User Database ──────────────────────────────────────────────────

USERS: Dict[str, Dict[str, Any]] = {
    "boss": {
        "password": "sqlops2024",
        "role": "boss",
        "display_name": "K. Ajay John Paul",
        "access": [
            "view_all", "reset_all", "manage_staff",
            "view_analytics", "run_queries", "view_leaderboard",
        ],
    },
    "staff1": {
        "password": "staff123",
        "role": "staff",
        "display_name": "Agent Operator 1",
        "access": ["run_queries", "view_own_scores", "view_tasks"],
    },
    "staff2": {
        "password": "staff456",
        "role": "staff",
        "display_name": "Agent Operator 2",
        "access": ["run_queries", "view_own_scores", "view_tasks"],
    },
}

# ─── Active Sessions ────────────────────────────────────────────────

SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSION_MAX_AGE = timedelta(hours=24)

# ─── Session Management ────────────────────────────────────────────

def create_session(username: str) -> str:
    """Generate a UUID session token, store it in SESSIONS."""
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "username": username,
        "role": USERS[username]["role"],
        "display_name": USERS[username]["display_name"],
        "login_time": datetime.utcnow().isoformat(),
        "access": USERS[username]["access"],
    }
    return session_id


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Return session dict or None if invalid/expired."""
    session = SESSIONS.get(session_id)
    if not session:
        return None
    # Check expiry
    login_time = datetime.fromisoformat(session["login_time"])
    if datetime.utcnow() - login_time > SESSION_MAX_AGE:
        del SESSIONS[session_id]
        return None
    return session


def delete_session(session_id: str):
    """Remove a session."""
    SESSIONS.pop(session_id, None)


# ─── FastAPI Dependencies ──────────────────────────────────────────

def require_role(required_role: str):
    """FastAPI dependency factory: require a specific role."""
    async def _dependency(request: Request):
        session_id = request.cookies.get("sqlops_session")
        if not session_id:
            raise HTTPException(status_code=401, detail="Not authenticated")
        session = get_session(session_id)
        if not session:
            raise HTTPException(status_code=401, detail="Session expired")
        if session["role"] != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Requires {required_role} role, you are {session['role']}",
            )
        return session
    return _dependency


async def require_any_auth(request: Request):
    """FastAPI dependency: any logged-in user passes."""
    session_id = request.cookies.get("sqlops_session")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    return session


def get_active_sessions_for_role(role: str) -> list:
    """Get all active sessions for a given role."""
    result = []
    for sid, sess in list(SESSIONS.items()):
        s = get_session(sid)  # validates expiry
        if s and s["role"] == role:
            result.append({"session_id": sid, **s})
    return result
