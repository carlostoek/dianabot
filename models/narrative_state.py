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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scene_id = Column(Integer, ForeignKey("narrative_scenes.id"), nullable=False)

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
   