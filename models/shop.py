from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from config.database import Base
import enum
from datetime import datetime


class ShopItemType(enum.Enum):
    GENERIC = "generic"


class ShopRarity(enum.Enum):
    COMMON = "common"


class ShopCategory(Base):
    __tablename__ = "shop_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))


class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("shop_categories.id"))
    name = Column(String(100))
    price = Column(Integer, default=0)
    item_type = Column(Enum(ShopItemType))
    rarity = Column(Enum(ShopRarity))
    is_active = Column(Boolean, default=True)

    category = relationship("ShopCategory")


class ShopPurchase(Base):
    __tablename__ = "shop_purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("shop_items.id"))
    purchased_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("ShopItem")
