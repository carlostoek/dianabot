import os
from typing import Dict, Any


class Settings:
    """Configuración centralizada del bot"""

    # === DATABASE ===
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://user:pass@localhost/diana_bot"
    )

    # === TELEGRAM ===
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")

    # === REDIS ===
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # === CHANNELS ===
    VIP_CHANNEL_ID = os.getenv("VIP_CHANNEL_ID")  # El Diván
    FREE_CHANNEL_ID = os.getenv("FREE_CHANNEL_ID")  # Los Kinkys

    # === BUSINESS LOGIC ===
    BESITOS_MULTIPLIERS = {"vip": 1.5, "divan": 2.0, "premium": 3.0}

    DAILY_LIMITS = {"missions": 10, "games": 15, "auctions_participation": 5}

    # === SOCIAL MEDIA ===
    SOCIAL_LINKS = {
        "instagram": "https://instagram.com/diana_profile",
        "twitter": "https://twitter.com/diana_profile",
        "tiktok": "https://tiktok.com/@diana_profile",
        "onlyfans": "https://onlyfans.com/diana_profile",
    }

    # === AUTO-APPROVAL ===
    AUTO_APPROVAL_DELAYS = {
        "min_minutes": 15,
        "max_minutes": 180,
        "default_minutes": 30,
    }


settings = Settings()
   