from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    JSON,
    BigInteger,
    Enum as SQLEnum,
    ForeignKey,  # ← AGREGADO
)
from sqlalchemy.orm import relationship
from config.database import Base
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class ChannelType(Enum):
    FREE = "free"
    VIP = "vip"
    ADMIN = "admin"
    SPECIAL = "special"


class ChannelStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class AccessTokenStatus(Enum):
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    REVOKED = "revoked"


class MembershipStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    BANNED = "banned"
    LEFT = "left"


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    channel_type = Column(SQLEnum(ChannelType), nullable=False)
    status = Column(SQLEnum(ChannelStatus), default=ChannelStatus.ACTIVE)

    # Configuración de acceso
    requires_approval = Column(Boolean, default=True)
    auto_approval_enabled = Column(Boolean, default=False)
    auto_approval_delay_minutes = Column(Integer, default=30)
    min_narrative_level = Column(String(50))
    vip_only = Column(Boolean, default=False)

    # Enlaces y tokens
    public_invite_link = Column(String(500))
    admin_invite_link = Column(String(500))

    # Configuración de moderación
    welcome_message = Column(Text)
    rules_message = Column(Text)
    auto_moderation_enabled = Column(Boolean, default=True)
    spam_detection_enabled = Column(Boolean, default=True)

    # Métricas
    total_members = Column(Integer, default=0)
    pending_requests = Column(Integer, default=0)
    daily_messages = Column(Integer, default=0)

    # Configuración adicional
    settings = Column(JSON, default=dict)
    social_media_links = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones ARREGLADAS
    memberships = relationship(
        "ChannelMembership", 
        back_populates="channel", 
        cascade="all, delete-orphan"
    )
    access_tokens = relationship(
        "ChannelAccessToken", 
        back_populates="channel", 
        cascade="all, delete-orphan"
    )


class ChannelMembership(Base):
    __tablename__ = "channel_memberships"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False, index=True)  # ← ARREGLADO
    user_id = Column(Integer, nullable=False, index=True)  # Asumiendo que User existe
    telegram_user_id = Column(BigInteger, nullable=False, index=True)

    status = Column(SQLEnum(MembershipStatus), default=MembershipStatus.PENDING)

    # Información de solicitud
    requested_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime)
    approved_by_user_id = Column(Integer)
    rejection_reason = Column(Text)

    # Actividad del miembro
    first_message_at = Column(DateTime)
    last_activity_at = Column(DateTime)
    total_messages = Column(Integer, default=0)
    warnings_count = Column(Integer, default=0)

    # Método de ingreso
    joined_via = Column(String(50))
    access_token_used = Column(String(100))

    # Datos adicionales
    join_metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones ARREGLADAS
    channel = relationship("Channel", back_populates="memberships")


class ChannelAccessToken(Base):
    __tablename__ = "channel_access_tokens"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False, index=True)  # ← ARREGLADO
    token = Column(String(100), unique=True, index=True)

    # Configuración del token
    created_by_user_id = Column(Integer, nullable=False)
    max_uses = Column(Integer, default=1)
    current_uses = Column(Integer, default=0)
    expires_at = Column(DateTime)

    status = Column(SQLEnum(AccessTokenStatus), default=AccessTokenStatus.ACTIVE)

    # Información adicional
    description = Column(String(200))
    target_user_name = Column(String(100))

    # Uso del token
    used_by_user_ids = Column(JSON, default=list)
    usage_log = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones ARREGLADAS
    channel = relationship("Channel", back_populates="access_tokens")


# Resto de clases sin cambios...
class ChannelMessage(Base):
    __tablename__ = "channel_messages"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False, index=True)  # ← ARREGLADO
    user_id = Column(Integer, nullable=False, index=True)
    telegram_message_id = Column(BigInteger, nullable=False)
    telegram_user_id = Column(BigInteger, nullable=False)

    # Contenido del mensaje
    message_type = Column(String(50), default="text")
    content = Column(Text)
    media_url = Column(String(500))

    # Análisis automático
    is_spam = Column(Boolean, default=False)
    spam_score = Column(Integer, default=0)
    sentiment_score = Column(Integer, default=0)
    engagement_score = Column(Integer, default=0)

    # Moderación
    is_flagged = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    moderation_action = Column(String(50))
    moderation_reason = Column(String(200))

    # Análisis de contenido
    contains_links = Column(Boolean, default=False)
    contains_media = Column(Boolean, default=False)
    word_count = Column(Integer, default=0)

    # Metadata
    message_metadata = Column(JSON, default=dict)

    # Timestamps
    sent_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChannelAnalytics(Base):
    __tablename__ = "channel_analytics"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False, index=True)  # ← ARREGLADO
    date = Column(DateTime, nullable=False, index=True)

    # Métricas de membresía
    new_members = Column(Integer, default=0)
    left_members = Column(Integer, default=0)
    banned_members = Column(Integer, default=0)
    total_members_end_day = Column(Integer, default=0)

    # Métricas de actividad
    total_messages = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    avg_messages_per_user = Column(Integer, default=0)

    # Métricas de engagement
    reactions_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    media_messages = Column(Integer, default=0)

    # Métricas de moderación
    spam_messages_detected = Column(Integer, default=0)
    messages_deleted = Column(Integer, default=0)
    warnings_issued = Column(Integer, default=0)

    # Métricas de conversión
    users_promoted_to_vip = Column(Integer, default=0)
    purchases_made = Column(Integer, default=0)

    # Datos adicionales
    top_users = Column(JSON, default=list)
    popular_topics = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
