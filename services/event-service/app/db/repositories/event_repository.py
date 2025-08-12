from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.db.models import Event
from app.api.v1.schemas import EventCreate, EventUpdate

class EventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_event(self, event_id: int) -> Event | None:
        result = await self.db.execute(select(Event).filter(Event.id == event_id))
        return result.scalars().first()

    async def get_events(self, skip: int = 0, limit: int = 100) -> list[Event]:
        result = await self.db.execute(select(Event).offset(skip).limit(limit))
        return result.scalars().all()

    async def create_event(self, event: EventCreate) -> Event:
        db_event = Event(**event.dict())
        self.db.add(db_event)
        await self.db.flush()
        await self.db.refresh(db_event)
        return db_event

    async def update_event(self, event_id: int, event: EventUpdate) -> Event | None:
        query = update(Event).where(Event.id == event_id).values(**event.dict(exclude_unset=True))
        await self.db.execute(query)
        await self.db.flush()
        return await self.get_event(event_id)

    async def delete_event(self, event_id: int) -> bool:
        event = await self.get_event(event_id)
        if event:
            await self.db.delete(event)
            await self.db.flush()
            return True
        return False