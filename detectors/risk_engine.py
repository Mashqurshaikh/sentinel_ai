"""
Risk engine - central orchestration point for the gateway.

Wires together the secret scanner, PII detector, code/injection heuristics,
the ML risk classifier, and the sanitizer into a single analyze_prompt()
call. Returns risk score, threat types, compliance tags, the sanitized
text, a recommendation, and an audit-log-ready dict.
"""

import datetime
import re
from dataclasses import asdict

from detectors.secret_scanner import scan_secrets
from detectors.pii_detector import detect_pii
from detectors.code_and_injection_detector import detect_source_code, detect_prompt_injection
from detectors.compliance import get_compliance_tags
from privacy.sanitizer import sanitize_prompt

try:
    from models.risk_classifier import RiskClassifier
    _ml_classifier = RiskClassifier()
except Exception:
    _ml_classifier = None  # falls back to rule-based-only detection


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _combine_risk(rule_risk: str, ml_risk: str, ml_confidence: float, confidence_floor: float = 0.55) -> str:
    """Escalates to whichever signal is more severe - but only lets the ML
    model raise the risk level when it's actually confident. A low-confidence
    guess (barely above chance for a 3-way split) shouldn't be allowed to
    override a clean rule-based verdict - that was causing ordinary questions
    to get flagged high risk purely on classifier noise."""
    if RISK_ORDER.get(ml_risk, 0) > RISK_ORDER[rule_risk] and ml_confidence < confidence_floor:
        return rule_risk
    return rule_risk if RISK_ORDER[rule_risk] >= RISK_ORDER.get(ml_risk, 0) else ml_risk


def _compile_custom_rules(custom_rule_rows):
    """Turns CustomRule DB rows into the {name: (compiled_pattern, severity)}
    shape scan_secrets() expects."""
    compiled = {}
    for row in custom_rule_rows or []:
        if not row.active:
            continue
        try:
            compiled[row.name] = (re.compile(row.pattern), row.severity)
        except re.error:
            continue  # skip a malformed pattern rather than crash the whole scan
    return compiled


def analyze_prompt(text: str, user_id: str = "anonymous", department: str = "Unassigned",
                    source: str = "prompt", custom_rule_rows=None, recent_flag_count: int = 0) -> dict:
    custom_rules = _compile_custom_rules(custom_rule_rows)
    secrets = scan_secrets(text, custom_rules=custom_rules)
    secret_spans = [(s.start, s.end) for s in secrets]

    pii_matches = detect_pii(text, pre_covered_spans=secret_spans)
    code_result = detect_source_code(text)
    injection_result = detect_prompt_injection(text)
    compliance_tags = get_compliance_tags(pii_matches, secrets)

    threat_types = []
    if secrets:
        threat_types.append("API_KEY" if any(s.rule_name != "PASSWORD_ASSIGNMENT" for s in secrets) else "CREDENTIALS")
    if pii_matches:
        threat_types.append("PII")
    if code_result["is_code"]:
        threat_types.append("SOURCE_CODE")
    if injection_result["is_injection"]:
        threat_types.append("PROMPT_INJECTION")
    if not threat_types:
        threat_types.append("NONE")

    # rule-based risk score
    if secrets and any(s.severity == "critical" for s in secrets):
        rule_risk = "critical"
    elif injection_result["is_injection"] or (secrets and any(s.severity == "high" for s in secrets)):
        rule_risk = "high"
    elif pii_matches or code_result["is_code"]:
        rule_risk = "medium" if len(pii_matches) <= 1 and not code_result["is_code"] else "high"
    elif secrets:  # any remaining lower-severity secret match (e.g. a custom "medium" rule)
        rule_risk = "medium"
    else:
        rule_risk = "low"

    # ML second opinion
    ml_result = {}
    if _ml_classifier is not None:
        ml_result = _ml_classifier.predict(text)
        ml_risk = ml_result.get("ml_risk_level", "low")
        ml_confidence = ml_result.get("ml_risk_confidence", 0.0)
    else:
        ml_risk = "low"
        ml_confidence = 0.0

    final_risk = _combine_risk(rule_risk, ml_risk, ml_confidence)
    # collapse "critical" into the 3-level Low/Medium/High display, while the
    # underlying secret severity still shows up in reasons/threat_types
    display_risk = "high" if final_risk == "critical" else final_risk

    # Chunked-leak escalation: someone splitting a leak across several
    # messages (one has a name, the next has an account number, etc.) can
    # slip past single-message detection even though each part looks mild.
    # If this user already has repeated medium+ flags in the recent window,
    # treat the current message as high risk regardless of how mild it
    # looks in isolation.
    chunking_flagged = False
    if recent_flag_count >= 3 and display_risk in ("low", "medium"):
        display_risk = "high"
        chunking_flagged = True

    reasons = []
    for s in secrets:
        reasons.append(f"Secret detected: {s.rule_name} (severity: {s.severity})")
    for p in pii_matches:
        reasons.append(f"PII detected: {p.entity_type} ('{p.matched_text}')")
    if code_result["is_code"]:
        reasons.append(f"Source code patterns detected (confidence {code_result['confidence']:.2f})")
    if injection_result["is_injection"]:
        reasons.append(f"Prompt injection pattern matched: {injection_result['matched_patterns'][0]}")
    if chunking_flagged:
        reasons.append(
            f"Escalated: {recent_flag_count} other flagged messages from this user in the last 30 minutes "
            "- possible incremental/chunked data leak"
        )
        threat_types.append("CHUNKED_LEAK_PATTERN")
    if not reasons:
        reasons.append("No sensitive content detected by rule-based scanners.")

    sanitized = sanitize_prompt(text, pii_matches, secrets)

    recommendation = {
        "low": "Safe to send. No action needed.",
        "medium": "Review recommended. Sanitized version can be sent instead of the original.",
        "high": "Blocked by default. Requires explicit user/admin override to send sanitized version.",
    }[display_risk]

    action = "ALLOW" if display_risk == "low" else ("REVIEW" if display_risk == "medium" else "BLOCK")

    audit_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "user_id": user_id,
        "department": department,
        "original_prompt": text,
        "sanitized_prompt": sanitized,
        "risk_level": display_risk,
        "threat_types": threat_types,
        "compliance_tags": compliance_tags,
        "action": action,
        "reasons": reasons,
        "source": source,
        "ml_category": ml_result.get("ml_category"),
        "ml_risk_level": ml_result.get("ml_risk_level"),
    }

    return {
        "risk_level": display_risk,
        "action": action,
        "threat_types": threat_types,
        "compliance_tags": compliance_tags,
        "reasons": reasons,
        "sanitized_prompt": sanitized,
        "recommendation": recommendation,
        "pii_matches": [asdict(p) for p in pii_matches],
        "secret_matches": [asdict(s) for s in secrets],
        "code_detection": code_result,
        "injection_detection": injection_result,
        "ml_result": ml_result,
        "audit_entry": audit_entry,
    }


if __name__ == "__main__":
    import json
    sample = "Here is our banking API code. def transfer_funds(acc, amount): ... Also here's my AWS key AKIAIOSFODNN7EXAMPLE"
    result = analyze_prompt(sample, user_id="demo_user")
    print(json.dumps(result, indent=2, default=str))
