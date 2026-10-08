"""
Agent 3: Threat Intelligence Agent.

Aggregates the audit log into a security report - risk breakdown, top
threat types, users with repeated blocked requests - and writes it to
agents/reports/. `_notify` returns the alert list for now; point it at a
real SMTP/Slack webhook to send actual notifications.
"""

import sys
import os
import json
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.database import get_all_logs_df

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


def _notify(alerts):
    """Stand-in for a real notification channel (email/Slack/Teams webhook).
    For the demo, this just returns the alert list so the dashboard can
    display it -- wire up smtplib or a Slack webhook POST here for a real
    deployment."""
    return alerts


def generate_threat_report():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    df = get_all_logs_df()

    if df.empty:
        report = {
            "agent": "Threat Intelligence Agent",
            "generated_at": datetime.datetime.utcnow().isoformat(),
            "summary": "No audit log data yet. Analyze some prompts first.",
        }
        return report, []

    risk_counts = df["risk_level"].value_counts().to_dict()
    action_counts = df["action"].value_counts().to_dict()

    threat_type_counter = {}
    for types_str in df["threat_types"].dropna():
        for t in types_str.split(","):
            t = t.strip()
            if t and t != "NONE":
                threat_type_counter[t] = threat_type_counter.get(t, 0) + 1

    top_users_by_block = df[df["action"] == "BLOCK"]["user_id"].value_counts().head(5).to_dict()

    alerts = []
    for user, count in top_users_by_block.items():
        if count >= 3:
            alerts.append(f"ALERT: user '{user}' has {count} blocked high-risk prompts -- recommend manual review.")

    report = {
        "agent": "Threat Intelligence Agent",
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "total_requests": len(df),
        "risk_level_breakdown": risk_counts,
        "action_breakdown": action_counts,
        "threat_type_frequency": threat_type_counter,
        "top_users_by_blocked_requests": top_users_by_block,
        "alerts": _notify(alerts),
    }

    report_path = os.path.join(REPORTS_DIR, f"threat_report_{datetime.date.today().isoformat()}.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    return report, alerts


if __name__ == "__main__":
    report, alerts = generate_threat_report()
    print(json.dumps(report, indent=2, default=str))
