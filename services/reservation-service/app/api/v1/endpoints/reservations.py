from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from aiokafka import AIOKafkaProducer

from app.api.v1.schemas.reservation_schemas import ReservationRequest
from app.services.reservation_service import ReservationService
from app.dependencies.auth import get_token_payload
from app.api.v1.schemas.auth_schemas import TokenPayload
from app.core.redis import get_redis_client_instance
from app.core.kafka import get_kafka_producer_instance

router = APIRouter()

@router.post("/", status_code=202)
async def reserve_seat(
    reservation_request: ReservationRequest,
    payload: TokenPayload = Depends(get_token_payload),
    redis_client: Redis = Depends(get_redis_client_instance), # Inject Redis client
    kafka_producer: AIOKafkaProducer = Depends(get_kafka_producer_instance) # Inject Kafka Producer
):
    reservation_service = ReservationService(redis_client, kafka_producer) # Instantiate with injected clients
    try:
        user_id = int(payload.sub)
        await reservation_service.reserve_seat(
            user_id=user_id,
            event_id=reservation_request.event_id,
            seat_num=reservation_request.seat_num,
        )
        return {"message": "Reservation request accepted and being processed."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {e}",
        )

@router.delete("/", status_code=200)
async def cancel_reservation(
    reservation_request: ReservationRequest,
    payload: TokenPayload = Depends(get_token_payload),
    redis_client: Redis = Depends(get_redis_client_instance),
    kafka_producer: AIOKafkaProducer = Depends(get_kafka_producer_instance)
):
    reservation_service = ReservationService(redis_client, kafka_producer)
    try:
        user_id = int(payload.sub)
        await reservation_service.cancel_reservation(
            user_id=user_id,
            event_id=reservation_request.event_id,
            seat_num=reservation_request.seat_num,
        )
        return {"message": "Reservation cancelled successfully."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {e}",
        )
