from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_URL: str = "postgresql+asyncpg://postgres:postgres@db:5434/authdb"
    SECRET_KEY: str = "davihbv5w48ovqi3yboq38"
    ALGORITHM: str = "HS256"
    ACCESS_EXPIRE_MINUTES: int = 15
    REFRESH_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"

settings = Settings()
