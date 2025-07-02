import os
from dataclasses import dataclass

@dataclass
class Settings:
    bot_token: str = os.getenv('BOT_TOKEN', '')
    database_url: str = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///./bot.db')

settings = Settings()

if not settings.bot_token:
    raise ValueError('BOT_TOKEN environment variable not set')
