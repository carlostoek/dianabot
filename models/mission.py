
    from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base
import enum


class MissionType(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    SPECIAL = "special"
    NARRATIVE = "narrative"


class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    description = Column(Text)
    mission_type = Column(Enum(MissionType))

    # Configuración
    reward_besitos = Column(Integer, default=25)
    reward_lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"), nullable=True)
    required_level = Column(Integer, default=1)
    max_completions = Column(Integer, default=1)

    # Estado
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relaciones
    user_missions = relationship("UserMission", back_populates="mission")


class UserMission(Base):
    __tablename__ = "user_missions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mission_id = Column(Integer, ForeignKey("missions.id"))

    progress = Column(Integer, default=0)
    target = Column(Integer, default=1)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    # Relaciones
    user = relationship("User", back_populates="missions")
    mission = relationship("Mission", back_populates="user_missions")
   