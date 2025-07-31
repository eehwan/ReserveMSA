from sqlalchemy import Column, Integer, String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base

class SeatStatus(enum.Enum):
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    SOLD = "sold"

class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    seat_number = Column(String, index=True)
    status = Column(Enum(SeatStatus), default=SeatStatus.AVAILABLE)
    price = Column(Integer)

    event = relationship("Event", back_populates="seats")

    __table_args__ = (UniqueConstraint('event_id', 'seat_number', name='_event_seat_uc'),)