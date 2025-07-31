from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class EventBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_active: Optional[bool] = True

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: Optional[bool] = None

class Event(EventBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 문자열 타입 힌트로 지연 평가
class EventWithSeats(Event):
    seats: List["Seat"] = []


from app.api.v1.schemas import Seat
EventWithSeats.update_forward_refs()