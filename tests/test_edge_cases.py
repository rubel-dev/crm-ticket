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


def test_invalid_channel_returns_json_validation_error() -> None:
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-005", "channel": "telegram", "message": "Need help."},
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/json")


def test_invalid_locale_returns_json_validation_error() -> None:
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-006", "locale": "jp", "message": "Need help."},
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/json")


def test_missing_required_message_returns_json_validation_error() -> None:
    response = client.post("/sort-ticket", json={"ticket_id": "T-007"})

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/json")


def test_empty_message_is_handled_without_500() -> None:
    response = client.post("/sort-ticket", json={"ticket_id": "T-008", "message": ""})

    assert response.status_code == 200
    body = response.json()
    assert body["ticket_id"] == "T-008"
    assert body["case_type"] == "other"
    assert 0 <= body["confidence"] <= 1


def test_long_mixed_language_phishing_message() -> None:
    message = "hello " * 400 + "OTP ta share korte bolse"
    response = client.post("/sort-ticket", json={"ticket_id": "T-009", "message": message})

    assert response.status_code == 200
    body = response.json()
    assert body["case_type"] == "phishing_or_social_engineering"
    assert body["severity"] == "critical"
    assert body["human_review_required"] is True
