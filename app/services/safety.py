import re

from app.schemas import CaseType, Severity
from app.utils.text import contains_any, normalize_text


SENSITIVE_TERMS = (
    "pin",
    "otp",
    "password",
    "passcode",
    "full card",
    "card number",
    "cvv",
    "পিন",
    "ওটিপি",
    "পাসওয়ার্ড",
    "পাসওয়ার্ড",
)

PHISHING_TERMS = (
    "otp",
    "pin",
    "password",
    "passcode",
    "cvv",
    "full card",
    "card number",
    "verification code",
    "security code",
    "scam",
    "fraud",
    "phishing",
    "pretending",
    "fake support",
    "unknown caller",
    "suspicious call",
    "suspicious sms",
    "share code",
    "asked for code",
    "asked me for",
    "ওটিপি",
    "otp ta",
    "পিন",
    "পাসওয়ার্ড",
    "পাসওয়ার্ড",
    "প্রতার",
    "ভুয়া",
    "ভুয়া",
    "কল করে",
)

_FORBIDDEN_INSTRUCTION_PATTERNS = (
    re.compile(r"\b(share|send|provide|give|tell)\b.{0,40}\b(otp|pin|password|passcode|cvv)\b", re.I),
    re.compile(r"\b(full card number|card number)\b", re.I),
)


def has_phishing_signal(message: str) -> bool:
    text = normalize_text(message)
    return contains_any(text, PHISHING_TERMS)


def requires_human_review(case_type: CaseType, severity: Severity) -> bool:
    return (
        severity in (Severity.HIGH, Severity.CRITICAL)
        or case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING
    )


def sanitize_agent_summary(summary: str) -> str:
    cleaned = summary.strip()
    for pattern in _FORBIDDEN_INSTRUCTION_PATTERNS:
        cleaned = pattern.sub("reported a sensitive information request", cleaned)
    return cleaned
