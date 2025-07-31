from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories import EventRepository, SeatRepository
from app.db.models import Event, SeatStatus
from app.api.v1.schemas.event_schemas import EventCreate, EventUpdate

class EventService:
    def __init__(self, db: AsyncSession):
        self.event_repo = EventRepository(db)
        self.seat_repo = SeatRepository(db)

    async def create_event(self, event: EventCreate) -> Event:
        return await self.event_repo.create_event(event)

    async def get_event(self, event_id: int) -> Event | None:
        return await self.event_repo.get_event(event_id)

    async def get_events(self, skip: int = 0, limit: int = 100) -> list[Event]:
        return await self.event_repo.get_events(skip=skip, limit=limit)

    async def update_event(self, event_id: int, event_update: EventUpdate) -> Event | None:
        return await self.event_repo.update_event(event_id, event_update)

    async def delete_event(self, event_id: int) -> bool:
        event = await self.event_repo.get_event(event_id)
        if not event:
            return False

        seats = await self.seat_repo.get_seats(event_id) # Changed to get_seats

        for seat in seats:
            if seat.status != SeatStatus.AVAILABLE:
                return False  # Cannot delete if any seat is not AVAILABLE

        # If all seats are AVAILABLE, proceed with deletion
        # The cascade option in the Event model will handle seat deletion
        return await self.event_repo.delete_event(event_id)