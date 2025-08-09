from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.kafka import (
    start_kafka_producer, 
    close_kafka_producer_instance, 
    get_kafka_producer_instance,
    initialize_consumer_manager,
    start_kafka_consumers,
    stop_kafka_consumers
)
from app.events.handlers import ReservationEventHandler
from app.core.redis import get_redis_client_instance, close_redis_client_instance
from app.api.v1.endpoints import reservations

@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_kafka_producer()

    kafka_producer_instance = await get_kafka_producer_instance()
    redis_client = await get_redis_client_instance()
    
    # Create event handler and topic handlers
    event_handler = ReservationEventHandler(kafka_producer_instance, redis_client)
    topic_handlers = {
        "seat_lock_rollback": event_handler.handle_seat_lock_rollback,
    }
    
    await initialize_consumer_manager(topic_handlers)
    await start_kafka_consumers()
    yield
    await stop_kafka_consumers()
    await close_kafka_producer_instance()

app = FastAPI(root_path="/api-reservation", lifespan=lifespan)

app.include_router(reservations.router, prefix="/reservations")

@app.get("/health")
def health_check():
    return {"status": "ok"}
