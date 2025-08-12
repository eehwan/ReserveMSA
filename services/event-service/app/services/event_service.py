from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories import EventRepository, SeatRepository
from app.db.models import Event, SeatStatus
from app.api.v1.schemas.event_schemas import EventCreate, EventUpdate

class EventService:
    def __init__(self, db: AsyncSession):
        self.event_repo = EventRepository(db)
        self.seat_repo = SeatRepository(db)
        self.db = db

    async def create_event(self, event: EventCreate) -> Event:
        try:
            event_obj = await self.event_repo.create_event(event)
            await self.db.commit()
            return event_obj
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_event(self, event_id: int) -> Event | None:
        return await self.event_repo.get_event(event_id)

    async def get_events(self, skip: int = 0, limit: int = 100) -> list[Event]:
        return await self.event_repo.get_events(skip=skip, limit=limit)

    async def update_event(self, event_id: int, event_update: EventUpdate) -> Event | None:
        try:
            event_obj = await self.event_repo.update_event(event_id, event_update)
            await self.db.commit()
            return event_obj
        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete_event(self, event_id: int) -> bool:
        event = await self.event_repo.get_event(event_id)
        if not event:
            return False

        non_available_seats = await self.seat_repo.get_seats_with_status(
            event_id, [SeatStatus.ALLOCATED, SeatStatus.SOLD]
        )
        if non_available_seats:
            return False

        try:
            result = await self.event_repo.delete_event(event_id)
            await self.db.commit()
            return result
        except Exception as e:
            await self.db.rollback()
            raise e