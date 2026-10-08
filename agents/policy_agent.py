"""
Agent 2: Policy Agent.

Scans recently BLOCKED prompts for high-entropy tokens (the same signal
gitleaks/trufflehog use - real secrets compress poorly and have high
Shannon entropy) that no existing rule already catches. If the same
"unknown token shape" shows up more than once, it's proposed as a new rule
and appended to agents/learned_rules.json.
"""

import sys
import os
import json
import math
import re
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.database import get_all_logs_df
from detectors.secret_scanner import SECRET_RULES

LEARNED_RULES_PATH = os.path.join(os.path.dirname(__file__), "learned_rules.json")

TOKEN_PATTERN = re.compile(r"\b[A-Za-z0-9\-_/+]{16,64}\b")


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    probs = [c / len(s) for c in counts.values()]
    return -sum(p * math.log2(p) for p in probs)


def _is_already_known(token: str) -> bool:
    return any(pattern.search(token) for pattern, _ in SECRET_RULES.values())


def find_candidate_secret_patterns(df, entropy_threshold: float = 3.5, min_occurrences: int = 2):
    """Looks at BLOCKED prompts' original text for high-entropy tokens not
    already caught by an existing rule, and proposes them as new rules if
    the same shape recurs."""
    if df.empty:
        return []

    # NOTE: original_prompt isn't in get_all_logs_df() by default (kept out
    # for the admin dashboard's own privacy), so this agent works off the
    # sanitized_prompt + full DB session for a proper look.
    from backend.database import get_session, AuditLog
    session = get_session()
    try:
        blocked = session.query(AuditLog).filter(AuditLog.action == "BLOCK").all()
        candidates = Counter()
        examples = {}
        for row in blocked:
            for token in TOKEN_PATTERN.findall(row.original_prompt or ""):
                if _is_already_known(token):
                    continue
                if shannon_entropy(token) >= entropy_threshold:
                    shape = re.sub(r"[A-Za-z]", "A", re.sub(r"\d", "9", token))
                    candidates[shape] += 1
                    examples.setdefault(shape, token)

        proposals = []
        for shape, count in candidates.items():
            if count >= min_occurrences:
                proposals.append({"pattern_shape": shape, "example": examples[shape], "occurrences": count})
        return proposals
    finally:
        session.close()


def update_policy():
    df = get_all_logs_df()
    proposals = find_candidate_secret_patterns(df)

    existing = []
    if os.path.exists(LEARNED_RULES_PATH):
        with open(LEARNED_RULES_PATH) as f:
            existing = json.load(f)

    existing_shapes = {r["pattern_shape"] for r in existing}
    new_rules = [p for p in proposals if p["pattern_shape"] not in existing_shapes]
    existing.extend(new_rules)

    with open(LEARNED_RULES_PATH, "w") as f:
        json.dump(existing, f, indent=2)

    return {
        "agent": "Policy Agent",
        "new_rules_proposed": new_rules,
        "total_learned_rules": len(existing),
    }


if __name__ == "__main__":
    print(json.dumps(update_policy(), indent=2))
