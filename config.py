from dataclasses import dataclass
import os

@dataclass
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/dbname")

settings = Settings()
if not settings.bot_token:
    raise ValueError("BOT_TOKEN not set")
