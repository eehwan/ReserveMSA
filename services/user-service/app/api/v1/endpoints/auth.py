from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.schemas.auth_schemas import UserLogin, Token
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/", response_model=Token)
async def login_for_access_token(
    user_credentials: UserLogin, db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    token = await auth_service.authenticate_user(user_credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token
