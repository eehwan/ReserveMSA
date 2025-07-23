from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.database import engine
from app.routers import users, auth

app = FastAPI()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
