from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories import UserRepository
from app.api.v1.schemas import UserCreate, User

class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def create_user(self, user_data: UserCreate) -> User:
        return await self.user_repo.create_user(user_data)

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.user_repo.get_user_by_id(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.user_repo.get_user_by_email(email)
