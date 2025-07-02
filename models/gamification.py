from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from database_init import Base


class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True)
    mission_type = Column(String(50), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(String(255))
    reward_besitos = Column(Integer, default=0)
    reward_lore = Column(Integer, default=0)


class UserMission(Base):
    __tablename__ = "user_missions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    progress = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    claimed = Column(Boolean, default=False)

    user = relationship("User")
    mission = relationship("Mission")


class DailyGift(Base):
    __tablename__ = "daily_gifts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    claimed_at = Column(DateTime, default=datetime.utcnow)
    besitos_reward = Column(Integer, default=0)
    lore_reward = Column(Integer, default=0)

    user = relationship("User")
