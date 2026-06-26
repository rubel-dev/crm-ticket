# CRM Ticket Classification API

FastAPI service for deterministic CRM support ticket classification. It exposes a health endpoint and a single ticket sorting endpoint with the exact JSON contract required by the judge.

## Endpoints

`GET /health`

Returns:

```json
{"status":"ok"}
```

`POST /sort-ticket`

Request:

```json
{
  "ticket_id": "T-001",
  "channel": "app",
  "locale": "en",
  "message": "I sent 5000 taka to a wrong number this morning, please help me get it back"
}
```

Response:

```json
{
  "ticket_id": "T-001",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer reports sending money to the wrong recipient and requests assistance.",
  "human_review_required": true,
  "confidence": 0.94
}
```

## Local Run

Use Python 3.12 for local development. Python 3.14 may try to compile `pydantic-core` from source and fail during installation.

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000/health`.

## Tests

```bash
python -m pytest tests
```

## Docker

```bash
docker build -t crm-ticket-api .
docker run --rm -p 8000:8000 crm-ticket-api
```

The container binds Uvicorn to `0.0.0.0:8000` for deployment.

## Deployment Notes

Deploy behind a platform-provided HTTPS endpoint such as Render, Railway, Fly.io, or a reverse proxy with TLS termination. No login, database, GPU, or external LLM is required. If secrets are added later, provide them through environment variables only and keep `.env` out of version control.

## Classification Behavior

The rule engine is deterministic and prioritizes safety:

- Phishing or social engineering signals are classified as `phishing_or_social_engineering`, severity `critical`, department `fraud_risk`, and require human review.
- Wrong transfers are `wrong_transfer`, severity `high`, department `dispute_resolution`.
- Failed or deducted payments are `payment_failed`, severity `high`, department `payments_ops`.
- Simple refunds are low severity and routed to `customer_support`.
- Contested refunds are routed to `dispute_resolution`.
- Unknown messages fall back to `other`, severity `low`, department `customer_support`.

Agent summaries are neutral and never ask customers to share OTPs, PINs, passwords, CVV, or full card numbers.
