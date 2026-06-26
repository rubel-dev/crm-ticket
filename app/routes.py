from fastapi import APIRouter

from app.schemas import (
    HealthResponse,
    TicketRequest,
    TicketResponse,
)
from app.services.reasoning_engine import classify_ticket


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/sort-ticket", response_model=TicketResponse)
def sort_ticket(ticket: TicketRequest) -> TicketResponse:
    return classify_ticket(ticket)
