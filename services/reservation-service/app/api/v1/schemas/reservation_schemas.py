from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReservationRequest(BaseModel):
    event_id: int
    seat_num: str

class ReservationResponse(BaseModel):
    reservation_id: str
    event_id: int
    seat_num: str
    expires_at: datetime
    status: str

class ReservationStatusResponse(BaseModel):
    reservation_id: str
    status: str
    event_id: Optional[int] = None
    seat_num: Optional[str] = None
    expires_at: Optional[datetime] = None
