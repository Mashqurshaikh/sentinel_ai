"""
FastAPI gateway service.

Sits between the employee-facing client and an external LLM: receives a
prompt (or an uploaded file), runs it through the risk engine, logs the
result, and - for anything not blocked - actually forwards the sanitized
text to the chosen provider (Claude / ChatGPT / Gemini) and returns the
real response. Blocked requests go through the approval queue instead;
approving one also triggers the forward.

Run with:
    uvicorn backend.main:app --reload --port 8000

Then open http://localhost:8000/docs for interactive API documentation.
"""

import os
import sys
import io
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
# Loads key=value pairs from a .env file in the project root into the
# environment, so ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY are
# available to backend/llm_providers.py without exporting them manually
# in every new terminal session.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List

from detectors.risk_engine import analyze_prompt
from detectors.file_extractor import extract_text, UnsupportedFileType
from backend.llm_providers import forward_to_llm, provider_status, LLMError
from backend.auth import hash_password, verify_password, create_token, decode_token, TokenError
from backend.database import (
    init_db, save_audit_entry, get_recent_logs, get_all_logs_df,
    list_custom_rules, add_custom_rule, delete_custom_rule, toggle_custom_rule,
    get_timeseries, get_department_breakdown,
    create_pending_approval, list_approvals, decide_approval, count_recent_flagged,
    get_approval_by_id,
    get_user_by_username, create_user, list_users,
    attach_llm_response, attach_approval_llm_response,
)

app = FastAPI(
    title="Sentinel AI Gateway",
    description="Autonomous, privacy-preserving gateway for Shadow AI threat detection.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


# ---------------------------------------------------------------- auth
def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Reads the Bearer token, verifies it, and returns the decoded claims.
    Raises 401 if missing/invalid so protected routes can just depend on
    this instead of checking manually."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header.")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return decode_token(token)
    except TokenError as e:
        raise HTTPException(status_code=401, detail=str(e))


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str = ""
    department: str = "Unassigned"
    role: str = "employee"  # only used if no admin exists yet / by an admin creating accounts


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/auth/register")
def register(req: RegisterRequest):
    if get_user_by_username(req.username):
        raise HTTPException(status_code=400, detail="That username is already taken.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    # Self-registration always creates an employee account, regardless of
    # what the client sends for "role" - promoting to admin has to happen
    # through an existing admin, not by asking nicely in a signup form.
    user_id = create_user(req.username, hash_password(req.password), "employee", req.department, req.full_name)
    return {"id": user_id, "username": req.username, "role": "employee"}


@app.post("/auth/login")
def login(req: LoginRequest):
    user = get_user_by_username(req.username)
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password.")
    token = create_token(user.id, user.username, user.role, user.department)
    return {
        "token": token,
        "user": {
            "id": user.id, "username": user.username, "role": user.role,
            "department": user.department, "full_name": user.full_name,
        },
    }


@app.get("/auth/me")
def me(user: dict = Depends(get_current_user)):
    return user


@app.get("/auth/users")
def get_users(admin: dict = Depends(require_admin)):
    users = list_users()
    return [{
        "id": u.id, "username": u.username, "role": u.role,
        "department": u.department, "full_name": u.full_name,
        "created_at": u.created_at.isoformat(),
    } for u in users]


@app.get("/providers")
def get_providers():
    """Which LLM providers have an API key configured - the frontend uses
    this to disable options that won't work rather than let someone pick
    Gemini and get a confusing error three steps later."""
    return provider_status()


# ---------------------------------------------------------------- live feed
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, payload: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ---------------------------------------------------------------- schemas
class PromptRequest(BaseModel):
    prompt: str
    user_id: Optional[str] = "anonymous"
    department: Optional[str] = "Unassigned"
    provider: Optional[str] = None  # "claude" | "chatgpt" | "gemini" - if set, ALLOW/REVIEW results get forwarded live


class RuleRequest(BaseModel):
    name: str
    pattern: str
    severity: Optional[str] = "high"


# ---------------------------------------------------------------- routes
@app.get("/")
def root():
    return {
        "service": "Sentinel AI Gateway",
        "status": "running",
        "endpoints": [
            "/auth/register", "/auth/login", "/auth/me", "/auth/users",
            "/providers",
            "/analyze", "/analyze-file", "/audit-logs", "/stats",
            "/analytics/timeseries", "/analytics/departments",
            "/rules", "/export/csv", "/ws/live-feed",
            "/approvals", "/approvals/{id}/approve", "/approvals/{id}/reject",
            "/agents/traffic-monitor", "/agents/policy",
            "/agents/threat-intel", "/agents/data-pipeline", "/docs",
        ],
    }


@app.post("/analyze")
async def analyze(req: PromptRequest):
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    rules = list_custom_rules(active_only=True)
    recent_flags = count_recent_flagged(req.user_id) if req.user_id else 0
    result = analyze_prompt(
        req.prompt, user_id=req.user_id, department=req.department,
        custom_rule_rows=rules, recent_flag_count=recent_flags,
    )
    log_id = save_audit_entry(result["audit_entry"])
    result["audit_log_id"] = log_id

    if result["action"] == "BLOCK":
        approval_id = create_pending_approval(result["audit_entry"], audit_log_id=log_id)
        result["approval_id"] = approval_id
    elif req.provider:
        # LOW and MEDIUM risk results already have the sensitive parts
        # masked, so it's safe to forward them straight through instead of
        # making the person copy/paste into a separate chat window.
        try:
            response_text = await forward_to_llm(result["sanitized_prompt"], req.provider)
            result["llm_response"] = response_text
            result["llm_provider"] = req.provider
            attach_llm_response(log_id, req.provider, response_text)
        except LLMError as e:
            result["llm_error"] = str(e)

    await manager.broadcast({"type": "new_analysis", "data": result["audit_entry"], "id": log_id})
    return result


@app.post("/analyze-file")
async def analyze_file(
    file: UploadFile = File(...),
    user_id: str = Form("anonymous"),
    department: str = Form("Unassigned"),
    provider: Optional[str] = Form(None),
):
    contents = await file.read()
    try:
        text = extract_text(file.filename, contents)
    except UnsupportedFileType as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in the uploaded file.")

    rules = list_custom_rules(active_only=True)
    recent_flags = count_recent_flagged(user_id) if user_id else 0
    result = analyze_prompt(
        text, user_id=user_id, department=department, source="file",
        custom_rule_rows=rules, recent_flag_count=recent_flags,
    )
    result["audit_entry"]["original_prompt"] = f"[file: {file.filename}]\n{text[:2000]}"
    log_id = save_audit_entry(result["audit_entry"])
    result["audit_log_id"] = log_id
    result["filename"] = file.filename

    if result["action"] == "BLOCK":
        approval_id = create_pending_approval(result["audit_entry"], audit_log_id=log_id)
        result["approval_id"] = approval_id
    elif provider:
        try:
            response_text = await forward_to_llm(result["sanitized_prompt"], provider)
            result["llm_response"] = response_text
            result["llm_provider"] = provider
            attach_llm_response(log_id, provider, response_text)
        except LLMError as e:
            result["llm_error"] = str(e)

    await manager.broadcast({"type": "new_analysis", "data": result["audit_entry"], "id": log_id})
    return result


@app.get("/audit-logs")
def audit_logs(limit: int = 50):
    logs = get_recent_logs(limit=limit)
    return [{
        "id": l.id, "timestamp": l.timestamp.isoformat(), "user_id": l.user_id,
        "department": l.department, "risk_level": l.risk_level,
        "threat_types": l.threat_types.split(",") if l.threat_types else [],
        "compliance_tags": l.compliance_tags.split(",") if l.compliance_tags else [],
        "action": l.action, "sanitized_prompt": l.sanitized_prompt, "source": l.source,
    } for l in logs]


@app.get("/stats")
def stats():
    df = get_all_logs_df()
    if df.empty:
        return {"total_requests": 0, "risk_distribution": {}, "block_rate": 0.0, "top_users": {}}

    return {
        "total_requests": len(df),
        "risk_distribution": df["risk_level"].value_counts().to_dict(),
        "block_rate": round(100 * (df["action"] == "BLOCK").mean(), 2),
        "top_users": df["user_id"].value_counts().head(5).to_dict(),
        "file_scans": int((df["source"] == "file").sum()),
    }


@app.get("/analytics/timeseries")
def analytics_timeseries(hours: int = 24):
    return get_timeseries(hours=hours)


@app.get("/analytics/departments")
def analytics_departments():
    return get_department_breakdown()


@app.get("/approvals")
def get_approvals(status: str = "pending", limit: int = 100):
    rows = list_approvals(status=status if status != "all" else None, limit=limit)
    return [{
        "id": a.id, "timestamp": a.timestamp.isoformat(), "user_id": a.user_id,
        "department": a.department, "original_prompt": a.original_prompt,
        "sanitized_prompt": a.sanitized_prompt, "risk_level": a.risk_level,
        "threat_types": a.threat_types.split(",") if a.threat_types else [],
        "reasons": a.reasons.split(" | ") if a.reasons else [],
        "status": a.status, "decided_by": a.decided_by,
        "decided_at": a.decided_at.isoformat() if a.decided_at else None,
        "llm_provider": a.llm_provider, "llm_response": a.llm_response,
    } for a in rows]


class ApprovalDecision(BaseModel):
    decided_by: str = "admin"
    provider: Optional[str] = None  # if set, forward the sanitized text on approval


@app.post("/approvals/{approval_id}/approve")
async def approve_request(approval_id: int, req: ApprovalDecision):
    ok = decide_approval(approval_id, "approved", req.decided_by)
    if not ok:
        raise HTTPException(status_code=404, detail="Approval request not found.")

    response = {"status": "approved"}
    if req.provider:
        approval = get_approval_by_id(approval_id)
        try:
            response_text = await forward_to_llm(approval.sanitized_prompt, req.provider)
            response["llm_response"] = response_text
            response["llm_provider"] = req.provider
            attach_approval_llm_response(approval_id, req.provider, response_text)
            if approval.audit_log_id:
                attach_llm_response(approval.audit_log_id, req.provider, response_text)
        except LLMError as e:
            response["llm_error"] = str(e)
    return response


@app.post("/approvals/{approval_id}/reject")
def reject_request(approval_id: int, req: ApprovalDecision):
    ok = decide_approval(approval_id, "rejected", req.decided_by)
    if not ok:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    return {"status": "rejected"}


@app.get("/rules")
def get_rules():
    rules = list_custom_rules()
    return [{
        "id": r.id, "name": r.name, "pattern": r.pattern,
        "severity": r.severity, "active": r.active,
        "created_at": r.created_at.isoformat(),
    } for r in rules]


@app.post("/rules")
def create_rule(req: RuleRequest):
    import re
    try:
        re.compile(req.pattern)
    except re.error as e:
        raise HTTPException(status_code=400, detail=f"Invalid regex pattern: {e}")
    rule_id = add_custom_rule(req.name, req.pattern, req.severity)
    return {"id": rule_id, "status": "created"}


@app.delete("/rules/{rule_id}")
def remove_rule(rule_id: int):
    ok = delete_custom_rule(rule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Rule not found.")
    return {"status": "deleted"}


@app.patch("/rules/{rule_id}/toggle")
def toggle_rule(rule_id: int, active: bool):
    ok = toggle_custom_rule(rule_id, active)
    if not ok:
        raise HTTPException(status_code=404, detail="Rule not found.")
    return {"status": "updated"}


@app.get("/export/csv")
def export_csv():
    df = get_all_logs_df()
    buffer = io.StringIO()
    if df.empty:
        buffer.write("no data yet\n")
    else:
        df.to_csv(buffer, index=False)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sentinel_audit_export.csv"},
    )


@app.post("/agents/traffic-monitor")
def run_traffic_monitor_agent():
    from agents.traffic_monitor_agent import run_traffic_monitor
    return run_traffic_monitor()


@app.post("/agents/policy")
def run_policy_agent():
    from agents.policy_agent import update_policy
    return update_policy()


@app.post("/agents/threat-intel")
def run_threat_intel_agent():
    from agents.threat_intel_agent import generate_threat_report
    report, alerts = generate_threat_report()
    return report


@app.post("/agents/data-pipeline")
def run_data_pipeline_agent():
    from agents.data_pipeline_agent import retrain_models
    return retrain_models()


@app.websocket("/ws/live-feed")
async def live_feed(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # client doesn't need to send anything; keeps the socket alive
    except WebSocketDisconnect:
        manager.disconnect(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
