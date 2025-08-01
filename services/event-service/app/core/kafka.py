# event-service/app/core/kafka.py
import asyncio
import logging
from shared.kafka.consumer import KafkaConsumerWorker
from shared.kafka.topics import (
    TOPICS,
    SeatReservedEvent,
    ReservationConfirmedEvent,
    PaymentCompletedEvent,
)
from shared.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -- Kafka Event Handlers ----------------------------------------------------

async def handle_seat_reserved(event: SeatReservedEvent):
    logger.info(f"[Seat Reserved] Reservation: {event.reservation_id}, Seat: {event.seat_id}, User: {event.user_id}")
    # TODO: Implement logic to change seat status to 'allocated'

async def handle_reservation_confirmed(event: ReservationConfirmedEvent):
    logger.info(f"[Reservation Confirmed] Reservation: {event.reservation_id}")
    # TODO: Implement logic to change seat status to 'sold'

async def handle_payment_completed(event: PaymentCompletedEvent):
    logger.info(f"[Payment Completed] Reservation: {event.reservation_id}, Payment: {event.payment_id}")
    # TODO: Implement logic to change seat status to 'sold' (idempotently)

# -- Consumer Setup ----------------------------------------------------------

CONSUMER_CONFIGS = [
    {
        "topic_key": "seat_reserved",
        "handler": handle_seat_reserved,
    },
    {
        "topic_key": "reservation_confirmed",
        "handler": handle_reservation_confirmed,
    },
    {
        "topic_key": "payment_completed",
        "handler": handle_payment_completed,
    },
]

consumer_tasks = []

async def start_kafka_consumers():
    bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
    group_id = "event-service-group"

    for config in CONSUMER_CONFIGS:
        topic_info = TOPICS[config["topic_key"]]
        worker = KafkaConsumerWorker(
            topic=topic_info["topic"],
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            event_model=topic_info["schema"],
            handler=config["handler"],
        )
        task = asyncio.create_task(worker.start())
        consumer_tasks.append(task)
    logger.info(f"Started {len(consumer_tasks)} Kafka consumer workers.")

async def stop_kafka_consumers():
    for task in consumer_tasks:
        task.cancel()
    await asyncio.gather(*consumer_tasks, return_exceptions=True)
    logger.info("All Kafka consumer workers stopped.")