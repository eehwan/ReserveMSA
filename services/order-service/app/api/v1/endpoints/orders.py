from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from aiokafka import AIOKafkaProducer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.schemas.order_schemas import OrderRequest, OrderResponse, OrderStatusResponse
from app.api.v1.schemas.auth_schemas import TokenPayload
from app.services.order_service import OrderService
from app.dependencies.auth import get_token_payload
from app.core.redis import get_redis_client_instance
from app.core.kafka import get_kafka_producer_instance

router = APIRouter()

@router.post("/", response_model=OrderResponse, status_code=201)
async def make_order(
    order_request: OrderRequest,
    payload: TokenPayload = Depends(get_token_payload),
    redis_client: Redis = Depends(get_redis_client_instance),
    kafka_producer: AIOKafkaProducer = Depends(get_kafka_producer_instance),
    db: AsyncSession = Depends(get_db)
):
    order_service = OrderService(redis_client, kafka_producer, db)
    try:
        user_id = int(payload.sub)
        order = await order_service.make_order(
            user_id=user_id,
            event_id=order_request.event_id,
            seat_num=order_request.seat_num,
        )
        return order
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {e}",
        )

@router.delete("/", status_code=200)
async def cancel_order(
    order_request: OrderRequest,
    payload: TokenPayload = Depends(get_token_payload),
    redis_client: Redis = Depends(get_redis_client_instance),
    kafka_producer: AIOKafkaProducer = Depends(get_kafka_producer_instance),
    db: AsyncSession = Depends(get_db)
):
    order_service = OrderService(redis_client, kafka_producer, db)
    try:
        user_id = int(payload.sub)
        await order_service.cancel_order(
            user_id=user_id,
            event_id=order_request.event_id,
            seat_num=order_request.seat_num,
        )
        return {"message": "Order cancelled successfully."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {e}",
        )
