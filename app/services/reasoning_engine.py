from dataclasses import dataclass

from app.schemas import CaseType, Department, Severity, TicketRequest, TicketResponse
from app.services.confidence import score_confidence
from app.services.safety import (
    has_phishing_signal,
    requires_human_review,
    sanitize_agent_summary,
)
from app.utils.text import contains_any, normalize_text


WRONG_TRANSFER_TERMS = (
    "wrong number",
    "wrong recipient",
    "wrong account",
    "wrong mobile",
    "wrong wallet",
    "another person",
    "sent to another",
    "sent money to another",
    "sent to someone else",
    "mistake transfer",
    "mistaken transfer",
    "mistakenly sent",
    "sent by mistake",
    "wrong transfer",
    "incorrect number",
    "incorrect recipient",
    "ভুল নাম্বার",
    "ভুল নম্বর",
    "ভুল একাউন্ট",
    "ভুল অ্যাকাউন্ট",
    "ভুল করে",
)

PAYMENT_FAILED_TERMS = (
    "payment failed",
    "transaction failed",
    "failed transaction",
    "balance deducted",
    "money deducted",
    "amount deducted",
    "charged but",
    "debited",
    "deducted",
    "পেমেন্ট ফেইল",
    "পেমেন্ট ফেল",
    "টাকা কেটে",
    "ব্যালেন্স কেটে",
    "লেনদেন ব্যর্থ",
)

PAYMENT_CONTEXT_TERMS = (
    "payment",
    "transaction",
    "checkout",
    "merchant payment",
    "bill payment",
    "recharge",
    "cashout",
    "cash out",
    "পেমেন্ট",
    "লেনদেন",
)

DEDUCTION_TERMS = (
    "balance deducted",
    "money deducted",
    "amount deducted",
    "debited",
    "deducted",
    "charged",
    "cut from balance",
    "টাকা কেটে",
    "ব্যালেন্স কেটে",
)

PAYMENT_FAILURE_EXPLICIT_TERMS = (
    "payment failed",
    "transaction failed",
    "failed transaction",
    "charged but",
    "পেমেন্ট ফেইল",
    "পেমেন্ট ফেল",
    "লেনদেন ব্যর্থ",
)

REFUND_TERMS = (
    "refund",
    "return my money",
    "money back",
    "cancel order",
    "changed my mind",
    "merchant refuses",
    "refuses refund",
    "রিফান্ড",
    "টাকা ফেরত",
    "ফেরত চাই",
)

CONTESTED_REFUND_TERMS = (
    "merchant refuses",
    "refuses refund",
    "not delivered",
    "damaged",
    "dispute",
    "merchant denied",
    "বণিক",
    "মার্চেন্ট",
    "দেয়নি",
    "দেয়নি",
)

AMOUNT_TERMS = ("bdt", "taka", "tk", "৳")


@dataclass(frozen=True)
class Classification:
    case_type: CaseType
    severity: Severity
    department: Department
    evidence: tuple[str, ...]


def classify_ticket(ticket: TicketRequest) -> TicketResponse:
    classification = classify_message(ticket.message)
    summary = sanitize_agent_summary(build_agent_summary(classification))
    confidence = score_confidence(classification.case_type, len(classification.evidence))

    return TicketResponse(
        ticket_id=ticket.ticket_id,
        case_type=classification.case_type,
        severity=classification.severity,
        department=classification.department,
        agent_summary=summary,
        human_review_required=requires_human_review(
            classification.case_type,
            classification.severity,
        ),
        confidence=confidence,
    )


def classify_message(message: str) -> Classification:
    text = normalize_text(message)

    if has_phishing_signal(text):
        return Classification(
            case_type=CaseType.PHISHING_OR_SOCIAL_ENGINEERING,
            severity=Severity.CRITICAL,
            department=Department.FRAUD_RISK,
            evidence=("sensitive_credential_or_fraud_signal",),
        )

    if contains_any(text, WRONG_TRANSFER_TERMS):
        evidence = ("wrong_recipient_signal",)
        if contains_any(text, AMOUNT_TERMS) or any(char.isdigit() for char in text):
            evidence = evidence + ("amount_signal",)
        return Classification(
            case_type=CaseType.WRONG_TRANSFER,
            severity=Severity.HIGH,
            department=Department.DISPUTE_RESOLUTION,
            evidence=evidence,
        )

    has_failed_payment = contains_any(text, PAYMENT_FAILURE_EXPLICIT_TERMS)
    has_contextual_deduction = contains_any(text, PAYMENT_CONTEXT_TERMS) and contains_any(text, DEDUCTION_TERMS)
    if has_failed_payment or has_contextual_deduction:
        evidence = ("payment_failure_signal",)
        if "deduct" in text or "debited" in text or "কেটে" in text:
            evidence = evidence + ("balance_deduction_signal",)
        return Classification(
            case_type=CaseType.PAYMENT_FAILED,
            severity=Severity.HIGH,
            department=Department.PAYMENTS_OPS,
            evidence=evidence,
        )

    if contains_any(text, REFUND_TERMS):
        contested = contains_any(text, CONTESTED_REFUND_TERMS)
        return Classification(
            case_type=CaseType.REFUND_REQUEST,
            severity=Severity.MEDIUM if contested else Severity.LOW,
            department=Department.DISPUTE_RESOLUTION if contested else Department.CUSTOMER_SUPPORT,
            evidence=("refund_signal", "contested_refund_signal") if contested else ("refund_signal",),
        )

    return Classification(
        case_type=CaseType.OTHER,
        severity=Severity.LOW,
        department=Department.CUSTOMER_SUPPORT,
        evidence=(),
    )


def build_agent_summary(classification: Classification) -> str:
    summaries = {
        CaseType.PHISHING_OR_SOCIAL_ENGINEERING: "Customer reports a suspicious contact or sensitive information request.",
        CaseType.WRONG_TRANSFER: "Customer reports sending money to the wrong recipient and requests assistance.",
        CaseType.PAYMENT_FAILED: "Customer reports a failed payment or deducted balance and requests assistance.",
        CaseType.REFUND_REQUEST: "Customer requests a refund or money return related to a transaction.",
        CaseType.OTHER: "Customer reports a general support issue that does not match the main ticket categories.",
    }
    return summaries[classification.case_type]
