from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    REDIS_HOST: str
    REDIS_PORT: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    SEAT_ORDER_TIMEOUT: int = 300
    KAFKA_BOOTSTRAP_SERVERS: str
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@postgreSQL:5432/order_db"
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    class Config:
        env_file = ".env"

settings = Settings()