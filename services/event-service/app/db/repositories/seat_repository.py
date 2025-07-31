from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.db.models import Seat, SeatStatus
from app.api.v1.schemas import SeatCreate, SeatUpdate

class SeatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_seat(self, seat_id: int) -> Seat | None:
        result = await self.db.execute(select(Seat).filter(Seat.id == seat_id))
        return result.scalars().first()

    async def get_seat_by_number(self, event_id: int, seat_number: str) -> Seat | None:
        result = await self.db.execute(select(Seat).filter(Seat.event_id == event_id, Seat.seat_number == seat_number))
        return result.scalars().first()

    async def get_seats(self, event_id: int, skip: int = 0, limit: int = 100) -> list[Seat]:
        result = await self.db.execute(select(Seat).filter(Seat.event_id == event_id).offset(skip).limit(limit))
        return result.scalars().all()

    async def create_seat(self, seat: SeatCreate) -> Seat:
        db_seat = Seat(**seat.dict())
        self.db.add(db_seat)
        await self.db.commit()
        await self.db.refresh(db_seat)
        return db_seat

    async def update_seat_status(self, seat_id: int, status: SeatStatus) -> Seat | None:
        query = update(Seat).where(Seat.id == seat_id).values(status=status)
        await self.db.execute(query)
        await self.db.commit()
        return await self.get_seat(seat_id)

    async def update_seat(self, seat_id: int, seat: SeatUpdate) -> Seat | None:
        query = update(Seat).where(Seat.id == seat_id).values(**seat.dict(exclude_unset=True))
        await self.db.execute(query)
        await self.db.commit()
        return await self.get_seat(seat_id)

    async def delete_seat(self, seat_id: int) -> bool:
        seat = await self.get_seat(seat_id)
        if seat:
            await self.db.delete(seat)
            await self.db.commit()
            return True
        return False