from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    FREE = "free"
    VIP = "vip"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class NarrativeLevel(int, Enum):
    KINKYS_1 = 1
    KINKYS_2 = 2
    KINKYS_3 = 3
    DIVAN_4 = 4
    DIVAN_5 = 5
    DIVAN_6 = 6

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=True)
    
    # Gamification
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    besitos = Column(Integer, default=100)
    
    # Status
    role = Column(String(20), default=UserRole.FREE)
    is_vip = Column(Boolean, default=False)
    vip_expires = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Narrative Progress
    narrative_level = Column(Integer, default=1)
    narrative_state = Column(JSON, default=dict)
    user_archetype = Column(String(50), nullable=True)
    
    # Economy
    total_spent = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_activity = Column(DateTime, default=func.now())
    last_daily_claim = Column(DateTime, nullable=True)
    
    # Relationships
    narrative_states = relationship("NarrativeState", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    auction_bids = relationship("AuctionBid", back_populates="user")
    purchases = relationship("Purchase", back_populates="user")

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    name = Column(String(255), nullable=False)
    role = Column(String(20), default="admin")
    permissions = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    user = relationship("User")

class NarrativeState(Base):
    __tablename__ = "narrative_states"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    level = Column(Integer, nullable=False)
    scene = Column(String(100), nullable=False)
    state_data = Column(JSON, default=dict)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    user = relationship("User", back_populates="narrative_states")

class StoreItem(Base):
    __tablename__ = "store_items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price_besitos = Column(Integer, nullable=False)
    category = Column(String(100))
    content_url = Column(String(500), nullable=True)
    content_type = Column(String(50))  # video, image, text, subscription
    is_active = Column(Boolean, default=True)
    stock = Column(Integer, default=-1)  # -1 = unlimited
    created_at = Column(DateTime, default=func.now())

class Auction(Base):
    __tablename__ = "auctions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    starting_price = Column(Integer, nullable=False)
    current_price = Column(Integer, nullable=False)
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    winner = relationship("User")
    bids = relationship("AuctionBid", back_populates="auction")

class AuctionBid(Base):
    __tablename__ = "auction_bids"
    
    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("auctions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    auction = relationship("Auction", back_populates="bids")
    user = relationship("User", back_populates="auction_bids")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String(50), nullable=False)  # earn, spend, transfer
    amount = Column(Integer, nullable=False)
    description = Column(String(500))
    reference_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    user = relationship("User", back_populates="transactions")

class Purchase(Base):
    __tablename__ = "purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("store_items.id"))
    price_paid = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    user = relationship("User", back_populates="purchases")
    item = relationship("StoreItem")

class Badge(Base):
    __tablename__ = "badges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    icon = Column(String(100))
    category = Column(String(100))
    requirements = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

class UserBadge(Base):
    __tablename__ = "user_badges"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    badge_id = Column(Integer, ForeignKey("badges.id"))
    earned_at = Column(DateTime, default=func.now())
    
    user = relationship("User")
    badge = relationship("Badge")

class ChannelPost(Base):
    __tablename__ = "channel_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, nullable=False)
    message_id = Column(Integer, nullable=False)
    content = Column(Text)
    buttons_config = Column(JSON, default=dict)
    reactions_count = Column(JSON, default=dict)
    created_at = Column(DateTime, default=func.now())

