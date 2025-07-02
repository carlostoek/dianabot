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


class AuctionStatus(enum.Enum):
    SCHEDULED = "scheduled"  # Programada para el futuro
    ACTIVE = "active"  # En curso
    ENDED = "ended"  # Terminada
    CANCELLED = "cancelled"  # Cancelada
    PAUSED = "paused"  # Pausada temporalmente


class AuctionType(enum.Enum):
    NORMAL = "normal"  # Subasta normal
    SEALED_BID = "sealed"  # Ofertas selladas
    DUTCH = "dutch"  # Subasta holandesa (precio baja)
    RESERVE = "reserve"  # Con precio de reserva


class AuctionItemCategory(enum.Enum):
    VIP_ACCESS = "vip_access"
    CUSTOM_ROLE = "custom_role"
    EXCLUSIVE_CONTENT = "exclusive_content"
    BESITOS = "besitos"
    LORE_PIECE = "lore_piece"
    CUSTOM_ITEM = "custom_item"


class ItemType(enum.Enum):
    VIDEO = "video"


class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Configuración
    auction_type = Column(Enum(AuctionType), default=AuctionType.NORMAL)
    status = Column(Enum(AuctionStatus), default=AuctionStatus.SCHEDULED)

    # Precios
    starting_price = Column(Integer, nullable=False)  # Precio inicial en besitos
    reserve_price = Column(Integer, nullable=True)  # Precio de reserva
    current_price = Column(Integer, nullable=False)  # Precio actual
    buyout_price = Column(Integer, nullable=True)  # Precio de compra inmediata

    # Configuración de pujas
    min_bid_increment = Column(Integer, default=10)  # Incremento mínimo
    max_bid_increment = Column(Integer, nullable=True)  # Incremento máximo

    # Restricciones
    vip_only = Column(Boolean, default=True)
    min_level_required = Column(Integer, default=1)
    max_participants = Column(Integer, nullable=True)

    # Tiempo
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    auto_extend = Column(
        Boolean, default=True
    )  # Extender si hay puja en últimos minutos
    extension_time = Column(Integer, default=300)  # Segundos de extensión

    # Ganador
    winner_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    winning_bid = Column(Integer, nullable=True)

    # Metadatos
    item_data = Column(JSON)  # Información específica del item
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    bids = relationship(
        "AuctionBid", back_populates="auction", order_by="AuctionBid.amount.desc()"
    )
    winner = relationship("User", foreign_keys=[winner_id])
    creator = relationship("User", foreign_keys=[created_by])
    items = relationship("AuctionItem", back_populates="auction")


class AuctionItem(Base):
    __tablename__ = "auction_items"

    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey('auction.id'), nullable=False)

    item_type = Column(Enum(AuctionItemCategory), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    quantity = Column(Integer, default=1)

    # Datos específicos del item
    item_data = Column(JSON)  # ej: {"vip_days": 30, "role_name": "Collector"}

    # Estado
    is_delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime, nullable=True)

    # Relación
    auction = relationship("Auction", back_populates="items")


class AuctionBid(Base):
    __tablename__ = "auction_bids"

    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey('auction.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    amount = Column(Integer, nullable=False)
    is_auto_bid = Column(Boolean, default=False)  # Si es puja automática
    max_auto_bid = Column(Integer, nullable=True)  # Límite de puja automática

    # Estado
    is_winning = Column(Boolean, default=False)
    is_refunded = Column(Boolean, default=False)

    # Metadatos
    bid_data = Column(JSON)  # Información adicional
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    auction = relationship("Auction", back_populates="bids")
    user = relationship("User", back_populates="auction_bids")


class AuctionWatch(Base):
    __tablename__ = "auction_watches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    auction_id = Column(Integer, ForeignKey('auction.id'), nullable=False)

    notify_on_outbid = Column(Boolean, default=True)
    notify_on_ending = Column(Boolean, default=True)
    notify_minutes_before = Column(Integer, default=30)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    user = relationship("User")
    auction = relationship("Auction")
   

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
    ForeignKey,
)
from sqlalchemy.orm import relationship
from config.database import Base
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class ChannelType(Enum):
    FREE = "free"  # Canal gratuito (Los Kinkys)
    VIP = "vip"  # Canal VIP (El Diván)
    ADMIN = "admin"  # Canal administrativo
    SPECIAL = "special"  # Canales especiales/temporales


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
    PENDING = "pending"  # Solicitud pendiente
    APPROVED = "approved"  # Miembro activo
    REJECTED = "rejected"  # Solicitud rechazada
    BANNED = "banned"  # Usuario baneado
    LEFT = "left"  # Usuario se fue voluntariamente


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(
        BigInteger, unique=True, index=True
    )  # ID del canal en Telegram
    name = Column(String(100), nullable=False)
    description = Column(Text)
    channel_type = Column(SQLEnum(ChannelType), nullable=False)
    status = Column(SQLEnum(ChannelStatus), default=ChannelStatus.ACTIVE)

    # Configuración de acceso
    requires_approval = Column(Boolean, default=True)
    auto_approval_enabled = Column(Boolean, default=False)
    auto_approval_delay_minutes = Column(
        Integer, default=30
    )  # Tiempo para auto-aprobación
    min_narrative_level = Column(String(50))  # Nivel mínimo requerido
    vip_only = Column(Boolean, default=False)

    # Enlaces y tokens
    public_invite_link = Column(String(500))  # Link público para solicitudes
    admin_invite_link = Column(String(500))  # Link admin para bypass

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
    settings = Column(JSON, default=dict)  # Configuraciones específicas
    social_media_links = Column(JSON, default=dict)  # Links a redes sociales

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    memberships = relationship(
        "ChannelMembership",
        back_populates="channel",
        cascade="all, delete-orphan",
        foreign_keys="[ChannelMembership.channel_id]",
    )
    access_tokens = relationship(
        "ChannelAccessToken", back_populates="channel", cascade="all, delete-orphan"
    )


class ChannelMembership(Base):
    __tablename__ = "channel_memberships"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('channel.id'), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    telegram_user_id = Column(BigInteger, nullable=False, index=True)

    status = Column(SQLEnum(MembershipStatus), default=MembershipStatus.PENDING)

    # Información de solicitud
    requested_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime)
    approved_by_user_id = Column(Integer)  # Admin que aprobó
    rejection_reason = Column(Text)

    # Actividad del miembro
    first_message_at = Column(DateTime)
    last_activity_at = Column(DateTime)
    total_messages = Column(Integer, default=0)
    warnings_count = Column(Integer, default=0)

    # Método de ingreso
    joined_via = Column(String(50))  # "manual", "token", "auto_approval", etc.
    access_token_used = Column(String(100))  # Token usado si aplica

    # Datos adicionales
    join_metadata = Column(JSON, default=dict)  # Info del contexto de ingreso

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    channel = relationship("Channel", back_populates="memberships")


class ChannelAccessToken(Base):
    __tablename__ = "channel_access_tokens"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('channel.id'), nullable=False, index=True)
    token = Column(String(100), unique=True, index=True)

    # Configuración del token
    created_by_user_id = Column(Integer, nullable=False)  # Admin que lo creó
    max_uses = Column(Integer, default=1)  # Número máximo de usos
    current_uses = Column(Integer, default=0)
    expires_at = Column(DateTime)

    status = Column(SQLEnum(AccessTokenStatus), default=AccessTokenStatus.ACTIVE)

    # Información adicional
    description = Column(String(200))  # Descripción del propósito
    target_user_name = Column(String(100))  # Si es para usuario específico

    # Uso del token
    used_by_user_ids = Column(JSON, default=list)  # Lista de usuarios que lo usaron
    usage_log = Column(JSON, default=list)  # Log de usos

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    channel = relationship("Channel", back_populates="access_tokens")


class ChannelMessage(Base):
    __tablename__ = "channel_messages"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    telegram_message_id = Column(BigInteger, nullable=False)
    telegram_user_id = Column(BigInteger, nullable=False)

    # Contenido del mensaje
    message_type = Column(String(50), default="text")  # text, photo, video, etc.
    content = Column(Text)
    media_url = Column(String(500))

    # Análisis automático
    is_spam = Column(Boolean, default=False)
    spam_score = Column(Integer, default=0)
    sentiment_score = Column(Integer, default=0)  # -100 a 100
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
    channel_id = Column(Integer, nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)

    # Métricas de membresía
    new_members = Column(Integer, default=0)
    left_members = Column(Integer, default=0)
    banned_members = Column(Integer, default=0)
    total_members_end_day = Column(Integer, default=0)

    # Métricas de actividad
    total_messages = Column(Integer, default=0)
    active_users = Column(Integer, default=0)  # Usuarios que enviaron mensajes
    avg_messages_per_user = Column(Integer, default=0)

    # Métricas de engagement
    reactions_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    media_messages = Column(Integer, default=0)

    # Métricas de moderación
    spam_messages_detected = Column(Integer, default=0)
    messages_deleted = Column(Integer, default=0)
    warnings_issued = Column(Integer, default=0)

    # Métricas de conversión (para canal gratuito)
    users_promoted_to_vip = Column(Integer, default=0)
    purchases_made = Column(Integer, default=0)

    # Datos adicionales
    top_users = Column(JSON, default=list)  # Top usuarios activos del día
    popular_topics = Column(JSON, default=list)  # Temas más mencionados

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Enum,
    Float,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base
import enum


class GameType(enum.Enum):
    TRIVIA = "trivia"
    NUMBER_GUESS = "number_guess"
    WORD_GAME = "word_game"
    MEMORY = "memory"
    MATH = "math"
    RIDDLE = "riddle"
    WORD_ASSOCIATION = "word_association"
    PATTERN_RECOGNITION = "pattern_recognition"
    MORAL_DILEMMA = "moral_dilemma"
    QUICK_CHOICE = "quick_choice"
    MEMORY_CHALLENGE = "memory_challenge"
    CREATIVITY_TEST = "creativity_test"


class DifficultyLevel(enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class GameDifficulty(enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class GameStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)


class TriviaQuestion(Base):
    __tablename__ = "trivia_questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    correct_answer = Column(String(200), nullable=False)
    wrong_answer_1 = Column(String(200), nullable=False)
    wrong_answer_2 = Column(String(200), nullable=False)
    wrong_answer_3 = Column(String(200), nullable=False)

    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM)
    category = Column(String(100), default="General")
    reward_besitos = Column(Integer, default=10)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_admin = Column(Integer, nullable=True)


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    game_type = Column(Enum(GameType))

    # Estado del juego
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    score = Column(Integer, default=0)
    max_score = Column(Integer, default=100)

    # Datos del juego (JSON string)
    game_data = Column(Text)  # Para guardar estado específico del juego

    # Recompensas
    besitos_earned = Column(Integer, default=0)
    lore_piece_earned = Column(Integer, ForeignKey('lorepiece.id'), nullable=True)

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relaciones
    user = relationship("User")


class TriviaAnswer(Base):
    __tablename__ = "trivia_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    question_id = Column(Integer, ForeignKey('triviaquestion.id'))

    selected_answer = Column(String(200))
    is_correct = Column(Boolean)
    time_taken = Column(Float)  # Segundos
    besitos_earned = Column(Integer, default=0)

    answered_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    user = relationship("User")
    question = relationship("TriviaQuestion")
   

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base
import enum
from enum import Enum


class MissionType(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    SPECIAL = "special"
    NARRATIVE = "narrative"


class MissionDifficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3


class MissionStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    description = Column(Text)
    mission_type = Column(SQLEnum(MissionType))

    # Configuración
    reward_besitos = Column(Integer, default=25)
    reward_lore_piece_id = Column(Integer, ForeignKey('lorepiece.id'), nullable=True)
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
    user_id = Column(Integer, ForeignKey('user.id'))
    mission_id = Column(Integer, ForeignKey('mission.id'))

    progress = Column(Integer, default=0)
    target = Column(Integer, default=1)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    # Relaciones
    user = relationship("User", back_populates="missions")
    mission = relationship("Mission", back_populates="user_missions")
   

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from config.database import Base as DBBase

Base = declarative_base()
Base = DBBase


class LorePiece(Base):
    __tablename__ = "lore_pieces"

    id = Column(Integer, primary_key=True, index=True)


class UserLorePiece(Base):
    __tablename__ = "user_lore_pieces"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    lore_piece_id = Column(Integer, ForeignKey('lorepiece.id'))

    user = relationship("User", back_populates="lore_pieces")
    lore_piece = relationship("LorePiece")


class NarrativeProgress(Base):
    __tablename__ = "narrative_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))


class LoreCombination(Base):
    __tablename__ = "lore_combinations"

    id = Column(Integer, primary_key=True, index=True)
    piece_a_id = Column(Integer, ForeignKey('lorepiece.id'))
    piece_b_id = Column(Integer, ForeignKey('lorepiece.id'))
    result_piece_id = Column(Integer, ForeignKey('lorepiece.id'))


from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base
import enum


class NarrativeLevel(enum.Enum):
    NEWCOMER = "newcomer"  # Recién llegado
    LEVEL_1_KINKY = "level_1_kinky"  # Los Kinkys - Inicial
    LEVEL_2_KINKY_DEEP = "level_2_kinky_deep"  # Los Kinkys - Profundización
    LEVEL_3_KINKY_FINAL = "level_3_kinky_final"  # Los Kinkys - Culminación
    LEVEL_4_DIVAN_ENTRY = "level_4_divan_entry"  # El Diván - Entrada
    LEVEL_5_DIVAN_DEEP = "level_5_divan_deep"  # El Diván - Profundización
    LEVEL_6_DIVAN_SUPREME = "level_6_divan_supreme"  # El Diván - Supremo
    INNER_CIRCLE = "inner_circle"  # Círculo Íntimo


class UserArchetype(enum.Enum):
    EXPLORER = "explorer"  # El que busca cada detalle
    DIRECT = "direct"  # Va al grano, conciso
    ROMANTIC = "romantic"  # Respuestas poéticas
    ANALYTICAL = "analytical"  # Reflexivo, intelectual
    PERSISTENT = "persistent"  # No se rinde fácilmente
    PATIENT = "patient"  # Procesa profundamente


class EmotionalResponse(enum.Enum):
    IMMEDIATE = "immediate"  # Reacciona al instante
    REFLECTIVE = "reflective"  # Toma tiempo para pensar
    POSSESSIVE = "possessive"  # Intenta poseer/controlar
    EMPATHETIC = "empathetic"  # Responde con empatía
    ANALYTICAL_RESP = "analytical_response"  # Analiza antes de responder
    RESPECTFUL = "respectful"  # Respeta límites y misterio


class UserNarrativeState(Base):
    __tablename__ = "user_narrative_state"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, unique=True)

    # Estado narrativo actual
    current_level = Column(SQLEnum(NarrativeLevel), default=NarrativeLevel.NEWCOMER)
    current_scene = Column(String(100), nullable=True)  # ej: "scene_2_challenge"

    # Arquetipos y personalización
    primary_archetype = Column(SQLEnum(UserArchetype), nullable=True)
    secondary_archetype = Column(SQLEnum(UserArchetype), nullable=True)
    dominant_emotional_response = Column(SQLEnum(EmotionalResponse), nullable=True)

    # Progreso narrativo
    scenes_completed = Column(JSON, default=list)  # Lista de escenas completadas
    choices_made = Column(JSON, default=dict)  # Decisiones tomadas por el usuario
    diana_interactions = Column(
        Integer, default=0
    )  # Número de interacciones directas con Diana

    # Análisis de comportamiento
    response_patterns = Column(JSON, default=dict)  # Patrones de respuesta del usuario
    engagement_metrics = Column(JSON, default=dict)  # Métricas de engagement
    personality_insights = Column(JSON, default=dict)  # Insights de personalidad

    # Estado de acceso
    has_divan_access = Column(Boolean, default=False)
    divan_unlock_date = Column(DateTime, nullable=True)
    special_recognitions = Column(JSON, default=list)  # Reconocimientos especiales

    # Temporización narrativa
    last_interaction = Column(DateTime, default=datetime.utcnow)
    next_scene_available_at = Column(DateTime, nullable=True)

    # Estado emocional de Diana hacia el usuario
    diana_interest_level = Column(Integer, default=0)  # 0-100
    diana_trust_level = Column(Integer, default=0)  # 0-100
    diana_vulnerability_shown = Column(Integer, default=0)  # 0-100

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación
    user = relationship("User", back_populates="narrative_state")


class NarrativeScene(Base):
    __tablename__ = "narrative_scenes"

    id = Column(Integer, primary_key=True, index=True)

    # Identificación de la escena
    level = Column(SQLEnum(NarrativeLevel), nullable=False)
    scene_key = Column(
        String(100), nullable=False
    )  # ej: "welcome_diana", "lucien_challenge"
    scene_order = Column(Integer, default=1)

    # Contenido base
    title = Column(String(200), nullable=False)
    lucien_dialogue = Column(Text, nullable=True)
    diana_dialogue = Column(Text, nullable=True)
    system_message = Column(Text, nullable=True)

    # Variaciones por arquetipo
    archetype_variations = Column(JSON, default=dict)  # Variaciones por tipo de usuario
    emotional_variations = Column(
        JSON, default=dict
    )  # Variaciones por respuesta emocional

    # Lógica de la escena
    triggers = Column(JSON, default=dict)  # Condiciones para activar la escena
    requirements = Column(JSON, default=dict)  # Requisitos para acceder
    outcomes = Column(JSON, default=dict)  # Posibles resultados

    # Temporización
    min_time_since_last = Column(
        Integer, default=0
    )  # Segundos mínimos desde última escena
    max_time_since_last = Column(Integer, nullable=True)  # Tiempo máximo para activar

    # Metadatos
    is_active = Column(Boolean, default=True)
    created_by = Column(String(100), default="system")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Índices únicos
    __table_args__ = {"extend_existing": True}


class UserSceneCompletion(Base):
    __tablename__ = "user_scene_completions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    scene_id = Column(Integer, ForeignKey('narrativescene.id'), nullable=False)

    # Detalles de la finalización
    choice_made = Column(String(100), nullable=True)  # Elección específica del usuario
    response_time = Column(Integer, nullable=True)  # Tiempo en segundos para responder
    emotional_response = Column(SQLEnum(EmotionalResponse), nullable=True)

    # Resultados
    diana_reaction = Column(String(100), nullable=True)  # Reacción de Diana
    lucien_reaction = Column(String(100), nullable=True)  # Reacción de Lucien
    narrative_impact = Column(JSON, default=dict)  # Impacto en la narrativa

    completed_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    user = relationship("User")
    scene = relationship("NarrativeScene")
   

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base
import enum


class TriggerType(enum.Enum):
    USER_ACTION = "user_action"  # Acción específica del usuario
    TIME_BASED = "time_based"  # Basado en tiempo
    METRIC_THRESHOLD = "metric_threshold"  # Umbral de métricas
    BEHAVIOR_PATTERN = "behavior_pattern"  # Patrón de comportamiento
    COMBINATION = "combination"  # Combinación de condiciones
    SPECIAL_EVENT = "special_event"  # Eventos especiales
    NARRATIVE_MILESTONE = "narrative_milestone"  # Hitos narrativos


class TriggerConditionOperator(enum.Enum):
    EQUALS = "equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    REGEX_MATCH = "regex_match"


class TriggerFrequency(enum.Enum):
    ONCE = "once"  # Solo una vez
    DAILY = "daily"  # Una vez por día
    WEEKLY = "weekly"  # Una vez por semana
    MONTHLY = "monthly"  # Una vez por mes
    UNLIMITED = "unlimited"  # Sin límite
    CONDITIONAL = "conditional"  # Basado en condiciones


class NarrativeTrigger(Base):
    __tablename__ = "narrative_triggers"

    id = Column(Integer, primary_key=True, index=True)

    # Identificación del trigger
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    trigger_key = Column(String(100), nullable=False, unique=True)

    # Tipo y configuración
    trigger_type = Column(SQLEnum(TriggerType), nullable=False)
    frequency = Column(SQLEnum(TriggerFrequency), default=TriggerFrequency.ONCE)
    priority = Column(Integer, default=100)  # Mayor número = mayor prioridad

    # Condiciones para activación
    conditions = Column(JSON, nullable=False)  # Condiciones estructuradas

    # Ejemplo de conditions:
    # {
    #   "user_level": {"operator": "greater_equal", "value": 5},
    #   "besitos": {"operator": "greater_than", "value": 1000},
    #   "missions_completed": {"operator": "equals", "value": 10},
    #   "days_since_last_interaction": {"operator": "greater_than", "value": 3},
    #   "user_responses_contains": {"operator": "contains", "value": ["amor", "corazón"]},
    #   "time_of_day": {"operator": "in_list", "value": ["morning", "evening"]},
    #   "user_archetype": {"operator": "equals", "value": "romantic"}
    # }

    # Restricciones de usuario
    user_filters = Column(JSON, default=dict)  # Filtros adicionales

    # Ejemplo de user_filters:
    # {
    #   "min_level": 1,
    #   "max_level": 50,
    #   "required_archetypes": ["explorer", "romantic"],
    #   "excluded_archetypes": ["possessive"],
    #   "vip_only": false,
    #   "narrative_levels": ["level_1_kinky", "level_2_kinky_deep"]
    # }

    # Acción a ejecutar
    action_type = Column(
        String(100), nullable=False
    )  # scene, message, notification, etc.
    action_config = Column(JSON, nullable=False)

    # Ejemplo de action_config para scene:
    # {
    #   "scene_key": "special_diana_surprise",
    #   "scene_template": "diana_special_message",
    #   "personalization": {
    #     "explorer": "Te he estado observando explorar cada rincón...",
    #     "romantic": "Tu romanticismo ha tocado algo profundo en mí..."
    #   },
    #   "rewards": {
    #     "besitos": 100,
    #     "experience": 50,
    #     "special_recognition": "Diana's Special Attention"
    #   }
    # }

    # Temporización
    delay_seconds = Column(Integer, default=0)  # Retraso antes de ejecutar
    cooldown_seconds = Column(Integer, default=0)  # Tiempo entre ejecuciones

    # Validez temporal
    valid_from = Column(DateTime, nullable=True)  # Válido desde
    valid_until = Column(DateTime, nullable=True)  # Válido hasta

    # Estados
    is_active = Column(Boolean, default=True)
    is_test_mode = Column(Boolean, default=False)  # Para pruebas

    # Metadatos
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Estadísticas
    times_triggered = Column(Integer, default=0)
    last_triggered = Column(DateTime, nullable=True)


class UserTriggerExecution(Base):
    __tablename__ = "user_trigger_executions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    trigger_id = Column(Integer, nullable=False)

    # Detalles de la ejecución
    executed_at = Column(DateTime, default=datetime.utcnow)
    execution_context = Column(JSON, default=dict)  # Contexto cuando se ejecutó

    # Resultados
    success = Column(Boolean, default=True)
    result_data = Column(JSON, default=dict)
    user_response = Column(Text, nullable=True)

    # Para control de frecuencia
    can_repeat_after = Column(DateTime, nullable=True)


class TriggerTemplate(Base):
    __tablename__ = "trigger_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Identificación
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(
        String(100), nullable=False
    )  # engagement, milestone, retention, etc.

    # Template de configuración
    template_config = Column(JSON, nullable=False)

    # Ejemplos predefinidos para facilitar creación
    # {
    #   "name_template": "Usuario completa {X} misiones",
    #   "description_template": "Trigger cuando usuario completa {X} misiones en {Y} días",
    #   "conditions_template": {
    #     "missions_completed": {"operator": "greater_equal", "value": "{X}"},
    #     "days_active": {"operator": "less_equal", "value": "{Y}"}
    #   },
    #   "action_template": {
    #     "scene_key": "congratulations_missions",
    #     "rewards": {"besitos": "{X*10}", "experience": "{X*5}"}
    #   },
    #   "variables": {
    #     "X": {"type": "integer", "min": 1, "max": 100, "default": 5},
    #     "Y": {"type": "integer", "min": 1, "max": 30, "default": 7}
    #   }
    # }

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
   

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
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

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
   

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Enum as SQLEnum,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import relationship
from config.database import Base
from enum import Enum
from datetime import datetime


class ShopItemType(Enum):
    GENERIC = "generic"
    SKIN = "skin"


class ShopRarity(Enum):
    COMMON = "common"


class ShopCategory(Base):
    __tablename__ = "shop_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))


class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey('shopcategory.id'))
    name = Column(String(100))
    price = Column(Integer, default=0)
    item_type = Column(SQLEnum(ShopItemType))
    rarity = Column(SQLEnum(ShopRarity))
    is_active = Column(Boolean, default=True)

    category = relationship("ShopCategory")


class ShopPurchase(Base):
    __tablename__ = "shop_purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    item_id = Column(Integer, ForeignKey('shopitem.id'))
    purchased_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("ShopItem")


from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from models.narrative import UserLorePiece
from models.narrative_state import UserNarrativeState
from models.auction import AuctionBid
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
    narrative_state = relationship("UserNarrativeState", uselist=False, back_populates="user")


class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))

    total_reactions = Column(Integer, default=0)
    missions_completed = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    trivia_correct = Column(Integer, default=0)
    trivia_total = Column(Integer, default=0)
    auctions_won = Column(Integer, default=0)
   

