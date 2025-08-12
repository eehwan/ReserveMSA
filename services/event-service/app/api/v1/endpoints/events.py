from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.api.v1.schemas import Event, EventCreate, EventUpdate, EventWithSeats, Seat, SeatCreate, SeatUpdate
from app.services import EventService, SeatService

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


@router.post("/{event_id}/seats", response_model=Seat, status_code=status.HTTP_201_CREATED)
async def create_seat(event_id: int, seat_data: dict, db: AsyncSession = Depends(get_db)):
    seat_data["event_id"] = event_id
    seat = SeatCreate(**seat_data)
    seat_service = SeatService(db)
    try:
        return await seat_service.create_seat(seat)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{event_id}/seats", response_model=List[Seat])
async def get_seats_for_event(event_id: int, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    seat_service = SeatService(db)
    return await seat_service.get_seats(event_id=event_id, skip=skip, limit=limit)

@router.get("/{event_id}/seats/{seat_number}", response_model=Seat)
async def get_seat_by_number(event_id: int, seat_number: str, db: AsyncSession = Depends(get_db)):
    seat_service = SeatService(db)
    seat = await seat_service.get_seat_by_number(event_id, seat_number)
    if not seat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found")
    return seat

@router.put("/{event_id}/seats/{seat_id}", response_model=Seat)
async def update_seat(event_id: int, seat_id: int, seat_update: SeatUpdate, db: AsyncSession = Depends(get_db)):
    seat_service = SeatService(db)
    seat = await seat_service.get_seat(seat_id)
    if not seat or seat.event_id != event_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found in this event")
    
    updated_seat = await seat_service.update_seat(seat_id, seat_update)
    if not updated_seat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found")
    return updated_seat

@router.delete("/{event_id}/seats/{seat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seat(event_id: int, seat_id: int, db: AsyncSession = Depends(get_db)):
    seat_service = SeatService(db)
    seat = await seat_service.get_seat(seat_id)
    if not seat or seat.event_id != event_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found in this event")
    
    deleted = await seat_service.delete_seat(seat_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found")
    return