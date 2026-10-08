"""
Secret / credential scanner.

Scans free text for hard-coded API keys, tokens, and passwords using a set
of regex signatures similar in spirit to gitleaks / trufflehog. Each rule
has a name and a severity so callers can decide how to react.

Supports merging in admin-defined custom rules at call time (see
backend/rules_store.py) so the rule set can grow without a code change.
"""

import re
from dataclasses import dataclass


@dataclass
class SecretMatch:
    rule_name: str
    matched_text: str
    severity: str  # "high" | "critical"
    start: int = 0
    end: int = 0


SECRET_RULES = {
    "AWS_ACCESS_KEY_ID": (re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"), "critical"),
    "AWS_SECRET_ACCESS_KEY": (re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}['\"]?"), "critical"),
    "GOOGLE_API_KEY": (re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"), "critical"),
    "OPENAI_API_KEY": (re.compile(r"\bsk-[A-Za-z0-9]{20,48}\b"), "critical"),
    "ANTHROPIC_API_KEY": (re.compile(r"\bsk-ant-[A-Za-z0-9\-_]{20,95}\b"), "critical"),
    "GITHUB_TOKEN": (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b"), "critical"),
    "SLACK_TOKEN": (re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,72}\b"), "critical"),
    "STRIPE_KEY": (re.compile(r"\b(sk|rk)_(live|test)_[A-Za-z0-9]{24,}\b"), "critical"),
    "PRIVATE_KEY_BLOCK": (re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----"), "critical"),
    "JWT_TOKEN": (re.compile(r"\beyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\b"), "high"),
    "GENERIC_API_KEY_ASSIGNMENT": (re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9\-_/+]{16,}['\"]?"), "high"),
    "PASSWORD_ASSIGNMENT": (re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?\S{6,}['\"]?"), "high"),
    "DB_CONNECTION_STRING": (re.compile(r"(?i)(postgres|mysql|mongodb)(\+\w+)?://[^\s]+:[^\s]+@[^\s]+"), "critical"),
}


def scan_secrets(text: str, custom_rules: dict | None = None):
    """Runs every built-in rule (plus any custom_rules passed in) against
    text and returns non-overlapping matches, first-found wins on overlap."""
    all_rules = dict(SECRET_RULES)
    if custom_rules:
        all_rules.update(custom_rules)

    matches = []
    covered = [False] * (len(text) + 1)
    for rule_name, (pattern, severity) in all_rules.items():
        for m in pattern.finditer(text):
            start, end = m.start(), m.end()
            if any(covered[start:end]):
                continue
            matches.append(SecretMatch(rule_name=rule_name, matched_text=m.group(0), severity=severity, start=start, end=end))
            for i in range(start, end):
                covered[i] = True
    matches.sort(key=lambda m: m.start)
    return matches


if __name__ == "__main__":
    sample = "My AWS key is AKIAIOSFODNN7EXAMPLE and my password: hunter22isbetter"
    for match in scan_secrets(sample):
        print(match)
