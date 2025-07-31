from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.api.v1.schemas import Event, EventCreate, EventUpdate, EventWithSeats
from app.services import EventService

router = APIRouter()

@router.post("/", response_model=Event, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    event_service = EventService(db)
    return await event_service.create_event(event)

@router.get("/{event_id}", response_model=EventWithSeats)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    event_service = EventService(db)
    event = await event_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event

@router.get("/", response_model=List[Event])
async def get_all_events(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    event_service = EventService(db)
    return await event_service.get_events(skip=skip, limit=limit)

@router.put("/{event_id}", response_model=Event)
async def update_event(event_id: int, event_update: EventUpdate, db: AsyncSession = Depends(get_db)):
    event_service = EventService(db)
    updated_event = await event_service.update_event(event_id, event_update)
    if not updated_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return updated_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db)):
    event_service = EventService(db)
    deleted = await event_service.delete_event(event_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete event: some seats are not AVAILABLE or event not found")
    return