import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from redis.asyncio import Redis
from shared.kafka.producer import KafkaProducer

from app.core.config import settings
from app.events.publishers import ReservationEventPublisher
from app.services.tasks import release_seat_task
from app.api.v1.schemas.reservation_schemas import ReservationResponse, ReservationStatusResponse

class ReservationService:
    def __init__(self, redis_client: Redis, kafka_producer: KafkaProducer):
        self.redis_client = redis_client
        self.event_publisher = ReservationEventPublisher(kafka_producer)

    async def reserve_seat(self, user_id: int, event_id: int, seat_num: str) -> ReservationResponse:
        """
        Attempts to reserve a seat using Redis SETNX for atomicity.
        If successful, generates reservation_id and returns reservation details.
        """
        # Generate reservation ID
        reservation_id = f"res_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        
        redis_key = f"seat:{event_id}:{seat_num}"
        lock_value = f"{user_id}:{reservation_id}"
        
        is_lock_acquired = await self.redis_client.set(
            redis_key, lock_value, nx=True, ex=settings.SEAT_RESERVATION_TIMEOUT
        )
        
        if not is_lock_acquired:
            await self.event_publisher.publish_seat_lock_failed(
                user_id=user_id,
                event_id=event_id,
                seat_num=seat_num,
                reason="redis_lock_failed"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Seat already reserved.",
            )
            
        try:
            expires_at = datetime.now() + timedelta(seconds=settings.SEAT_RESERVATION_TIMEOUT)
            
            await self.event_publisher.publish_seat_lock(
                reservation_id=reservation_id,
                user_id=user_id,
                event_id=event_id,
                seat_num=seat_num,
                lock_key=lock_value,
                expires_at=expires_at
            )

            # Schedule the timeout task with a small buffer
            release_seat_task.apply_async(
                args=[event_id, seat_num, lock_value],
                countdown=settings.SEAT_RESERVATION_TIMEOUT + 10
            )
            
            return ReservationResponse(
                reservation_id=reservation_id,
                event_id=event_id,
                seat_num=seat_num,
                expires_at=expires_at,
                status="reserved"
            )

        except Exception as e:
            await self.redis_client.delete(redis_key)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create reservation: {e}",
            )

    async def cancel_reservation(self, user_id: int, event_id: int, seat_num: str) -> None:
        """
        Cancels a reservation and publishes a message to the Kafka "seat.unlock" topic.
        """
        redis_key = f"seat:{event_id}:{seat_num}"
        lock_value = await self.redis_client.get(redis_key)

        if not lock_value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reservation not found or already released.",
            )
        
        # 권한 체크: 본인의 예약인지 확인
        lock_value_str = str(lock_value)
        if not lock_value_str.startswith(f"{user_id}:"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot cancel other user's reservation.",
            )

        try:
            # Delete the Redis lock
            await self.redis_client.delete(redis_key)

            # Publish seat.unlock event
            await self.event_publisher.publish_seat_unlock(
                event_id=event_id,
                seat_num=seat_num,
                lock_key=lock_value_str
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cancel reservation or publish unlock event: {e}",
            )
