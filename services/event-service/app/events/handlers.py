import logging
from datetime import datetime
from typing import Callable, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession

from shared.kafka.producer import KafkaProducer
from shared.kafka.topics import (
    TOPICS,
    SeatLockEvent,
    SeatUnlockEvent,
    SeatSoldEvent,
    PaymentTimeoutEvent,
    PaymentRequestedEvent,
    PaymentVerifiedEvent,
    SeatLockRollbackEvent,
)

from app.services.seat_service import SeatService
from app.events.publishers import EventServicePublisher

logger = logging.getLogger(__name__)

class EventHandler:
    def __init__(
        self,
        kafka_producer: KafkaProducer,
        db_session_factory: Callable[[], Awaitable[AsyncSession]],
    ):
        self.db_session_factory = db_session_factory
        self.event_publisher = EventServicePublisher(kafka_producer)

    async def handle_seat_lock(self, event: SeatLockEvent):
        logger.info(f"[Seat Lock] Event: {event.event_id}, Seat: {event.seat_num}, User: {event.user_id}")
        async for db_session in self.db_session_factory():
            seat_service = SeatService(db_session)
            try:
                # DB 상태를 ALLOCATED로 변경 시도
                success = await seat_service.allocate_seat(
                    event.event_id, event.seat_num, event.user_id, event.lock_key
                )

                if success:
                    # 성공 시 payment.requested 발행
                    await self.event_publisher.publish_payment_requested(
                        user_id=event.user_id,
                        event_id=event.event_id,
                        seat_num=event.seat_num,
                        amount=100.0,  # TODO: 실제 가격은 DB에서 가져오도록 수정
                        lock_key=event.lock_key
                    )
                    logger.info(f"Published payment.requested for seat {event.seat_num}")
                else:
                    # 실패 시 seat.lock-rollback 발행 (예: 이미 할당된 좌석)
                    await self.event_publisher.publish_seat_lock_rollback(
                        event_id=event.event_id,
                        seat_num=event.seat_num,
                        lock_key=event.lock_key,
                        reason="seat_already_allocated"
                    )
                    logger.warning(f"Seat {event.seat_num} already allocated, publishing seat.lock-rollback.")

            except Exception as e:
                # DB 업데이트 중 예외 발생 시 seat.lock-rollback 발행
                logger.error(f"Failed to allocate seat {event.seat_num}: {e}")
                await self.event_publisher.publish_seat_lock_rollback(
                    event_id=event.event_id,
                    seat_num=event.seat_num,
                    lock_key=event.lock_key,
                    reason=f"db_update_failed: {e}"
                )

    async def handle_seat_unlock(self, event: SeatUnlockEvent):
        logger.info(f"[Seat Unlock] Event: {event.event_id}, Seat: {event.seat_num}, Lock Key: {event.lock_key}")
        async for db_session in self.db_session_factory():
            seat_service = SeatService(db_session)
            # DB 상태를 ALLOCATED → AVAILABLE로 변경
            await seat_service.release_seat(event.event_id, event.seat_num, event.lock_key)

    async def handle_seat_sold(self, event: SeatSoldEvent):
        logger.info(f"[Seat Sold] Event: {event.event_id}, Seat: {event.seat_num}, Payment: {event.payment_id}")
        async for db_session in self.db_session_factory():
            seat_service = SeatService(db_session)
            # DB 상태를 SOLD로 변경
            await seat_service.sell_seat(event.event_id, event.seat_num, event.payment_id)

    async def handle_payment_timeout(self, event: PaymentTimeoutEvent):
        logger.info(f"[Payment Timeout] Event: {event.event_id}, Seat: {event.seat_num}")
        async for db_session in self.db_session_factory():
            seat_service = SeatService(db_session)
            # DB 상태를 ALLOCATED → AVAILABLE로 변경
            await seat_service.release_seat(event.event_id, event.seat_num, event.lock_key)

    async def handle_payment_verified(self, event: PaymentVerifiedEvent):
        """결제 완료 이벤트 처리 - 좌석 상태를 SOLD로 변경"""
        logger.info(f"[Payment Verified] Event: {event.event_id}, Seat: {event.seat_num}, Order: {event.order_id}")
        
        try:
            async for db_session in self.db_session_factory():
                seat_service = SeatService(db_session)
                # 좌석 상태를 ALLOCATED → SOLD로 변경
                await seat_service.sell_seat(event.event_id, event.seat_num, event.payment_key)
                logger.info(f"Seat {event.seat_num} marked as SOLD for payment {event.payment_key}")
                
        except Exception as e:
            logger.error(f"Failed to mark seat as sold for order {event.order_id}: {e}")
            # TODO: 실패 시 보상 패턴 추가 (payment.cancel 이벤트 발행)