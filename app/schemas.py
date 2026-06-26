from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Channel(str, Enum):
    APP = "app"
    SMS = "sms"
    CALL_CENTER = "call_center"
    MERCHANT_PORTAL = "merchant_portal"


class Locale(str, Enum):
    BN = "bn"
    EN = "en"
    MIXED = "mixed"


class CaseType(str, Enum):
    WRONG_TRANSFER = "wrong_transfer"
    PAYMENT_FAILED = "payment_failed"
    REFUND_REQUEST = "refund_request"
    PHISHING_OR_SOCIAL_ENGINEERING = "phishing_or_social_engineering"
    OTHER = "other"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Department(str, Enum):
    CUSTOMER_SUPPORT = "customer_support"
    DISPUTE_RESOLUTION = "dispute_resolution"
    PAYMENTS_OPS = "payments_ops"
    FRAUD_RISK = "fraud_risk"


class TicketRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ticket_id: str = Field(min_length=1)
    channel: Channel | None = None
    locale: Locale | None = None
    message: str = Field(min_length=1)

    @field_validator("ticket_id", "message", mode="before")
    @classmethod
    def require_non_empty_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Field must be a non-empty string.")
        return value

    @field_validator("channel", mode="before")
    @classmethod
    def ignore_unknown_channel(cls, value: Any) -> Any:
        if value is None or isinstance(value, Channel):
            return value
        if isinstance(value, str):
            normalized = value.strip()
            return normalized if normalized in {item.value for item in Channel} else None
        return value

    @field_validator("locale", mode="before")
    @classmethod
    def ignore_unknown_locale(cls, value: Any) -> Any:
        if value is None or isinstance(value, Locale):
            return value
        if isinstance(value, str):
            normalized = value.strip()
            return normalized if normalized in {item.value for item in Locale} else None
        return value


class TicketResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticket_id: str
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str
    human_review_required: bool
    confidence: float = Field(ge=0.0, le=1.0)


class HealthResponse(BaseModel):
    status: str
