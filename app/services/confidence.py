from app.schemas import CaseType


def score_confidence(case_type: CaseType, evidence_count: int) -> float:
    base_scores = {
        CaseType.PHISHING_OR_SOCIAL_ENGINEERING: 0.95,
        CaseType.WRONG_TRANSFER: 0.9,
        CaseType.PAYMENT_FAILED: 0.88,
        CaseType.REFUND_REQUEST: 0.84,
        CaseType.OTHER: 0.7,
    }
    evidence_bonus = min(evidence_count, 3) * 0.02
    return min(0.99, max(0.0, round(base_scores[case_type] + evidence_bonus, 2)))
