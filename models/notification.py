
    from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Enum,
    JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base
import enum


class NotificationType(enum.Enum):
    LEVEL_UP = "level_up"
    MISSION_COMPLETED = "mission_completed"
    MISSION_AVAILABLE = "mission_available"
    MISSION_EXPIRING = "mission_expiring"
    LORE_UNLOCKED = "lore_unlocked"
    LORE_COMBINATION = "lore_combination"
    NARRATIVE_PROGRESS = "narrative_progress"
    AUCTION_OUTBID = "auction_outbid"
    AUCTION_ENDING = "auction_ending"
    AUCTION_WON = "auction_won"
    VIP_GRANTED = "vip_granted"
    VIP_EXPIRING = "vip_expiring"
    DAILY_GIFT = "daily_gift"
    ACHIEVEMENT = "achievement"
    RANKING_CHANGE = "ranking_change"
    GAME_RECORD = "game_record"
    SYSTEM_MESSAGE = "system_message"
    HUMOR_MESSAGE = "humor_message"
    WELCOME_MESSAGE = "welcome_message"
    REACTION_REWARD = "reaction_reward"


class NotificationPriority(enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    notification_type = Column(Enum(NotificationType), nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL)

    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Datos adicionales para la notificación
    data = Column(JSON)  # Información específica del contexto

    # Estado
    is_sent = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)

    # Configuración de envío
    send_immediately = Column(Boolean, default=True)
    scheduled_for = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)

    # Relación
    user = relationship("User")


class HumorMessage(Base):
    __tablename__ = "humor_messages"

    id = Column(Integer, primary_key=True, index=True)

    category = Column(String(100), nullable=False)  # level_up, mission_complete, etc.
    message_template = Column(Text, nullable=False)

    # Configuración
    is_active = Column(Boolean, default=True)
    weight = Column(Integer, default=1)  # Para probabilidad de selección

    # Restricciones de uso
    min_level = Column(Integer, default=1)
    vip_only = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)

    notification_type = Column(Enum(NotificationType), nullable=False)
    title_template = Column(String(200), nullable=False)
    message_template = Column(Text, nullable=False)

    # Configuración
    is_active = Column(Boolean, default=True)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL)

    created_at = Column(DateTime, default=datetime.utcnow)
   