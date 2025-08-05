from pydantic import BaseModel

class ReservationRequest(BaseModel):
    event_id: int
    seat_num: str
