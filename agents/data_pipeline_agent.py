"""
Agent 4: Data Pipeline Agent.

Audit rows are already written continuously by backend/database.py on
every /analyze call, so this agent owns the other two jobs:

    clean_dataset()   -> exports the audit log to CSV, drops duplicate or
                          empty rows, ready for retraining
    retrain_models()  -> merges the cleaned export back into the training
                          set and retrains the risk classifier, closing
                          the feedback loop between live traffic and the
                          model

Runs on demand from the dashboard's "Retrain" button today; wire it into
cron / Task Scheduler / an Airflow DAG for a scheduled version.
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.database import get_session, AuditLog
from models.risk_classifier import train_classifiers

CLEANED_EXPORT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "audit_log_export.csv")
PROMPTS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "prompts.csv")


def clean_dataset():
    """Exports the raw audit log to CSV, deduplicates, and drops rows with
    empty prompts -- a minimal but real data-cleaning step before any
    retraining happens."""
    session = get_session()
    try:
        rows = session.query(AuditLog).all()
        df = pd.DataFrame([{
            "prompt": r.original_prompt,
            "risk_level": r.risk_level,
            "threat_types": r.threat_types,
        } for r in rows])
    finally:
        session.close()

    if df.empty:
        return {"agent": "Data Pipeline Agent", "status": "no data to clean yet", "rows": 0}

    before = len(df)
    df = df.dropna(subset=["prompt"])
    df = df[df["prompt"].str.strip() != ""]
    df = df.drop_duplicates(subset=["prompt"])
    after = len(df)

    df.to_csv(CLEANED_EXPORT_PATH, index=False)
    return {"agent": "Data Pipeline Agent", "status": "cleaned", "rows_before": before, "rows_after": after, "export_path": CLEANED_EXPORT_PATH}


def retrain_models():
    """Merges the cleaned audit log export into the synthetic training set
    and retrains the risk/category classifiers -- closing the human-in-
    the-loop feedback cycle: real traffic makes the model smarter over
    time."""
    clean_result = clean_dataset()

    if not os.path.exists(PROMPTS_PATH):
        return {"agent": "Data Pipeline Agent", "status": "error", "message": "Base prompts.csv not found. Run data/generate_prompts.py first."}

    base_df = pd.read_csv(PROMPTS_PATH)

    if os.path.exists(CLEANED_EXPORT_PATH):
        audit_df = pd.read_csv(CLEANED_EXPORT_PATH)
        if not audit_df.empty:
            # Map audit log's binary threat_types into a coarse category
            # label so it fits the same schema as the synthetic training set.
            def infer_category(row):
                types = str(row.get("threat_types", ""))
                if "PROMPT_INJECTION" in types:
                    return "prompt_injection"
                if "API_KEY" in types or "CREDENTIALS" in types:
                    return "secret_leak"
                if "PII" in types:
                    return "pii_leak"
                if "SOURCE_CODE" in types:
                    return "source_code"
                return "benign"

            audit_df["category"] = audit_df.apply(infer_category, axis=1)
            audit_df = audit_df[["prompt", "category", "risk_level"]]
            merged = pd.concat([base_df, audit_df], ignore_index=True).drop_duplicates(subset=["prompt"])
        else:
            merged = base_df
    else:
        merged = base_df

    merged.to_csv(PROMPTS_PATH, index=False)
    train_classifiers(PROMPTS_PATH)

    return {
        "agent": "Data Pipeline Agent",
        "status": "retrained",
        "clean_result": clean_result,
        "total_training_rows": len(merged),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(retrain_models(), indent=2, default=str))
