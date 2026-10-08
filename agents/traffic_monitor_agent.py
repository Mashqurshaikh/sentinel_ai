"""
Agent 1: Traffic Monitoring Agent.

Watches request volume and per-user risk patterns. Reads directly from the
SQLite audit log for now; swap `_load_logs` for a Kafka consumer if this
ever needs to run against a live stream instead of a batch table.
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.database import get_all_logs_df


def _load_logs():
    return get_all_logs_df()


def detect_traffic_spikes(df: pd.DataFrame, window_minutes: int = 10, spike_multiplier: float = 2.5):
    """Flags time windows where request volume exceeds `spike_multiplier`
    times the rolling average -- a simple, explainable anomaly rule
    (no need for a full time-series model for this scope)."""
    if df.empty:
        return []
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()
    counts = df.resample(f"{window_minutes}min").size()
    if len(counts) < 2:
        return []
    avg = counts.mean()
    spikes = counts[counts > max(avg * spike_multiplier, 3)]
    return [{"window_start": str(idx), "request_count": int(val)} for idx, val in spikes.items()]


def detect_suspicious_users(df: pd.DataFrame, min_high_risk_requests: int = 3):
    """Flags users whose requests are disproportionately high/blocked risk."""
    if df.empty:
        return []
    risky = df[df["risk_level"].isin(["high", "critical"])]
    counts = risky.groupby("user_id").size()
    suspicious = counts[counts >= min_high_risk_requests]
    return [{"user_id": u, "high_risk_request_count": int(c)} for u, c in suspicious.items()]


def run_traffic_monitor():
    df = _load_logs()
    spikes = detect_traffic_spikes(df)
    suspicious_users = detect_suspicious_users(df)
    report = {
        "agent": "Traffic Monitoring Agent",
        "total_requests_analyzed": len(df),
        "traffic_spikes": spikes,
        "suspicious_users": suspicious_users,
    }
    return report


if __name__ == "__main__":
    import json
    print(json.dumps(run_traffic_monitor(), indent=2, default=str))
