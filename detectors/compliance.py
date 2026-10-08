"""
Compliance tagging.

Maps detected entity types to the data-protection regulations they're
typically covered by, so a flagged prompt can carry a "this touches GDPR /
PCI-DSS / DPDP" label for audit purposes. This is a coarse mapping meant to
help a security reviewer triage, not a legal classification.
"""

COMPLIANCE_MAP = {
    "PERSON_NAME": ["GDPR", "DPDP Act (India)"],
    "PHONE_NUMBER": ["GDPR", "DPDP Act (India)", "TCPA"],
    "EMAIL": ["GDPR", "DPDP Act (India)", "CAN-SPAM"],
    "ACCOUNT_NUMBER": ["PCI-DSS", "GLBA"],
    "CREDIT_CARD": ["PCI-DSS"],
    "AADHAAR_ID": ["DPDP Act (India)", "Aadhaar Act"],
    "PAN_ID": ["DPDP Act (India)", "IT Act (India)"],
    "IP_ADDRESS": ["GDPR"],
    "AWS_ACCESS_KEY_ID": ["SOC 2", "ISO 27001"],
    "AWS_SECRET_ACCESS_KEY": ["SOC 2", "ISO 27001"],
    "GOOGLE_API_KEY": ["SOC 2", "ISO 27001"],
    "OPENAI_API_KEY": ["SOC 2", "ISO 27001"],
    "ANTHROPIC_API_KEY": ["SOC 2", "ISO 27001"],
    "GITHUB_TOKEN": ["SOC 2", "ISO 27001"],
    "SLACK_TOKEN": ["SOC 2", "ISO 27001"],
    "STRIPE_KEY": ["PCI-DSS", "SOC 2"],
    "PRIVATE_KEY_BLOCK": ["SOC 2", "ISO 27001"],
    "JWT_TOKEN": ["SOC 2"],
    "GENERIC_API_KEY_ASSIGNMENT": ["SOC 2", "ISO 27001"],
    "PASSWORD_ASSIGNMENT": ["SOC 2", "ISO 27001", "NIST 800-53"],
    "DB_CONNECTION_STRING": ["SOC 2", "ISO 27001"],
}


def get_compliance_tags(pii_matches, secret_matches) -> list:
    tags = set()
    for m in pii_matches:
        for tag in COMPLIANCE_MAP.get(m.entity_type, []):
            tags.add(tag)
    for s in secret_matches:
        for tag in COMPLIANCE_MAP.get(s.rule_name, []):
            tags.add(tag)
    return sorted(tags)
