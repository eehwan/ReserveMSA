from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_HOST: str
    REDIS_PORT: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    SEAT_RESERVATION_TIMEOUT: int = 300
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    class Config:
        env_file = ".env"

settings = Settings()