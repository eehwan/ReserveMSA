from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.schemas import User, UserCreate
from app.services.user_service import UserService
from app.dependencies.auth import get_token_payload
from app.api.v1.schemas import TokenPayload

router = APIRouter()

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    db_user = await user_service.get_user_by_email(email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return await user_service.create_user(user)

@router.get("/me", response_model=User)
async def read_users_me(
    payload: TokenPayload = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    user_id = int(payload.sub)
    db_user = await user_service.get_user_by_id(user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    db_user = await user_service.get_user_by_id(user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user
