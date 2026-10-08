"""
Database layer.

SQLite by default - zero setup, single file. To move to Postgres, change
DATABASE_URL below to something like
    postgresql://user:password@localhost:5432/sentinel
and install psycopg2-binary; SQLAlchemy handles the rest.
"""

import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "audit_log.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    user_id = Column(String(100), index=True)
    department = Column(String(100), index=True, default="Unassigned")
    original_prompt = Column(Text)
    sanitized_prompt = Column(Text)
    risk_level = Column(String(20), index=True)
    threat_types = Column(String(255))
    compliance_tags = Column(String(255), default="")
    action = Column(String(20))
    reasons = Column(Text)
    source = Column(String(20), default="prompt")  # "prompt" | "file"
    llm_provider = Column(String(30), nullable=True)
    llm_response = Column(Text, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255))
    role = Column(String(20), default="employee")  # "employee" | "admin"
    department = Column(String(100), default="Unassigned")
    full_name = Column(String(150), default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class CustomRule(Base):
    __tablename__ = "custom_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    pattern = Column(Text)
    severity = Column(String(20), default="high")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PendingApproval(Base):
    __tablename__ = "pending_approvals"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    user_id = Column(String(100), index=True)
    department = Column(String(100), default="Unassigned")
    original_prompt = Column(Text)
    sanitized_prompt = Column(Text)
    risk_level = Column(String(20))
    threat_types = Column(String(255))
    reasons = Column(Text)
    status = Column(String(20), default="pending", index=True)  # pending | approved | rejected
    decided_by = Column(String(100), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    audit_log_id = Column(Integer, nullable=True)
    llm_provider = Column(String(30), nullable=True)
    llm_response = Column(Text, nullable=True)


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _seed_default_admin()


def _seed_default_admin():
    """Creates a default admin account on first run so there's always a way
    in. Change this password immediately in any real deployment - it's only
    here so the demo isn't locked out of its own admin pages."""
    from backend.auth import hash_password

    session = get_session()
    try:
        if session.query(User).count() == 0:
            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                role="admin",
                department="IT Security",
                full_name="Default Admin",
            )
            session.add(admin)
            session.commit()
    finally:
        session.close()


def get_session():
    return SessionLocal()


def save_audit_entry(entry: dict):
    session = get_session()
    try:
        log = AuditLog(
            timestamp=datetime.datetime.fromisoformat(entry["timestamp"]),
            user_id=entry["user_id"],
            department=entry.get("department") or "Unassigned",
            original_prompt=entry["original_prompt"],
            sanitized_prompt=entry["sanitized_prompt"],
            risk_level=entry["risk_level"],
            threat_types=",".join(entry["threat_types"]),
            compliance_tags=",".join(entry.get("compliance_tags", [])),
            action=entry["action"],
            reasons=" | ".join(entry["reasons"]),
            source=entry.get("source", "prompt"),
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log.id
    finally:
        session.close()


def list_custom_rules(active_only: bool = False):
    session = get_session()
    try:
        q = session.query(CustomRule)
        if active_only:
            q = q.filter(CustomRule.active == True)  # noqa: E712
        return q.order_by(CustomRule.created_at.desc()).all()
    finally:
        session.close()


def add_custom_rule(name: str, pattern: str, severity: str = "high"):
    session = get_session()
    try:
        rule = CustomRule(name=name, pattern=pattern, severity=severity, active=True)
        session.add(rule)
        session.commit()
        session.refresh(rule)
        return rule.id
    finally:
        session.close()


def delete_custom_rule(rule_id: int):
    session = get_session()
    try:
        rule = session.query(CustomRule).filter(CustomRule.id == rule_id).first()
        if rule:
            session.delete(rule)
            session.commit()
            return True
        return False
    finally:
        session.close()


def toggle_custom_rule(rule_id: int, active: bool):
    session = get_session()
    try:
        rule = session.query(CustomRule).filter(CustomRule.id == rule_id).first()
        if rule:
            rule.active = active
            session.commit()
            return True
        return False
    finally:
        session.close()


def get_recent_logs(limit: int = 100):
    session = get_session()
    try:
        return session.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    finally:
        session.close()


def get_all_logs_df():
    import pandas as pd
    session = get_session()
    try:
        logs = session.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
        return pd.DataFrame([{
            "id": l.id, "timestamp": l.timestamp, "user_id": l.user_id,
            "department": l.department, "risk_level": l.risk_level,
            "threat_types": l.threat_types, "compliance_tags": l.compliance_tags,
            "action": l.action, "sanitized_prompt": l.sanitized_prompt,
            "source": l.source,
        } for l in logs])
    finally:
        session.close()


def get_timeseries(hours: int = 24):
    """Request counts bucketed by hour, split by risk level - powers the
    admin dashboard's activity chart."""
    import pandas as pd
    df = get_all_logs_df()
    if df.empty:
        return []
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    df = df[df["timestamp"] >= cutoff]
    if df.empty:
        return []
    df["bucket"] = df["timestamp"].dt.floor("h")
    grouped = df.groupby(["bucket", "risk_level"]).size().unstack(fill_value=0)
    result = []
    for bucket, row in grouped.iterrows():
        entry = {"time": bucket.isoformat()}
        entry.update({level: int(row.get(level, 0)) for level in ["low", "medium", "high"]})
        result.append(entry)
    return result


def get_department_breakdown():
    df = get_all_logs_df()
    if df.empty:
        return []
    grouped = df.groupby("department").agg(
        total=("id", "count"),
        blocked=("action", lambda x: (x == "BLOCK").sum()),
    ).reset_index()
    return grouped.to_dict(orient="records")


# ---------------------------------------------------------------- approvals
def create_pending_approval(entry: dict, audit_log_id: int = None):
    session = get_session()
    try:
        approval = PendingApproval(
            timestamp=datetime.datetime.fromisoformat(entry["timestamp"]),
            user_id=entry["user_id"],
            department=entry.get("department") or "Unassigned",
            original_prompt=entry["original_prompt"],
            sanitized_prompt=entry["sanitized_prompt"],
            risk_level=entry["risk_level"],
            threat_types=",".join(entry["threat_types"]),
            reasons=" | ".join(entry["reasons"]),
            status="pending",
            audit_log_id=audit_log_id,
        )
        session.add(approval)
        session.commit()
        session.refresh(approval)
        return approval.id
    finally:
        session.close()


def list_approvals(status: str = None, limit: int = 100):
    session = get_session()
    try:
        q = session.query(PendingApproval)
        if status:
            q = q.filter(PendingApproval.status == status)
        return q.order_by(PendingApproval.timestamp.desc()).limit(limit).all()
    finally:
        session.close()


def get_approval_by_id(approval_id: int):
    session = get_session()
    try:
        return session.query(PendingApproval).filter(PendingApproval.id == approval_id).first()
    finally:
        session.close()


def decide_approval(approval_id: int, decision: str, decided_by: str):
    """decision: 'approved' or 'rejected'"""
    session = get_session()
    try:
        approval = session.query(PendingApproval).filter(PendingApproval.id == approval_id).first()
        if not approval:
            return False
        approval.status = decision
        approval.decided_by = decided_by
        approval.decided_at = datetime.datetime.utcnow()
        session.commit()
        return True
    finally:
        session.close()


# ---------------------------------------------------------------- chunked-leak detection
def count_recent_flagged(user_id: str, minutes: int = 30, min_level: str = "medium"):
    """Counts how many medium-or-higher-risk requests this user has sent in
    the last `minutes` - used to catch someone splitting a leak across
    several messages that each look mild on their own (e.g. one message
    with a name, a follow-up with an account number, a follow-up with a
    phone number)."""
    session = get_session()
    try:
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)
        levels = ["medium", "high", "critical"] if min_level == "medium" else ["high", "critical"]
        return session.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= cutoff,
            AuditLog.risk_level.in_(levels),
        ).count()
    finally:
        session.close()


# ---------------------------------------------------------------- users
def get_user_by_username(username: str):
    session = get_session()
    try:
        return session.query(User).filter(User.username == username).first()
    finally:
        session.close()


def create_user(username: str, password_hash: str, role: str, department: str, full_name: str = ""):
    session = get_session()
    try:
        user = User(username=username, password_hash=password_hash, role=role,
                    department=department, full_name=full_name)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id
    finally:
        session.close()


def list_users():
    session = get_session()
    try:
        return session.query(User).order_by(User.created_at.desc()).all()
    finally:
        session.close()


# ---------------------------------------------------------------- LLM forwarding
def attach_llm_response(audit_log_id: int, provider: str, response: str):
    session = get_session()
    try:
        row = session.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
        if row:
            row.llm_provider = provider
            row.llm_response = response
            session.commit()
    finally:
        session.close()


def attach_approval_llm_response(approval_id: int, provider: str, response: str):
    session = get_session()
    try:
        row = session.query(PendingApproval).filter(PendingApproval.id == approval_id).first()
        if row:
            row.llm_provider = provider
            row.llm_response = response
            session.commit()
    finally:
        session.close()
