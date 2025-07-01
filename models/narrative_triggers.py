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
   