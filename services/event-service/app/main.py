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
from app.events.handlers import EventHandler
from app.db.session import init_db, get_db

from app.api.v1.endpoints import events

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await start_kafka_producer()

    kafka_producer_instance = await get_kafka_producer_instance()
    
    # Create event handler and topic handlers
    event_handler = EventHandler(kafka_producer_instance, get_db)
    topic_handlers = {
        "seat_lock": event_handler.handle_seat_lock,
        "seat_unlock": event_handler.handle_seat_unlock,
        "seat_sold": event_handler.handle_seat_sold,
        "payment_timeout": event_handler.handle_payment_timeout,
        "payment_verified": event_handler.handle_payment_verified,
    }
    
    await initialize_consumer_manager(topic_handlers)
    await start_kafka_consumers()
    yield
    await stop_kafka_consumers()
    await close_kafka_producer_instance()


app = FastAPI(root_path="/api-event", lifespan=lifespan)

app.include_router(events.router, prefix="/events", tags=["events"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
