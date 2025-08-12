from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories import UserRepository
from app.api.v1.schemas import UserCreate, User

class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        try:
            user = await self.user_repo.create_user(user_data)
            await self.db.commit()
            return user
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.user_repo.get_user_by_id(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.user_repo.get_user_by_email(email)
