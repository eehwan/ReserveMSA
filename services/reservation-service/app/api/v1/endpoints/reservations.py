from fastapi import APIRouter

router = APIRouter()

@router.post("/reservations", status_code=202)
async def reserve_seat():
    # TODO: Implement seat reservation logic
    return {"message": "Reservation request accepted"}
