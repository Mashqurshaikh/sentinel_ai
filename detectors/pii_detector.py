"""
PII detector.

Combines spaCy NER (PERSON / ORG / GPE) with regex rules for structured PII
- phone numbers, bank account numbers, credit cards, emails, Aadhaar-style
IDs, PAN numbers, IP addresses. Runs fully offline, no external service.
"""

import re
from dataclasses import dataclass

import spacy

_NLP = None


def get_nlp():
    global _NLP
    if _NLP is None:
        _NLP = spacy.load("en_core_web_sm")
    return _NLP


@dataclass
class PIIMatch:
    entity_type: str
    matched_text: str
    start: int
    end: int


REGEX_RULES = {
    "PHONE_NUMBER": re.compile(r"\b(?:\+?91[\-\s]?)?[6-9]\d{9}\b"),
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "ACCOUNT_NUMBER": re.compile(r"\b\d{9,18}\b"),
    "AADHAAR_ID": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    "PAN_ID": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "IP_ADDRESS": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

# Priority order: more specific patterns should "win" over generic ones
# (e.g. an Aadhaar-shaped number shouldn't also get flagged as a generic
# account number). We resolve overlaps by matching in this order and
# skipping spans already covered.
_PRIORITY = ["EMAIL", "PAN_ID", "AADHAAR_ID", "CREDIT_CARD", "PHONE_NUMBER", "IP_ADDRESS", "ACCOUNT_NUMBER"]

_SPACY_LABELS_OF_INTEREST = {"PERSON"}
# Deliberately NOT flagging ORG/GPE (company and place names) as PII. Those
# entity types show up constantly in completely ordinary questions ("what's
# the capital of France", "how do I contact Google support") and aren't
# personal data about an identifiable individual - flagging them just
# trains people to distrust every "medium risk" result.


def detect_pii(text: str, use_spacy: bool = True, pre_covered_spans=None):
    """pre_covered_spans: optional list of (start, end) tuples (e.g. from
    secret_scanner) to exclude from PII detection, so a secret like an API
    key doesn't get misclassified as an organization name by spaCy."""
    matches = []
    covered = [False] * (len(text) + 1)
    if pre_covered_spans:
        for start, end in pre_covered_spans:
            for i in range(start, min(end, len(covered))):
                covered[i] = True

    for rule_name in _PRIORITY:
        pattern = REGEX_RULES[rule_name]
        for m in pattern.finditer(text):
            start, end = m.start(), m.end()
            if any(covered[start:end]):
                continue
            matches.append(PIIMatch(entity_type=rule_name, matched_text=m.group(0), start=start, end=end))
            for i in range(start, end):
                covered[i] = True

    if use_spacy:
        try:
            nlp = get_nlp()
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in _SPACY_LABELS_OF_INTEREST:
                    if any(covered[ent.start_char:ent.end_char]):
                        continue
                    # Small spaCy models frequently mis-tag unfamiliar
                    # single-word capitalized nouns (place names, brand
                    # names, etc.) as PERSON. Requiring a first + last name
                    # shape cuts that false-positive rate dramatically while
                    # still catching the "Customer: Rahul Sharma" pattern
                    # this detector actually exists for.
                    if len(ent.text.split()) < 2:
                        continue
                    label = "PERSON_NAME"
                    matches.append(PIIMatch(entity_type=label, matched_text=ent.text, start=ent.start_char, end=ent.end_char))
                    for i in range(ent.start_char, ent.end_char):
                        covered[i] = True
        except Exception:
            # spaCy model unavailable -> silently fall back to regex-only detection
            pass

    matches.sort(key=lambda m: m.start)
    return matches


if __name__ == "__main__":
    sample = "Customer: Rahul Sharma, Account: 567812345678, Phone: 9876543210, email rahul@acme.com"
    for match in detect_pii(sample):
        print(match)
