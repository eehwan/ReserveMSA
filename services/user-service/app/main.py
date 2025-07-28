from fastapi import FastAPI

from app.db.session import init_db
from app.api.v1.endpoints import users, auth

app = FastAPI(root_path="/user")

@app.on_event("startup")
async def startup():
    await init_db()

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])