from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories import SeatRepository
from app.api.v1.schemas import SeatCreate, SeatUpdate
from app.db.models import Seat, SeatStatus

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

    async def allocate_seat(self, event_id: int, seat_num: str, user_id: int, lock_key: str) -> bool:
        """
        좌석 상태를 AVAILABLE에서 ALLOCATED로 변경합니다.
        """
        seat = await self.seat_repo.get_seat_by_number(event_id, seat_num)
        if not seat:
            return False # 좌석이 존재하지 않음

        rows_affected = await self.seat_repo.update_seat_status(
            seat.id, 
            SeatStatus.ALLOCATED, 
            expected_status=SeatStatus.AVAILABLE, 
            user_id=user_id, 
            lock_key=lock_key
        )
        return rows_affected > 0

    async def release_seat(self, event_id: int, seat_num: str, lock_key: str) -> bool:
        """
        좌석 상태를 ALLOCATED에서 AVAILABLE로 변경합니다.
        lock_key가 일치하는 경우에만 해제합니다.
        """
        seat = await self.seat_repo.get_seat_by_number(event_id, seat_num)
        if not seat:
            return False
        
        if seat.status == SeatStatus.ALLOCATED and seat.lock_key == lock_key:
            rows_affected = await self.seat_repo.update_seat_status(
                seat.id, 
                SeatStatus.AVAILABLE, 
                expected_status=SeatStatus.ALLOCATED, 
                user_id=None, 
                lock_key=None
            )
            return rows_affected > 0
        return False

    async def sell_seat(self, event_id: int, seat_num: str, payment_id: str) -> bool:
        """
        좌석 상태를 ALLOCATED에서 SOLD로 변경합니다.
        """
        seat = await self.seat_repo.get_seat_by_number(event_id, seat_num)
        if not seat:
            return False
        
        rows_affected = await self.seat_repo.update_seat_status(
            seat.id, 
            SeatStatus.SOLD, 
            expected_status=SeatStatus.ALLOCATED, 
            user_id=seat.user_id, 
            lock_key=seat.lock_key # 기존 user_id와 lock_key 유지
        )
        return rows_affected > 0