from app.schemas import CaseType, Severity
from app.services.safety import has_phishing_signal, requires_human_review, sanitize_agent_summary


def test_human_review_required_for_critical() -> None:
    assert requires_human_review(CaseType.OTHER, Severity.CRITICAL) is True


def test_human_review_required_for_high_severity() -> None:
    assert requires_human_review(CaseType.WRONG_TRANSFER, Severity.HIGH) is True


def test_human_review_required_for_phishing() -> None:
    assert requires_human_review(CaseType.PHISHING_OR_SOCIAL_ENGINEERING, Severity.LOW) is True


def test_sanitize_agent_summary_removes_sensitive_instruction() -> None:
    summary = sanitize_agent_summary("Please provide your OTP so support can help.")

    assert "provide your OTP" not in summary


def test_phishing_signal_detects_sensitive_code_request() -> None:
    assert has_phishing_signal("Someone called and asked for my verification code.") is True


def test_phishing_signal_detects_bangla_otp() -> None:
    assert has_phishing_signal("একজন আমাকে ওটিপি দিতে বলেছে") is True
