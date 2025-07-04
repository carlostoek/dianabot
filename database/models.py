from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
from datetime import datetime

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
    role = Column(String(20), default="free")
    is_vip = Column(Boolean, default=False)
    vip_expires = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Narrative Progress
    narrative_level = Column(Integer, default=1)
    narrative_state = Column(Text, default="{}")  # JSON como texto por compatibilidad
    user_archetype = Column(String(50), nullable=True)
    
    # Economy
    total_spent = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_activity = Column(DateTime, default=func.now())
    last_daily_claim = Column(DateTime, nullable=True)

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    name = Column(String(255), nullable=False)
    role = Column(String(20), default="admin")
    permissions = Column(Text, default="{}")  # JSON como texto
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

class NarrativeState(Base):
    __tablename__ = "narrative_states"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    level = Column(Integer, nullable=False)
    scene = Column(String(100), nullable=False)
    state_data = Column(Text, default="{}")  # JSON como texto
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String(50), nullable=False)  # earn, spend, transfer
    amount = Column(Integer, nullable=False)
    description = Column(String(500))
    reference_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now())

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
    
