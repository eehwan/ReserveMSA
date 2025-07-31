from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db.session import init_db
from app.api.v1.endpoints.events import router as events_router
from app.api.v1.endpoints.seats import router as seats_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(root_path="/event", lifespan=lifespan)

app.include_router(events_router, prefix="/events", tags=["events"])
app.include_router(seats_router, prefix="/seats", tags=["seats"])
