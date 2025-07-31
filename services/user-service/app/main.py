from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db.session import init_db
from app.api.v1.endpoints import users, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(root_path="/api-user", lifespan=lifespan)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])