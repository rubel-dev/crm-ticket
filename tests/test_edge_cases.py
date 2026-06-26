from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_optional_fields_can_be_omitted() -> None:
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-003", "message": "App crashed during login."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ticket_id"] == "T-003"
    assert body["case_type"] == "other"
    assert 0 <= body["confidence"] <= 1


def test_bangla_wrong_transfer() -> None:
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-004", "locale": "bn", "message": "আমি ভুল নাম্বারে টাকা পাঠিয়েছি"},
    )

    assert response.status_code == 200
    assert response.json()["case_type"] == "wrong_transfer"


def test_unknown_channel_is_ignored_without_crashing() -> None:
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-005", "channel": "telegram", "message": "Need help."},
    )

    assert response.status_code == 200
    assert response.json()["case_type"] == "other"


def test_unknown_locale_is_ignored_without_crashing() -> None:
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-006", "locale": "jp", "message": "Need help."},
    )

    assert response.status_code == 200
    assert response.json()["case_type"] == "other"


def test_missing_required_message_returns_json_validation_error() -> None:
    response = client.post("/sort-ticket", json={"ticket_id": "T-007"})

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/json")


def test_empty_message_returns_validation_error() -> None:
    response = client.post("/sort-ticket", json={"ticket_id": "T-008", "message": ""})

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/json")


def test_long_mixed_language_phishing_message() -> None:
    message = "hello " * 400 + "OTP ta share korte bolse"
    response = client.post("/sort-ticket", json={"ticket_id": "T-009", "message": message})

    assert response.status_code == 200
    body = response.json()
    assert body["case_type"] == "phishing_or_social_engineering"
    assert body["severity"] == "critical"
    assert body["human_review_required"] is True


def test_hidden_phishing_code_terms() -> None:
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-010", "message": "A bkash agent asked me to send code to verify account."},
    )

    assert response.status_code == 200
    assert response.json()["case_type"] == "phishing_or_social_engineering"


def test_broader_wrong_transfer_terms() -> None:
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-011", "message": "I sent money to another person by mistake transfer."},
    )

    assert response.status_code == 200
    assert response.json()["case_type"] == "wrong_transfer"


def test_deducted_without_payment_context_is_not_payment_failed() -> None:
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-012", "message": "Wrong transfer deducted my money from my wallet."},
    )

    assert response.status_code == 200
    assert response.json()["case_type"] == "wrong_transfer"
