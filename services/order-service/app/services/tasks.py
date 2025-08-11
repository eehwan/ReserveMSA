from datetime import datetime
import logging

from app.core.celery_app import celery_app
from app.core.kafka import get_kafka_producer_instance
from app.events.publishers import OrderEventPublisher

logger = logging.getLogger(__name__)

@celery_app.task
def release_seat_task(event_id: int, seat_num: str, lock_key: str):
    """
    A Celery task to publish a 'seat.release' event if a seat order expires.
    This task is intended to be called with a countdown.
    """
    try:
        # This part is tricky as kafka_producer is async, and Celery tasks are often sync.
        # We will need to run the async producer's send method in an event loop.
        import asyncio
        async def send_event_async():
            producer = await get_kafka_producer_instance()
            event_publisher = OrderEventPublisher(producer)
            await event_publisher.publish_payment_timeout(
                event_id=event_id,
                seat_num=seat_num,
                lock_key=lock_key
            )
        
        asyncio.run(send_event_async())
        logger.info(f"Published payment.timeout event for seat {seat_num} of event {event_id}")

    except Exception as e:
        logger.error(f"Failed to publish payment.timeout event for seat {seat_num} of event {event_id}: {e}")
        # Optionally, you could retry the task
        raise
