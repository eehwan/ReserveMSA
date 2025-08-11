import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi import status
from jose import jwt
from datetime import datetime, timedelta

from app.core.config import settings

# Helper to create a valid JWT for tests
def create_test_token(user_id: int = 1, role: str = "user") -> str:
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@pytest.mark.asyncio
@patch("app.services.order_service.release_seat_task.apply_async")
@patch("app.services.order_service.kafka_producer.send")
@patch("app.services.order_service.redis_client")
async def test_make_order_success(
    mock_redis_client: AsyncMock,
    mock_kafka_send: MagicMock,
    mock_celery_apply_async: MagicMock,
    client
):
    """
    Test successful seat order.
    """
    # Configure mock Redis client to simulate successful SETNX
    mock_redis_client.set.return_value = True  # SETNX returns True on success
    mock_redis_client.delete.return_value = None # delete returns None

    token = create_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"event_id": 1, "seat_num": "A1"}
    redis_key = f"seat:{payload['event_id']}:{payload['seat_num']}"

    response = await client.post("/api-order/orders/", json=payload, headers=headers)

    # 1. Check API response
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"message": "Order request accepted and being processed."}

    # 2. Check if Redis set was called
    mock_redis_client.set.assert_called_once_with(
        redis_key, 
        mock_redis_client.set.call_args.args[1], # dynamic lock_value
        nx=True, 
        ex=settings.SEAT_ORDER_TIMEOUT
    )

    # 3. Check if Kafka event was sent
    mock_kafka_send.assert_called_once()

    # 4. Check if Celery task was scheduled
    mock_celery_apply_async.assert_called_once()
    assert mock_celery_apply_async.call_args.kwargs["countdown"] == settings.SEAT_ORDER_TIMEOUT + 10


@pytest.mark.asyncio
@patch("app.services.order_service.kafka_producer.send")
@patch("app.services.order_service.redis_client")
async def test_make_order_already_reserved(
    mock_redis_client: AsyncMock,
    mock_kafka_send: MagicMock,
    client
):
    """
    Test attempting to reserve a seat that is already locked.
    """
    # Configure mock Redis client to simulate failed SETNX
    mock_redis_client.set.return_value = False # SETNX returns False on failure

    token = create_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"event_id": 2, "seat_num": "B2"}
    redis_key = f"seat:{payload['event_id']}:{payload['seat_num']}"

    response = await client.post("/api-order/orders/", json=payload, headers=headers)

    # 1. Check API response for conflict
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Seat already reserved."

    # 2. Check that Redis set was called
    mock_redis_client.set.assert_called_once_with(
        redis_key, 
        mock_redis_client.set.call_args.args[1], # dynamic lock_value
        nx=True, 
        ex=settings.SEAT_ORDER_TIMEOUT
    )

    # 3. Check that the failure event was sent to Kafka
    mock_kafka_send.assert_called_once()


@pytest.mark.asyncio
async def test_make_order_no_auth(client):
    """
    Test that the endpoint requires authentication.
    """
    payload = {"event_id": 3, "seat_num": "C3"}
    response = await client.post("/api-order/orders/", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED