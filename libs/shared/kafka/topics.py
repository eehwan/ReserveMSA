# shared/kafka/topics.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


# -- Seat 관련 메시지 (좌석 생명주기) -----------------

class SeatLockEvent(BaseModel):
    event_type: Literal["seat.lock"] = "seat.lock"
    order_id: str
    user_id: int
    event_id: int
    seat_num: str
    lock_key: str
    expires_at: datetime
    timestamp: datetime
    version: str = "1.0"


class SeatLockFailedEvent(BaseModel):
    event_type: Literal["seat.lock-failed"] = "seat.lock-failed"
    user_id: int
    event_id: int
    seat_num: str
    reason: str  # "redis_lock_failed" | "race_condition"
    timestamp: datetime
    version: str = "1.0"


class SeatLockRollbackEvent(BaseModel):
    event_type: Literal["seat.lock-rollback"] = "seat.lock-rollback"
    event_id: int
    seat_num: str
    lock_key: str  # Redis lock key to release
    reason: str    # "db_update_failed" | "payment_timeout"
    timestamp: datetime
    version: str = "1.0"


class SeatUnlockEvent(BaseModel):
    event_type: Literal["seat.unlock"] = "seat.unlock"
    event_id: int
    seat_num: str
    lock_key: str  # Redis lock key to release
    timestamp: datetime
    version: str = "1.0"


class SeatSoldEvent(BaseModel):
    event_type: Literal["seat.sold"] = "seat.sold"
    user_id: int
    event_id: int
    seat_num: str
    lock_key: str
    payment_id: str
    timestamp: datetime
    version: str = "1.0"


# -- Payment 관련 메시지 (결제 생명주기) ---------------

class PaymentRequestedEvent(BaseModel):
    event_type: Literal["payment.requested"] = "payment.requested"
    user_id: int
    event_id: int
    seat_num: str
    amount: float
    lock_key: str  # 좌석 추적용
    timestamp: datetime
    version: str = "1.0"


class PaymentVerifiedEvent(BaseModel):
    event_type: Literal["payment.verified"] = "payment.verified"
    payment_key: str
    order_id: str
    amount: int
    approved_at: datetime
    timestamp: datetime
    version: str = "1.0"


class PaymentRejectedEvent(BaseModel):
    event_type: Literal["payment.rejected"] = "payment.rejected"
    payment_key: str
    order_id: str
    failure_reason: str
    timestamp: datetime
    version: str = "1.0"


class PaymentCancelEvent(BaseModel):
    event_type: Literal["payment.cancel"] = "payment.cancel"
    payment_key: str
    order_id: str
    reason: str
    timestamp: datetime
    version: str = "1.0"


class PaymentTimeoutEvent(BaseModel):
    event_type: Literal["payment.timeout"] = "payment.timeout"
    user_id: int
    event_id: int
    seat_num: str
    lock_key: str
    timeout_duration: int  # seconds
    timestamp: datetime
    version: str = "1.0"


# -- Topic 레지스트리 ----------------------------

TOPICS = {
    # Seat 관련
    "seat_lock": {
        "topic": "seat-lock",
        "schema": SeatLockEvent,
    },
    "seat_lock_failed": {
        "topic": "seat-lock-failed", 
        "schema": SeatLockFailedEvent,
    },
    "seat_lock_rollback": {
        "topic": "seat-lock-rollback",
        "schema": SeatLockRollbackEvent,
    },
    
    "seat_unlock": {
        "topic": "seat-unlock",
        "schema": SeatUnlockEvent,
    },
    "seat_sold": {
        "topic": "seat-sold",
        "schema": SeatSoldEvent,
    },
    
    # Payment 관련
    "payment_requested": {
        "topic": "payment-requested",
        "schema": PaymentRequestedEvent,
    },
    "payment_verified": {
        "topic": "payment-verified",
        "schema": PaymentVerifiedEvent,
    },
    "payment_rejected": {
        "topic": "payment-rejected",
        "schema": PaymentRejectedEvent,
    },
    "payment_cancel": {
        "topic": "payment-cancel",
        "schema": PaymentCancelEvent,
    },
    "payment_timeout": {
        "topic": "payment-timeout",
        "schema": PaymentTimeoutEvent,
    },
}