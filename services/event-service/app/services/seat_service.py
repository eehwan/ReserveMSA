from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories import SeatRepository
from app.api.v1.schemas import SeatCreate, SeatUpdate
from app.db.models import Seat

class SeatService:
    def __init__(self, db: AsyncSession):
        self.seat_repo = SeatRepository(db)

    async def create_seat(self, seat: SeatCreate) -> Seat:
        existing_seat = await self.seat_repo.get_seat_by_number(seat.event_id, seat.seat_number)
        if existing_seat:
            raise ValueError("Seat with this number already exists for this event")
        return await self.seat_repo.create_seat(seat)

    async def get_seat(self, seat_id: int) -> Seat | None:
        return await self.seat_repo.get_seat(seat_id)

    async def get_seats(self, event_id: int, skip: int = 0, limit: int = 100) -> list[Seat]:
        return await self.seat_repo.get_seats(event_id=event_id, skip=skip, limit=limit)

    async def update_seat(self, seat_id: int, seat_update: SeatUpdate) -> Seat | None:
        return await self.seat_repo.update_seat(seat_id, seat_update)

    async def delete_seat(self, seat_id: int) -> bool:
        return await self.seat_repo.delete_seat(seat_id)