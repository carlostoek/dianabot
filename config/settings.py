import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    # Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///diana.db")
    
    # Channel Configuration
    FREE_CHANNEL_ID: int = int(os.getenv("FREE_CHANNEL_ID", "0"))
    VIP_CHANNEL_ID: int = int(os.getenv("VIP_CHANNEL_ID", "0"))
    
    # Economy Configuration
    INITIAL_BESITOS: int = 100
    DAILY_GIFT_BASE: int = 50
    PURCHASE_CASHBACK_RATE: float = 0.1
    
    # Narrative Configuration
    MAX_NARRATIVE_LEVEL: int = 6
    TRIVIA_REWARD_BASE: int = 25
    
    # Admin Configuration
    SUPER_ADMIN_IDS: list = None
    
    # AI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    def __post_init__(self):
        if self.SUPER_ADMIN_IDS is None:
            admin_ids = os.getenv("SUPER_ADMIN_IDS", "")
            self.SUPER_ADMIN_IDS = [int(id.strip()) for id in admin_ids.split(",") if id.strip()]
