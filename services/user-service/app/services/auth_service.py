from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import UserRepository
from app.api.v1.schemas import UserLogin, Token
from app.core import security
from app.core.config import settings

class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def authenticate_user(self, user_credentials: UserLogin) -> Token | None:
        user = await self.user_repo.get_user_by_email(email=user_credentials.email)
        if not user or not security.verify_password(user_credentials.password, user.hashed_password):
            return None
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
