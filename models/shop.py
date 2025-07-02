from enum import Enum
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, ForeignKey
from config.database import Base


class ShopItemType(Enum):
    SKIN = "skin"
    POWERUP = "powerup"


class ShopRarity(Enum):
    COMMON = "common"
    EPIC = "epic"


class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    item_type = Column(SQLEnum(ShopItemType))
    rarity = Column(SQLEnum(ShopRarity))
