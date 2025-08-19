from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    KAFKA_BOOTSTRAP_SERVERS: str
    
    # Mock PG 설정
    MOCK_PG_SUCCESS_RATE: float = 0.95  # 95% 성공률
    MOCK_PG_MIN_DELAY: float = 0.5      # 최소 지연시간 (초)
    MOCK_PG_MAX_DELAY: float = 2.0      # 최대 지연시간 (초)
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@postgreSQL:5432/payment_db"
    
    class Config:
        env_file = ".env"

settings = Settings()