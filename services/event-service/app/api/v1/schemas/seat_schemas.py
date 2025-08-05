from typing import Optional
from pydantic import BaseModel
from app.db.models import SeatStatus

class SeatBase(BaseModel):
    event_id: int
    seat_number: str
    status: Optional[SeatStatus] = SeatStatus.AVAILABLE
    price: int

class SeatCreate(SeatBase):
    pass

class SeatUpdate(BaseModel):
    event_id: Optional[int] = None
    seat_number: Optional[str] = None
    status: Optional[SeatStatus] = None
    price: Optional[int] = None

class Seat(SeatBase):
    id: int
    user_id: Optional[int] = None
    lock_key: Optional[str] = None

    class Config:
        from_attributes = True