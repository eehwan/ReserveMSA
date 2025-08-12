from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import User
from app.api.v1.schemas import UserCreate
from app.core import security

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).filter(User.id == user_id))
        db_user = result.scalars().first()
        if not db_user:
            return None
        
        return db_user
        return User(
            id=db_user.id,
            email=db_user.email,
            role=db_user.role
        )

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).filter(User.email == email))
        db_user = result.scalars().first()
        if not db_user:
            return None
        
        return db_user
        # return User(
        #     id=db_user.id,
        #     email=db_user.email,
        #     role=db_user.role
        # )

    async def create_user(self, user: UserCreate) -> User:
        hashed_password = security.get_password_hash(user.password)
        db_user = User(email=user.email, hashed_password=hashed_password)
        self.db.add(db_user)
        await self.db.flush()
        await self.db.refresh(db_user)
        
        return db_user
        return User(
            id=db_user.id,
            email=db_user.email,
            role=db_user.role
        )
