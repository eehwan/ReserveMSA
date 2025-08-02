from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.kafka import kafka_producer
from app.core.redis import redis_client
from app.api.v1.endpoints import reservations

@asynccontextmanager
async def lifespan(app: FastAPI):
    await kafka_producer.start()
    yield
    await kafka_producer.stop()
    await redis_client.close()

app = FastAPI(root_path="/api-reservation", lifespan=lifespan)

app.include_router(reservations.router, prefix="/reservations")

@app.get("/health")
def health_check():
    return {"status": "ok"}
