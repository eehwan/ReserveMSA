from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.api.v1.schemas import Seat, SeatCreate, SeatUpdate
from app.services import SeatService

router = APIRouter()

@router.post("/", response_model=Seat, status_code=status.HTTP_201_CREATED)
async def create_seat(seat: SeatCreate, db: AsyncSession = Depends(get_db)):
    seat_service = SeatService(db)
    try:
        return await seat_service.create_seat(seat)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{seat_id}", response_model=Seat)
async def get_seat(seat_id: int, db: AsyncSession = Depends(get_db)):
    seat_service = SeatService(db)
    seat = await seat_service.get_seat(seat_id)
    if not seat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found")
    return seat

@router.get("/event/{event_id}", response_model=List[Seat])
async def get_seats_for_event(event_id: int, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    seat_service = SeatService(db)
    return await seat_service.get_seats(event_id=event_id, skip=skip, limit=limit)

@router.put("/{seat_id}", response_model=Seat)
async def update_seat(seat_id: int, seat_update: SeatUpdate, db: AsyncSession = Depends(get_db)):
    seat_service = SeatService(db)
    updated_seat = await seat_service.update_seat(seat_id, seat_update)
    if not updated_seat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found")
    return updated_seat

@router.delete("/{seat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seat(seat_id: int, db: AsyncSession = Depends(get_db)):
    seat_service = SeatService(db)
    deleted = await seat_service.delete_seat(seat_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found")
    return