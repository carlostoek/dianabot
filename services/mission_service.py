from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from models.mission import Mission, MissionType, MissionDifficulty, MissionStatus
from models.user import User
from models.narrative_state import UserNarrativeState, NarrativeLevel, UserArchetype
from config.database import get_db
from utils.lucien_voice import LucienVoice
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import random
import json


class MissionService:
    """Servicio para gestión inteligente de misiones narrativas"""

    def __init__(self):
        self.db = next(get_db())
        self.lucien = LucienVoice()

        # Templates de misiones por tipo y nivel narrativo
        self.mission_templates = self._load_mission_templates()

    # ===== GESTIÓN DE MISIONES =====

    def get_all_users(self) -> List[User]:
        """Devuelve la lista completa de usuarios."""

        return self.db.query(User).all()

    def get_user_missions(
        self, user_id: int, status: Optional[MissionStatus] = None
    ) -> List[Mission]:
        """Obtiene misiones del usuario"""

        query = self.db.query(Mission).filter(Mission.user_id == user_id)

        if status:
            query = query.filter(Mission.status == status)

        return query.order_by(desc(Mission.created_at)).all()

    def get_active_missions(self, user_id: int) -> List[Mission]:
        """Obtiene misiones activas del usuario"""

        return (
            self.db.query(Mission)
            .filter(
                and_(
                    Mission.user_id == user_id,
                    Mission.status == MissionStatus.ACTIVE,
                    or_(
                        Mission.expires_at.is_(None),
                        Mission.expires_at > datetime.utcnow(),
                    ),
                )
            )
            .order_by(Mission.priority.desc(), Mission.created_at)
            .all()
        )

    def create_mission(self, user_id: int, mission_data: Dict[str, Any]) -> Mission:
        """Crea una nueva misión"""

        mission = Mission(
            user_id=user_id,
            title=mission_data["title"],
            description=mission_data["description"],
            mission_type=mission_data["type"],
            difficulty=mission_data.get("difficulty", MissionDifficulty.MEDIUM),
            objectives=mission_data["objectives"],
            rewards=mission_data.get("rewards", {}),
            requirements=mission_data.get("requirements", {}),
            metadata=mission_data.get("metadata", {}),
            expires_at=mission_data.get("expires_at"),
            priority=mission_data.get("priority", 100),
            auto_check=mission_data.get("auto_check", True),
            narrative_context=mission_data.get("narrative_context", {}),
        )

        self.db.add(mission)
        self.db.commit()
        self.db.refresh(mission)

        return mission

    def assign_daily_missions(self, user_id: int) -> List[Mission]:
        """Asigna misiones diarias personalizadas al usuario"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        # Verificar si ya tiene misiones diarias hoy
        today = datetime.utcnow().date()
        existing_daily = (
            self.db.query(Mission)
            .filter(
                and_(
                    Mission.user_id == user_id,
                    Mission.mission_type == MissionType.DAILY,
                    func.date(Mission.created_at) == today,
                    Mission.status.in_([MissionStatus.ACTIVE, MissionStatus.COMPLETED]),
                )
            )
            .first()
        )

        if existing_daily:
            return self.get_user_missions(user_id, MissionStatus.ACTIVE)

        # Obtener estado narrativo para personalización
        from services.user_service import UserService

        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(user_id)

        # Generar misiones diarias personalizadas
        daily_missions = self._generate_daily_missions(user, narrative_state)

        created_missions = []
        for mission_data in daily_missions:
            mission = self.create_mission(user_id, mission_data)
            created_missions.append(mission)

        return created_missions

    def create_daily_missions_for_user(self, user_id: int) -> List[Mission]:
        """Alias para asignar misiones diarias a un usuario"""

        return self.assign_daily_missions(user_id)

    def generate_personalized_missions(self, user_id: int) -> List[Dict[str, Any]]:
        """Genera misiones personalizadas para el usuario (dummy)."""

        # Placeholder: Devuelve lista vacía
        return []

    def check_mission_completion(
        self, mission_id: int, user_action: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Verifica si una misión se ha completado"""

        mission = self.db.query(Mission).filter(Mission.id == mission_id).first()
        if not mission or mission.status != MissionStatus.ACTIVE:
            return {"error": "Misión no encontrada o no activa"}

        # Verificar expiración
        if mission.expires_at and datetime.utcnow() > mission.expires_at:
            return self._handle_mission_expiry(mission)

        # Evaluar objetivos
        completion_result = self._evaluate_mission_objectives(mission, user_action)

        if completion_result["completed"]:
            return self._complete_mission(mission, completion_result)
        else:
            return self._update_mission_progress(mission, completion_result)

    def complete_mission_manually(
        self, mission_id: int, admin_user: str = "system"
    ) -> Dict[str, Any]:
        """Completa una misión manualmente (para admins)"""

        mission = self.db.query(Mission).filter(Mission.id == mission_id).first()
        if not mission:
            return {"error": "Misión no encontrada"}

        if mission.status == MissionStatus.COMPLETED:
            return {"error": "Misión ya completada"}

        completion_result = {
            "completed": True,
            "manual_completion": True,
            "completed_by": admin_user,
        }
        return self._complete_mission(mission, completion_result)

    def cancel_mission(
        self, mission_id: int, reason: str = "Cancelada"
    ) -> Dict[str, Any]:
        """Cancela una misión activa"""

        mission = self.db.query(Mission).filter(Mission.id == mission_id).first()
        if not mission:
            return {"error": "Misión no encontrada"}

        if mission.status not in [MissionStatus.ACTIVE, MissionStatus.PAUSED]:
            return {"error": "No se puede cancelar una misión en este estado"}

        mission.status = MissionStatus.CANCELLED
        mission.completed_at = datetime.utcnow()
        mission.completion_notes = reason

        self.db.commit()

        return {
            "success": True,
            "mission_id": mission_id,
            "message": self._generate_cancellation_message(mission, reason),
        }

    # ===== MISIONES NARRATIVAS ESPECIALES =====

    def create_narrative_mission(
        self, user_id: int, narrative_trigger: str, context: Dict[str, Any] = None
    ) -> Optional[Mission]:
        """Crea misión basada en trigger narrativo"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        from services.user_service import UserService

        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(user_id)

        # Seleccionar template de misión narrativa
        mission_template = self._get_narrative_mission_template(
            narrative_trigger,
            narrative_state.current_level,
            narrative_state.primary_archetype,
            context or {},
        )

        if not mission_template:
            return None

        # Personalizar misión según arquetipo
        personalized_mission = self._personalize_mission_for_archetype(
            mission_template, narrative_state.primary_archetype, user
        )

        # Añadir contexto narrativo
        personalized_mission["narrative_context"] = {
            "trigger": narrative_trigger,
            "user_level": narrative_state.current_level.value,
            "diana_interest": narrative_state.diana_interest_level,
            "diana_trust": narrative_state.diana_trust_level,
            "created_from": "narrative_trigger",
        }

        mission = self.create_mission(user_id, personalized_mission)

        return mission

    def create_diana_special_mission(
        self, user_id: int, diana_mood: str, special_context: Dict[str, Any]
    ) -> Optional[Mission]:
        """Crea misión especial de Diana"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        from services.user_service import UserService

        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(user_id)

        # Misiones especiales de Diana según su mood
        diana_missions = {
            "curious": {
                "title": "Curiosidad de Diana",
                "description": "Diana está intrigada por algo específico sobre ti. Demuestra tu verdadera naturaleza.",
                "objectives": {
                    "interact_authentically": {
                        "type": "response_quality",
                        "target": 1,
                        "description": "Responde a Diana con autenticidad absoluta",
                    }
                },
                "rewards": {"besitos": 150, "experience": 75, "diana_trust": 10},
            },
            "playful": {
                "title": "Juego de Diana",
                "description": "Diana está de humor juguetón y quiere ver tu lado más espontáneo.",
                "objectives": {
                    "play_games": {
                        "type": "activity_count",
                        "target": 3,
                        "activity": "games",
                        "description": "Juega 3 juegos mientras Diana observa",
                    }
                },
                "rewards": {"besitos": 100, "experience": 50, "diana_interest": 15},
            },
            "testing": {
                "title": "Prueba de Diana",
                "description": "Diana quiere poner a prueba tu dedicación hacia ella.",
                "objectives": {
                    "dedication_test": {
                        "type": "consistency",
                        "target": 24,  # 24 horas
                        "description": "Mantén actividad consistente durante 24 horas",
                    }
                },
                "rewards": {
                    "besitos": 300,
                    "experience": 150,
                    "diana_trust": 25,
                    "special_recognition": "Dedicated to Diana",
                },
            },
        }

        mission_template = diana_missions.get(diana_mood)
        if not mission_template:
            return None

        # Personalizar con contexto especial
        mission_data = mission_template.copy()
        mission_data["mission_type"] = MissionType.SPECIAL
        mission_data["difficulty"] = MissionDifficulty.HARD
        mission_data["priority"] = 200  # Alta prioridad
        mission_data["expires_at"] = datetime.utcnow() + timedelta(hours=48)
        mission_data["narrative_context"] = {
            "diana_mood": diana_mood,
            "special_context": special_context,
            "created_from": "diana_special",
        }

        # Añadir introducción especial de Diana
        mission_data["diana_message"] = self._generate_diana_special_message(
            diana_mood, narrative_state.primary_archetype, user.first_name
        )

        mission = self.create_mission(user_id, mission_data)

        return mission

    # ===== ANÁLISIS Y ESTADÍSTICAS =====

    def get_mission_statistics(self, user_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas de misiones del usuario"""

        # Contar misiones por estado
        completed = (
            self.db.query(Mission)
            .filter(
                and_(
                    Mission.user_id == user_id,
                    Mission.status == MissionStatus.COMPLETED,
                )
            )
            .count()
        )

        failed = (
            self.db.query(Mission)
            .filter(
                and_(Mission.user_id == user_id, Mission.status == MissionStatus.FAILED)
            )
            .count()
        )

        active = (
            self.db.query(Mission)
            .filter(
                and_(Mission.user_id == user_id, Mission.status == MissionStatus.ACTIVE)
            )
            .count()
        )

        # Calcular tasa de éxito
        total_completed = completed + failed
        success_rate = (completed / max(total_completed, 1)) * 100

        # Misiones por tipo
        type_stats = {}
        for mission_type in MissionType:
            count = (
                self.db.query(Mission)
                .filter(
                    and_(
                        Mission.user_id == user_id,
                        Mission.mission_type == mission_type,
                        Mission.status == MissionStatus.COMPLETED,
                    )
                )
                .count()
            )
            type_stats[mission_type.value] = count

        # Recompensas totales ganadas
        total_besitos = (
            self.db.query(
                func.sum(
                    func.json_extract(Mission.rewards, "$.besitos").cast(db.Integer)
                )
            )
            .filter(
                and_(
                    Mission.user_id == user_id,
                    Mission.status == MissionStatus.COMPLETED,
                )
            )
            .scalar()
            or 0
        )

        return {
            "missions_completed": completed,
            "missions_failed": failed,
            "missions_active": active,
            "success_rate": round(success_rate, 1),
            "missions_by_type": type_stats,
            "total_besitos_earned": total_besitos,
            "total_missions": completed + failed + active,
        }

    def get_mission_leaderboard(
        self, category: str = "completed", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene leaderboard de misiones"""

        if category == "completed":
            # Top usuarios por misiones completadas
            results = (
                self.db.query(
                    User.first_name,
                    User.username,
                    func.count(Mission.id).label("missions_completed"),
                )
                .join(Mission, User.id == Mission.user_id)
                .filter(Mission.status == MissionStatus.COMPLETED)
                .group_by(User.id)
                .order_by(desc("missions_completed"))
                .limit(limit)
                .all()
            )

            return [
                {
                    "position": i + 1,
                    "name": name,
                    "username": username,
                    "missions_completed": count,
                }
                for i, (name, username, count) in enumerate(results)
            ]

        elif category == "success_rate":
            # Top usuarios por tasa de éxito
            # Aquí iría una query más compleja para calcular success rate
            # Por simplicidad, retornamos lista vacía por ahora
            return []

        return []

    # ===== MÉTODOS AUXILIARES =====

    def _generate_daily_missions(
        self, user: User, narrative_state: UserNarrativeState
    ) -> List[Dict[str, Any]]:
        """Genera misiones diarias personalizadas"""

        missions = []

        # Misión básica diaria (siempre incluida)
        basic_mission = {
            "title": "Presencia Diaria",
            "description": "Diana valora la consistencia. Demuestra tu dedicación diaria.",
            "type": MissionType.DAILY,
            "difficulty": MissionDifficulty.EASY,
            "objectives": {
                "daily_interaction": {
                    "type": "activity_count",
                    "target": 3,
                    "activity": "any",
                    "description": "Interactúa 3 veces con el bot hoy",
                }
            },
            "rewards": {"besitos": 50, "experience": 25},
            "expires_at": datetime.utcnow() + timedelta(hours=24),
        }
        missions.append(basic_mission)

        # Misión basada en nivel narrativo
        narrative_mission = self._get_narrative_daily_mission(
            narrative_state.current_level
        )
        if narrative_mission:
            missions.append(narrative_mission)

        # Misión basada en arquetipo
        archetype_mission = self._get_archetype_daily_mission(
            narrative_state.primary_archetype, user.level
        )
        if archetype_mission:
            missions.append(archetype_mission)

        # Misión de desafío (solo usuarios nivel 5+)
        if user.level >= 5:
            challenge_mission = self._get_challenge_daily_mission(
                user.level, narrative_state.diana_trust_level
            )
            if challenge_mission:
                missions.append(challenge_mission)

        return missions

    def _get_narrative_daily_mission(
        self, current_level: NarrativeLevel
    ) -> Optional[Dict[str, Any]]:
        """Obtiene misión diaria basada en nivel narrativo"""

        narrative_missions = {
            NarrativeLevel.NEWCOMER: {
                "title": "Primeros Pasos hacia Diana",
                "description": "Diana observa tus primeros movimientos. Demuestra que mereces su atención.",
                "objectives": {
                    "explore_features": {
                        "type": "feature_usage",
                        "target": 2,
                        "features": ["profile", "games"],
                        "description": "Explora 2 funciones diferentes del bot",
                    }
                },
                "rewards": {"besitos": 75, "experience": 40},
            },
            NarrativeLevel.LEVEL_1_KINKY: {
                "title": "Profundización en Los Kinkys",
                "description": "En Los Kinkys, cada acción cuenta. Diana evalúa tu compromiso.",
                "objectives": {
                    "consistent_engagement": {
                        "type": "time_based",
                        "target": 6,  # 6 horas de actividad
                        "description": "Mantén actividad consistente durante 6 horas",
                    }
                },
                "rewards": {"besitos": 100, "experience": 60, "diana_interest": 5},
            },
            NarrativeLevel.LEVEL_4_DIVAN_ENTRY: {
                "title": "Intimidad del Diván",
                "description": "En el Diván, Diana espera más profundidad en tus interacciones.",
                "objectives": {
                    "quality_interactions": {
                        "type": "interaction_quality",
                        "target": 3,
                        "min_quality_score": 80,
                        "description": "Realiza 3 interacciones de alta calidad",
                    }
                },
                "rewards": {"besitos": 200, "experience": 100, "diana_trust": 10},
            },
        }

        mission_template = narrative_missions.get(current_level)
        if mission_template:
            mission_data = mission_template.copy()
            mission_data["type"] = MissionType.DAILY
            mission_data["difficulty"] = MissionDifficulty.MEDIUM
            mission_data["expires_at"] = datetime.utcnow() + timedelta(hours=24)
            return mission_data

        return None

    def _get_archetype_daily_mission(
        self, archetype: Optional[UserArchetype], user_level: int
    ) -> Optional[Dict[str, Any]]:
        """Obtiene misión diaria basada en arquetipo del usuario"""

        if not archetype:
            return None

        archetype_missions = {
            UserArchetype.EXPLORER: {
                "title": "Exploración Meticulosa",
                "description": "Tu naturaleza exploradora fascina a Diana. Demuestra tu atención al detalle.",
                "objectives": {
                    "detailed_exploration": {
                        "type": "feature_exploration",
                        "target": 4,
                        "min_time_per_feature": 120,  # 2 minutos por función
                        "description": "Explora 4 funciones con detalle",
                    }
                },
                "rewards": {"besitos": 120, "experience": 80},
            },
            UserArchetype.ROMANTIC: {
                "title": "Romanticismo Auténtico",
                "description": "Diana aprecia tu naturaleza romántica. Expresa tu lado más poético.",
                "objectives": {
                    "romantic_expression": {
                        "type": "message_sentiment",
                        "target": 2,
                        "sentiment": "romantic",
                        "description": "Envía 2 mensajes con tono romántico auténtico",
                    }
                },
                "rewards": {"besitos": 150, "experience": 70, "diana_interest": 10},
            },
            UserArchetype.PERSISTENT: {
                "title": "Persistencia Admirada",
                "description": "Diana valora tu dedicación constante. Demuestra tu perseverancia.",
                "objectives": {
                    "persistent_activity": {
                        "type": "activity_consistency",
                        "target": 8,  # 8 intervalos de actividad
                        "interval_hours": 2,
                        "description": "Mantén actividad cada 2 horas por 16 horas",
                    }
                },
                "rewards": {"besitos": 180, "experience": 90, "diana_trust": 8},
            },
            UserArchetype.ANALYTICAL: {
                "title": "Análisis Profundo",
                "description": "Tu mente analítica intriga a Diana. Demuestra tu capacidad de comprensión.",
                "objectives": {
                    "analytical_thinking": {
                        "type": "complex_interaction",
                        "target": 1,
                        "complexity_score": 85,
                        "description": "Completa una interacción compleja con puntuación alta",
                    }
                },
                "rewards": {"besitos": 140, "experience": 100},
            },
        }

        mission_template = archetype_missions.get(archetype)
        if mission_template:
            mission_data = mission_template.copy()
            mission_data["type"] = MissionType.DAILY
            mission_data["difficulty"] = MissionDifficulty.MEDIUM
            mission_data["expires_at"] = datetime.utcnow() + timedelta(hours=24)

            # Ajustar recompensas según nivel del usuario
            level_multiplier = min(user_level / 10, 2.0)  # Máximo 2x
            for reward_type in mission_data["rewards"]:
                if isinstance(mission_data["rewards"][reward_type], int):
                    mission_data["rewards"][reward_type] = int(
                        mission_data["rewards"][reward_type] * level_multiplier
                    )

            return mission_data

        return None

    def _get_challenge_daily_mission(
        self, user_level: int, diana_trust: int
    ) -> Optional[Dict[str, Any]]:
        """Obtiene misión de desafío para usuarios avanzados"""

        if user_level < 5:
            return None

        # Desafíos más complejos para usuarios avanzados
        challenges = [
            {
                "title": "Maestría Total",
                "description": "Diana quiere ver tu dominio completo de todas las habilidades.",
                "objectives": {
                    "complete_mastery": {
                        "type": "multi_objective",
                        "targets": {
                            "games_played": 2,
                            "quality_score": 90,
                            "time_consistency": 8,
                        },
                        "description": "Domina múltiples aspectos simultáneamente",
                    }
                },
                "rewards": {"besitos": 300, "experience": 200, "diana_trust": 15},
            },
            {
                "title": "Dedicación Suprema",
                "description": "Diana pone a prueba tu dedicación máxima hacia ella.",
                "objectives": {
                    "supreme_dedication": {
                        "type": "endurance_test",
                        "target": 12,  # 12 horas de actividad espaciada
                        "max_gap_hours": 2,
                        "description": "Demuestra dedicación constante por 12 horas",
                    }
                },
                "rewards": {
                    "besitos": 400,
                    "experience": 250,
                    "diana_trust": 20,
                    "special_recognition": "Supreme Dedication",
                },
            },
        ]

        # Seleccionar desafío basado en nivel de confianza con Diana
        if diana_trust >= 70:
            challenge = challenges[1]  # Desafío supremo
        else:
            challenge = challenges[0]  # Desafío maestría

        challenge_data = challenge.copy()
        challenge_data["type"] = MissionType.CHALLENGE
        challenge_data["difficulty"] = MissionDifficulty.HARD
        challenge_data["expires_at"] = datetime.utcnow() + timedelta(
            hours=36
        )  # Más tiempo para desafíos

        return challenge_data

    def _evaluate_mission_objectives(
        self, mission: Mission, user_action: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Evalúa si los objetivos de la misión se han cumplido"""

        objectives = mission.objectives or {}
        progress = mission.progress or {}
        completed_objectives = 0
        total_objectives = len(objectives)

        result = {
            "completed": False,
            "progress": progress.copy(),
            "completed_objectives": [],
            "remaining_objectives": [],
            "completion_percentage": 0,
        }

        for obj_key, obj_config in objectives.items():
            obj_type = obj_config.get("type")
            target = obj_config.get("target", 1)
            current_progress = progress.get(obj_key, 0)

            # Evaluar según tipo de objetivo
            objective_completed = False

            if obj_type == "activity_count":
                if user_action and user_action.get("type") == obj_config.get(
                    "activity", "any"
                ):
                    current_progress += 1
                    progress[obj_key] = current_progress

                objective_completed = current_progress >= target

            elif obj_type == "time_based":
                # Verificar si ha pasado el tiempo suficiente con actividad
                if user_action:
                    progress[obj_key] = current_progress + 1
                objective_completed = progress[obj_key] >= target

            elif obj_type == "interaction_quality":
                if user_action and user_action.get(
                    "quality_score", 0
                ) >= obj_config.get("min_quality_score", 80):
                    current_progress += 1
                    progress[obj_key] = current_progress
                objective_completed = current_progress >= target

            elif obj_type == "feature_usage":
                if user_action and user_action.get("feature") in obj_config.get(
                    "features", []
                ):
                    if "used_features" not in progress:
                        progress["used_features"] = []
                    if user_action["feature"] not in progress["used_features"]:
                        progress["used_features"].append(user_action["feature"])
                    progress[obj_key] = len(progress["used_features"])
                objective_completed = progress.get(obj_key, 0) >= target

            # Registrar resultado del objetivo
            if objective_completed:
                completed_objectives += 1
                result["completed_objectives"].append(obj_key)
            else:
                result["remaining_objectives"].append(
                    {
                        "key": obj_key,
                        "description": obj_config.get("description"),
                        "progress": progress.get(obj_key, 0),
                        "target": target,
                    }
                )

        # Calcular porcentaje de completado
        result["completion_percentage"] = (
            completed_objectives / max(total_objectives, 1)
        ) * 100
        result["completed"] = completed_objectives == total_objectives
        result["progress"] = progress

        return result

    def _complete_mission(
        self, mission: Mission, completion_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Completa una misión y otorga recompensas"""

        mission.status = MissionStatus.COMPLETED
        mission.completed_at = datetime.utcnow()
        mission.progress = completion_result.get("progress", {})
        mission.completion_notes = json.dumps(completion_result)

        # Otorgar recompensas
        rewards_result = self._grant_mission_rewards(mission)

        self.db.commit()

        # Generar mensaje de completado con voz de Lucien
        completion_message = self._generate_completion_message(mission, rewards_result)

        # Trigger narrativo por completar misión
        self._trigger_mission_completion_narrative(mission)

        return {
            "success": True,
            "mission_id": mission.id,
            "mission_title": mission.title,
            "rewards": rewards_result,
            "message": completion_message,
            "completion_time": mission.completed_at.isoformat(),
        }

    def _update_mission_progress(
        self, mission: Mission, completion_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Actualiza progreso de misión sin completar"""

        mission.progress = completion_result.get("progress", {})
        mission.updated_at = datetime.utcnow()
        self.db.commit()

        # Generar mensaje de progreso
        progress_message = self._generate_progress_message(mission, completion_result)

        return {
            "success": True,
            "mission_id": mission.id,
            "progress": completion_result["completion_percentage"],
            "message": progress_message,
            "remaining_objectives": completion_result["remaining_objectives"],
        }

    def _grant_mission_rewards(self, mission: Mission) -> Dict[str, Any]:
        """Otorga las recompensas de la misión"""

        rewards = mission.rewards or {}
        granted_rewards = {}

        from services.user_service import UserService

        user_service = UserService()

        # Otorgar besitos
        if "besitos" in rewards:
            amount = rewards["besitos"]
            result = user_service.add_besitos(
                mission.user_id, amount, f"Misión: {mission.title}"
            )
            granted_rewards["besitos"] = amount

        # Otorgar experiencia
        if "experience" in rewards:
            amount = rewards["experience"]
            result = user_service.add_experience(
                mission.user_id, amount, f"Misión: {mission.title}"
            )
            granted_rewards["experience"] = amount

        # Otorgar mejoras a relación con Diana
        if "diana_interest" in rewards or "diana_trust" in rewards:
            narrative_state = user_service.get_or_create_narrative_state(
                mission.user_id
            )

            if "diana_interest" in rewards:
                narrative_state.diana_interest_level = min(
                    100,
                    narrative_state.diana_interest_level + rewards["diana_interest"],
                )
                granted_rewards["diana_interest"] = rewards["diana_interest"]

            if "diana_trust" in rewards:
                narrative_state.diana_trust_level = min(
                    100, narrative_state.diana_trust_level + rewards["diana_trust"]
                )
                granted_rewards["diana_trust"] = rewards["diana_trust"]

            self.db.commit()

        # Reconocimientos especiales
        if "special_recognition" in rewards:
            narrative_state = user_service.get_or_create_narrative_state(
                mission.user_id
            )
            if not narrative_state.special_recognitions:
                narrative_state.special_recognitions = []
            narrative_state.special_recognitions.append(
                {
                    "recognition": rewards["special_recognition"],
                    "earned_from": f"Mission: {mission.title}",
                    "date": datetime.utcnow().isoformat(),
                }
            )
            granted_rewards["special_recognition"] = rewards["special_recognition"]
            self.db.commit()

        return granted_rewards

    def _generate_completion_message(
        self, mission: Mission, rewards: Dict[str, Any]
    ) -> str:
        """Genera mensaje de misión completada con voz de Lucien"""

        user = self.db.query(User).filter(User.id == mission.user_id).first()

        # Mensaje base de Lucien
        base_message = f"""
{self.lucien.EMOJIS['lucien']} **Misión Completada con Elegancia**

*[Con satisfacción visible]*

**"{mission.title}"** - Completada magistralmente.

{self._get_mission_completion_comment(mission)}
        """.strip()

        # Recompensas
        rewards_text = "\n**Recompensas recibidas:**\n"
        if "besitos" in rewards:
            rewards_text += (
                f"💋 **{rewards['besitos']} Besitos** - Tokens de aprecio de Diana\n"
            )
        if "experience" in rewards:
            rewards_text += (
                f"⚡ **{rewards['experience']} Experiencia** - Crecimiento personal\n"
            )
        if "diana_interest" in rewards:
            rewards_text += f"💫 **+{rewards['diana_interest']} Interés de Diana** - Has captado su atención\n"
        if "diana_trust" in rewards:
            rewards_text += f"🗝️ **+{rewards['diana_trust']} Confianza de Diana** - Has ganado su confianza\n"
        if "special_recognition" in rewards:
            rewards_text += (
                f"👑 **{rewards['special_recognition']}** - Reconocimiento especial\n"
            )

        # Comentario final personalizado
        final_comment = self._get_personalized_completion_comment(mission, user)

        return base_message + rewards_text + final_comment

    def _get_mission_completion_comment(self, mission: Mission) -> str:
        """Obtiene comentario específico sobre la completación"""

        if mission.mission_type == MissionType.DAILY:
            return "*[Con aprobación]*\nLa consistencia diaria es lo que más aprecia Diana. Has demostrado dedicación."
        elif mission.mission_type == MissionType.SPECIAL:
            return "*[Con admiración]*\nMisiones especiales requieren algo extra. Diana está... impresionada."
        elif mission.mission_type == MissionType.CHALLENGE:
            return "*[Con respeto genuino]*\nPocos completan estos desafíos. Has demostrado ser excepcional."
        elif mission.mission_type == MissionType.NARRATIVE:
            return "*[Con elegancia]*\nHas navegado las complejidades narrativas con gracia. Diana toma nota."
        else:
            return "*[Con profesionalismo]*\nTarea completada con la dedicación que Diana espera."

    def _get_personalized_completion_comment(self, mission: Mission, user: User) -> str:
        """Obtiene comentario personalizado final"""

        from services.user_service import UserService

        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(user.id)

        trust_level = narrative_state.diana_trust_level

        if trust_level >= 80:
            return f"""

{self.lucien.EMOJIS['diana']} *Diana susurra desde su espacio privado:*
"*{user.first_name}... cada misión que completas me revela más sobre quién eres realmente. Me gusta lo que veo.*"
            """.strip()
        elif trust_level >= 60:
            return f"""

*[Lucien sonríe discretamente]*
Diana ha comentado sobre tu progreso, {user.first_name}. Dice que hay algo... especial en tu dedicación.
            """.strip()
        else:
            return f"""

*[Con aliento profesional]*
Diana observa cada misión completada, {user.first_name}. Continúa así y pronto notarás cambios en su actitud hacia ti.
            """.strip()

    def _generate_progress_message(
        self, mission: Mission, completion_result: Dict[str, Any]
    ) -> str:
        """Genera mensaje de progreso de misión"""

        progress_percentage = completion_result["completion_percentage"]
        remaining = completion_result["remaining_objectives"]

        base_message = f"""
{self.lucien.EMOJIS['lucien']} **Progreso en "{mission.title}"**

*[Consultando sus notas]*

**Progreso:** {progress_percentage:.1f}% completado

**Objetivos restantes:**
        """.strip()

        for obj in remaining[:3]:  # Mostrar solo los primeros 3
            base_message += (
                f"\n• {obj['description']} ({obj['progress']}/{obj['target']})"
            )

        if len(remaining) > 3:
            base_message += f"\n• ... y {len(remaining) - 3} objetivos más"

        encouragement = self._get_progress_encouragement(progress_percentage)

        return base_message + f"\n\n{encouragement}"

    def _get_progress_encouragement(self, progress_percentage: float) -> str:
        """Obtiene mensaje de aliento según progreso"""

        if progress_percentage >= 75:
            return "*[Con anticipación]*\nEstás muy cerca. Diana está observando tu aproximación final con interés."
        elif progress_percentage >= 50:
            return "*[Con aprobación]*\nBuen progreso. Diana nota tu consistencia y dedicación."
        elif progress_percentage >= 25:
            return "*[Con aliento]*\nVas bien encaminado. Cada paso te acerca más a impresionar a Diana."
        else:
            return "*[Con paciencia]*\nTodo gran logro comienza con pequeños pasos. Diana valora la persistencia."

    def _trigger_mission_completion_narrative(self, mission: Mission) -> None:
        """Dispara eventos narrativos al completar misiones especiales"""

        # Trigger para el servicio de triggers narrativos
        from services.narrative_trigger_service import NarrativeTriggerService

        trigger_service = NarrativeTriggerService()

        # Contexto para posibles triggers
        context = {
            "mission_completed": mission.title,
            "mission_type": mission.mission_type.value,
            "mission_difficulty": mission.difficulty.value,
            "completion_time": mission.completed_at.isoformat(),
        }

        # Evaluar triggers narrativos
        user = self.db.query(User).filter(User.id == mission.user_id).first()
        if user:
            # Esto se ejecutará asíncronamente para no bloquear
            # En una implementación real, esto se haría en background
            pass

    def _load_mission_templates(self) -> Dict[str, Any]:
        """Carga templates de misiones"""
        # Por ahora retornamos dict vacío, en implementación real
        # esto cargaría desde base de datos o archivos de configuración
        return {}

    def _handle_mission_expiry(self, mission: Mission) -> Dict[str, Any]:
        """Maneja expiración de misión"""

        mission.status = MissionStatus.FAILED
        mission.completed_at = datetime.utcnow()
        mission.completion_notes = "Expired"
        self.db.commit()

        expiry_message = f"""
{self.lucien.EMOJIS['lucien']} **Misión Expirada**

*[Con aire de disculpa]*

"{mission.title}" ha expirado sin completarse.

*[Con aliento]*
Diana comprende que a veces las circunstancias no permiten completar todo. Habrá más oportunidades de impresionarla.
        """.strip()

        return {
            "success": False,
            "error": "Mission expired",
            "mission_id": mission.id,
            "message": expiry_message,
        }

    def _generate_cancellation_message(self, mission: Mission, reason: str) -> str:
        """Genera mensaje de cancelación de misión"""

        return f"""
{self.lucien.EMOJIS['lucien']} **Misión Cancelada**

*[Con comprensión profesional]*

"{mission.title}" ha sido cancelada.

**Razón:** {reason}

*[Con elegancia]*
Diana comprende que a veces los planes cambian. Lo importante es la intención de crecer y acercarse a ella.
        """.strip()

    def _generate_diana_special_message(
        self, diana_mood: str, user_archetype: Optional[UserArchetype], user_name: str
    ) -> str:
        """Genera mensaje especial de Diana para misiones especiales"""

        mood_messages = {
            "curious": f"*{user_name}... hay algo sobre ti que despierta mi curiosidad. Déjame conocerte mejor.*",
            "playful": f"*Estoy de humor juguetón hoy, {user_name}. ¿Te atreves a jugar conmigo?*",
            "testing": f"*{user_name}, es hora de que demuestres tu verdadera dedicación hacia mí.*",
        }

        base_message = mood_messages.get(
            diana_mood, f"*{user_name}, tengo algo especial preparado para ti.*"
        )

        # Personalizar según arquetipo
        if user_archetype == UserArchetype.ROMANTIC:
            base_message += (
                "*\n\n*Tu romanticismo me intriga... veamos qué tan profundo llega.*"
            )
        elif user_archetype == UserArchetype.ANALYTICAL:
            base_message += "*\n\n*Tu mente analítica es... estimulante. Déjame poner a prueba esa inteligencia.*"

        return f"""
{self.lucien.EMOJIS['diana']} *Diana aparece con una sonrisa enigmática:*

"{base_message}"
        """.strip()
   