# shared/kafka/topics.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


# -- Reservation 관련 메시지 ----------------------

class SeatReservedEvent(BaseModel):
    event_type: Literal["seat_reserved"] = "seat_reserved"
    reservation_id: str
    seat_id: str
    user_id: int
    timestamp: datetime
    version: str = "1.0"


class ReservationConfirmedEvent(BaseModel):
    event_type: Literal["reservation_confirmed"] = "reservation_confirmed"
    reservation_id: str
    confirmed_at: datetime
    version: str = "1.0"


# -- Payment 관련 메시지 --------------------------

class PaymentRequestedEvent(BaseModel):
    event_type: Literal["payment_requested"] = "payment_requested"
    reservation_id: str
    user_id: int
    amount: float
    requested_at: datetime
    version: str = "1.0"


class PaymentCompletedEvent(BaseModel):
    event_type: Literal["payment_completed"] = "payment_completed"
    reservation_id: str
    payment_id: str
    completed_at: datetime
    version: str = "1.0"


# -- Topic 레지스트리 ----------------------------

TOPICS = {
    "seat_reserved": {
        "topic": "reservation-events",
        "schema": SeatReservedEvent,
    },
    "reservation_confirmed": {
        "topic": "reservation-confirmed",
        "schema": ReservationConfirmedEvent,
    },
    "payment_requested": {
        "topic": "payment-events",
        "schema": PaymentRequestedEvent,
    },
    "payment_completed": {
        "topic": "payment-completed",
        "schema": PaymentCompletedEvent,
    },
}