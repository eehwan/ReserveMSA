from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    KAFKA_BOOTSTRAP_SERVERS: str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@postgreSQL:5432/event_db"

    class Config:
        env_file = ".env"

settings = Settings()
