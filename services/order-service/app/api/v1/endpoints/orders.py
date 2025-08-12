from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from aiokafka import AIOKafkaProducer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories import OrderRepository
from app.api.v1.schemas.order_schemas import OrderRequest, OrderResponse
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

@router.get("/", response_model=list[OrderResponse])
async def get_user_orders(
    payload: TokenPayload = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db)
):
    """사용자의 주문 목록 조회"""
    try:
        user_id = int(payload.sub)
        order_repo = OrderRepository(db)
        orders = await order_repo.get_orders_by_user(user_id)
        
        return [
            OrderResponse(
                order_id=order.order_id,
                status=order.status.value,
                event_id=order.event_id,
                seat_num=order.seat_num,
                expires_at=order.expires_at
            )
            for order in orders
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch orders: {e}",
        )
