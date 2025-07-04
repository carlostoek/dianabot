import os
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Settings:
    # Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Database Configuration - Usar SQLite por defecto
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///diana.db")
    
    # Channel Configuration
    FREE_CHANNEL_ID: int = int(os.getenv("FREE_CHANNEL_ID", "0"))
    VIP_CHANNEL_ID: int = int(os.getenv("VIP_CHANNEL_ID", "0"))
    
    # Economy Configuration
    INITIAL_BESITOS: int = int(os.getenv("INITIAL_BESITOS", "100"))
    DAILY_GIFT_BASE: int = int(os.getenv("DAILY_GIFT_BASE", "50"))
    PURCHASE_CASHBACK_RATE: float = float(os.getenv("PURCHASE_CASHBACK_RATE", "0.1"))
    
    # Narrative Configuration
    MAX_NARRATIVE_LEVEL: int = int(os.getenv("MAX_NARRATIVE_LEVEL", "6"))
    TRIVIA_REWARD_BASE: int = int(os.getenv("TRIVIA_REWARD_BASE", "25"))
    
    # Admin Configuration
    SUPER_ADMIN_IDS: List[int] = None
    
    # AI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    def __post_init__(self):
        if self.SUPER_ADMIN_IDS is None:
            admin_ids = os.getenv("SUPER_ADMIN_IDS", "")
            if admin_ids:
                self.SUPER_ADMIN_IDS = [int(id.strip()) for id in admin_ids.split(",") if id.strip()]
            else:
                self.SUPER_ADMIN_IDS = []
        
        # Validar BOT_TOKEN
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN es requerido")
            
