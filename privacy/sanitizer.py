"""
Privacy sanitizer.

Takes the raw prompt plus detection results from pii_detector and
secret_scanner, and produces a sanitized version with every sensitive span
replaced by a placeholder token (<Person>, <Account_Number>, <API_KEY>...).
"""

PLACEHOLDER_MAP = {
    "PERSON_NAME": "<Person>",
    "ORGANIZATION": "<Organization>",
    "LOCATION": "<Location>",
    "PHONE_NUMBER": "<Phone_Number>",
    "EMAIL": "<Email>",
    "CREDIT_CARD": "<Credit_Card_Number>",
    "ACCOUNT_NUMBER": "<Account_Number>",
    "AADHAAR_ID": "<Aadhaar_ID>",
    "PAN_ID": "<PAN_ID>",
    "IP_ADDRESS": "<IP_Address>",
}


def sanitize_prompt(text: str, pii_matches, secret_matches) -> str:
    """Replaces every detected PII/secret span with a placeholder token.
    Works by building a list of (start, end, replacement) spans and applying
    them right-to-left so earlier offsets stay valid."""
    spans = []

    for m in pii_matches:
        placeholder = PLACEHOLDER_MAP.get(m.entity_type, f"<{m.entity_type}>")
        spans.append((m.start, m.end, placeholder))

    # secret matches don't carry character offsets (regex found across the
    # whole rule-set, possibly overlapping) -- do a straightforward find &
    # replace instead, longest matches first to avoid partial overlaps.
    sanitized = text
    for span_start, span_end, placeholder in sorted(spans, key=lambda s: -s[0]):
        sanitized = sanitized[:span_start] + placeholder + sanitized[span_end:]

    for secret in sorted(secret_matches, key=lambda s: -len(s.matched_text)):
        if secret.matched_text in sanitized:
            sanitized = sanitized.replace(secret.matched_text, f"<{secret.rule_name}>")

    return sanitized


if __name__ == "__main__":
    from pii_detector import detect_pii  # noqa
    from secret_scanner import scan_secrets  # noqa

    sample = "Customer: Rahul Sharma, Account: 567812345678, Phone: 9876543210. AWS key AKIAIOSFODNN7EXAMPLE"
    pii = detect_pii(sample)
    secrets = scan_secrets(sample)
    print(sanitize_prompt(sample, pii, secrets))
