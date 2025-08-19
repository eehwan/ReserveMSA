from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from aiokafka import AIOKafkaProducer

from app.db.session import get_db
from app.api.v1.schemas.payment_schemas import (
    PaymentWebhookRequest,
    PaymentWebhookResponse,
    PaymentStatusRequest,
    PaymentStatusResponse
)
from app.services.payment_service import PaymentService
from app.core.kafka import get_kafka_producer_instance

router = APIRouter()

@router.post("/webhook", response_model=PaymentWebhookResponse)
async def payment_webhook(
    request: PaymentWebhookRequest,
    db: AsyncSession = Depends(get_db),
    kafka_producer: AIOKafkaProducer = Depends(get_kafka_producer_instance)
):
    """PG사 Webhook 수신"""
    payment_service = PaymentService(db, kafka_producer)
    try:
        response = await payment_service.handle_webhook(request.dict())
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook data: {e}",
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required field: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {e}",
        )

@router.post("/status", response_model=PaymentStatusResponse)
async def get_payment_status(
    request: PaymentStatusRequest,
    db: AsyncSession = Depends(get_db),
    kafka_producer: AIOKafkaProducer = Depends(get_kafka_producer_instance)
):
    """결제 상태 조회"""
    payment_service = PaymentService(db, kafka_producer)
    try:
        response = await payment_service.get_payment_status(request.payment_key)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status query failed: {e}",
        )