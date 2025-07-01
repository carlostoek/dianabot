from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))

    # Gamificación
    besitos = Column(Integer, default=0)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)

    # Estado
    is_vip = Column(Boolean, default=False)
    vip_expires = Column(DateTime, nullable=True)
    is_banned = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_daily_claim = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    missions = relationship("UserMission", back_populates="user")
    lore_pieces = relationship("UserLorePiece", back_populates="user")
    auction_bids = relationship("AuctionBid", back_populates="user")


class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    total_reactions = Column(Integer, default=0)
    missions_completed = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    trivia_correct = Column(Integer, default=0)
    trivia_total = Column(Integer, default=0)
    auctions_won = Column(Integer, default=0)
   