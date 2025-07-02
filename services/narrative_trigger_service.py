from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from models.narrative_triggers import (
    NarrativeTrigger,
    UserTriggerExecution,
    TriggerType,
    TriggerConditionOperator,
    TriggerFrequency,
)
from models.narrative_state import UserNarrativeState, NarrativeLevel, UserArchetype
from models.user import User
from models.mission import Mission
from models.auction import Auction
from config.database import get_db
from utils.lucien_voice import LucienVoice
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import re
import json
import asyncio
from dataclasses import dataclass


@dataclass
class TriggerEvaluationResult:
    """Resultado de evaluación de trigger"""

    matches: bool
    details: Dict[str, Any]
    missing_conditions: List[str]
    user_context: Dict[str, Any]
    trigger_context: Dict[str, Any]


@dataclass
class TriggerExecutionResult:
    """Resultado de ejecución de trigger"""

    success: bool
    trigger_id: int
    user_id: int
    action_taken: str
    result_data: Dict[str, Any]
    user_response_expected: bool
    next_steps: List[str]


class NarrativeTriggerService:
    """Servicio para evaluación y ejecución de triggers narrativos"""

    def __init__(self):
        self.db = next(get_db())
        self.lucien = LucienVoice()

        # Operadores de comparación
        self.operators = {
            TriggerConditionOperator.EQUALS: lambda a, b: a == b,
            TriggerConditionOperator.GREATER_THAN: lambda a, b: a > b,
            TriggerConditionOperator.LESS_THAN: lambda a, b: a < b,
            TriggerConditionOperator.GREATER_EQUAL: lambda a, b: a >= b,
            TriggerConditionOperator.LESS_EQUAL: lambda a, b: a <= b,
            TriggerConditionOperator.CONTAINS: lambda a, b: str(b).lower()
            in str(a).lower(),
            TriggerConditionOperator.NOT_CONTAINS: lambda a, b: str(b).lower()
            not in str(a).lower(),
            TriggerConditionOperator.IN_LIST: lambda a, b: a in b,
            TriggerConditionOperator.NOT_IN_LIST: lambda a, b: a not in b,
            TriggerConditionOperator.REGEX_MATCH: lambda a, b: bool(
                re.search(str(b), str(a), re.IGNORECASE)
            ),
        }

    # ===== EVALUACIÓN DE TRIGGERS =====

    async def evaluate_all_triggers_for_user(
        self, user: User, context: Dict[str, Any] = None
    ) -> List[TriggerEvaluationResult]:
        """Evalúa todos los triggers activos para un usuario"""

        # Obtener triggers activos
        active_triggers = (
            self.db.query(NarrativeTrigger)
            .filter(
                and_(
                    NarrativeTrigger.is_active == True,
                    or_(
                        NarrativeTrigger.valid_from.is_(None),
                        NarrativeTrigger.valid_from <= datetime.utcnow(),
                    ),
                    or_(
                        NarrativeTrigger.valid_until.is_(None),
                        NarrativeTrigger.valid_until >= datetime.utcnow(),
                    ),
                )
            )
            .order_by(desc(NarrativeTrigger.priority))
            .all()
        )

        results = []
        user_context = await self._build_user_context(user, context or {})

        for trigger in active_triggers:
            # Verificar cooldown y frecuencia
            if not self._can_trigger_for_user(trigger, user.id):
                continue

            # Evaluar trigger
            evaluation = await self.evaluate_trigger_for_user(
                trigger, user, user_context
            )
            if evaluation.matches:
                results.append(evaluation)

        return results

    async def evaluate_trigger_for_user(
        self, trigger: NarrativeTrigger, user: User, user_context: Dict[str, Any] = None
    ) -> TriggerEvaluationResult:
        """Evalúa un trigger específico para un usuario"""

        if user_context is None:
            user_context = await self._build_user_context(user)

        details = {}
        missing_conditions = []

        # Verificar filtros de usuario primero
        user_filter_result = self._check_user_filters(trigger, user, user_context)
        if not user_filter_result["passes"]:
            return TriggerEvaluationResult(
                matches=False,
                details=user_filter_result,
                missing_conditions=user_filter_result["missing"],
                user_context=user_context,
                trigger_context={
                    "trigger_id": trigger.id,
                    "trigger_name": trigger.name,
                },
            )

        # Evaluar condiciones principales
        conditions_result = await self._evaluate_conditions(
            trigger.conditions, user_context
        )

        return TriggerEvaluationResult(
            matches=conditions_result["all_match"],
            details={**user_filter_result, **conditions_result},
            missing_conditions=conditions_result.get("missing", []),
            user_context=user_context,
            trigger_context={
                "trigger_id": trigger.id,
                "trigger_name": trigger.name,
                "trigger_type": trigger.trigger_type.value,
            },
        )

    async def _evaluate_conditions(
        self, conditions: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evalúa todas las condiciones de un trigger"""

        results = {}
        all_match = True
        missing = []

        for condition_key, condition_config in conditions.items():
            try:
                operator = TriggerConditionOperator(condition_config["operator"])
                expected_value = condition_config["value"]

                # Obtener valor actual del contexto del usuario
                actual_value = self._get_context_value(user_context, condition_key)

                if actual_value is None:
                    results[condition_key] = {
                        "status": "missing_data",
                        "expected": expected_value,
                        "actual": None,
                    }
                    missing.append(condition_key)
                    all_match = False
                    continue

                # Aplicar operador
                matches = self.operators[operator](actual_value, expected_value)

                results[condition_key] = {
                    "status": "match" if matches else "no_match",
                    "operator": operator.value,
                    "expected": expected_value,
                    "actual": actual_value,
                    "matches": matches,
                }

                if not matches:
                    all_match = False
                    missing.append(condition_key)

            except Exception as e:
                results[condition_key] = {"status": "error", "error": str(e)}
                all_match = False
                missing.append(condition_key)

        return {
            "all_match": all_match,
            "individual_results": results,
            "missing": missing,
        }

    def _check_user_filters(
        self, trigger: NarrativeTrigger, user: User, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verifica filtros de usuario para el trigger"""

        filters = trigger.user_filters or {}
        results = {"passes": True, "filter_results": {}, "missing": []}

        # Verificar nivel mínimo
        if "min_level" in filters:
            user_level = user_context.get("level", 1)
            if user_level < filters["min_level"]:
                results["passes"] = False
                results["filter_results"][
                    "min_level"
                ] = f"Usuario nivel {user_level} < requerido {filters['min_level']}"
                results["missing"].append("min_level")

        # Verificar nivel máximo
        if "max_level" in filters:
            user_level = user_context.get("level", 1)
            if user_level > filters["max_level"]:
                results["passes"] = False
                results["filter_results"][
                    "max_level"
                ] = f"Usuario nivel {user_level} > máximo {filters['max_level']}"
                results["missing"].append("max_level")

        # Verificar arquetipos requeridos
        if "required_archetypes" in filters:
            user_archetype = user_context.get("primary_archetype")
            if user_archetype not in filters["required_archetypes"]:
                results["passes"] = False
                results["filter_results"][
                    "required_archetypes"
                ] = f"Arquetipo {user_archetype} no en lista requerida"
                results["missing"].append("required_archetypes")

        # Verificar arquetipos excluidos
        if "excluded_archetypes" in filters:
            user_archetype = user_context.get("primary_archetype")
            if user_archetype in filters["excluded_archetypes"]:
                results["passes"] = False
                results["filter_results"][
                    "excluded_archetypes"
                ] = f"Arquetipo {user_archetype} está excluido"
                results["missing"].append("excluded_archetypes")

        # Verificar acceso VIP
        if filters.get("vip_only", False):
            if not user_context.get("has_divan_access", False):
                results["passes"] = False
                results["filter_results"]["vip_only"] = "Usuario no tiene acceso VIP"
                results["missing"].append("vip_access")

        # Verificar niveles narrativos
        if "narrative_levels" in filters:
            current_level = user_context.get("narrative_level")
            if current_level not in filters["narrative_levels"]:
                results["passes"] = False
                results["filter_results"][
                    "narrative_levels"
                ] = f"Nivel narrativo {current_level} no permitido"
                results["missing"].append("narrative_level")

        return results

    def _can_trigger_for_user(self, trigger: NarrativeTrigger, user_id: int) -> bool:
        """Verifica si el trigger puede ejecutarse para el usuario (cooldown/frecuencia)"""

        # Obtener última ejecución
        last_execution = (
            self.db.query(UserTriggerExecution)
            .filter(
                and_(
                    UserTriggerExecution.user_id == user_id,
                    UserTriggerExecution.trigger_id == trigger.id,
                    UserTriggerExecution.success == True,
                )
            )
            .order_by(desc(UserTriggerExecution.executed_at))
            .first()
        )

        if not last_execution:
            return True  # Primera vez

        now = datetime.utcnow()

        # Verificar frecuencia
        if trigger.frequency == TriggerFrequency.ONCE:
            return False  # Solo una vez y ya se ejecutó

        elif trigger.frequency == TriggerFrequency.DAILY:
            return (now - last_execution.executed_at).days >= 1

        elif trigger.frequency == TriggerFrequency.WEEKLY:
            return (now - last_execution.executed_at).days >= 7

        elif trigger.frequency == TriggerFrequency.MONTHLY:
            return (now - last_execution.executed_at).days >= 30

        elif trigger.frequency == TriggerFrequency.CONDITIONAL:
            # Verificar si puede repetir basado en can_repeat_after
            return (
                last_execution.can_repeat_after is None
                or now >= last_execution.can_repeat_after
            )

        # UNLIMITED - verificar solo cooldown
        if trigger.cooldown_seconds > 0:
            return (
                now - last_execution.executed_at
            ).total_seconds() >= trigger.cooldown_seconds

        return True

    # ===== EJECUCIÓN DE TRIGGERS =====

    async def execute_trigger(
        self,
        trigger: NarrativeTrigger,
        user: User,
        evaluation_result: TriggerEvaluationResult,
    ) -> TriggerExecutionResult:
        """Ejecuta un trigger para un usuario"""

        try:
            # Aplicar delay si existe
            if trigger.delay_seconds > 0:
                await asyncio.sleep(trigger.delay_seconds)

            # Ejecutar acción según tipo
            execution_result = await self._execute_trigger_action(
                trigger, user, evaluation_result
            )

            # Registrar ejecución
            execution_record = UserTriggerExecution(
                user_id=user.id,
                trigger_id=trigger.id,
                executed_at=datetime.utcnow(),
                execution_context=evaluation_result.user_context,
                success=execution_result.success,
                result_data=execution_result.result_data,
            )

            # Calcular próxima repetición si aplica
            if trigger.frequency == TriggerFrequency.CONDITIONAL:
                # Calcular basado en el resultado de la acción
                next_repeat_delay = execution_result.result_data.get(
                    "next_repeat_hours", 24
                )
                execution_record.can_repeat_after = datetime.utcnow() + timedelta(
                    hours=next_repeat_delay
                )

            self.db.add(execution_record)

            # Actualizar estadísticas del trigger
            trigger.times_triggered += 1
            trigger.last_triggered = datetime.utcnow()

            self.db.commit()

            return execution_result

        except Exception as e:
            # Registrar error
            error_record = UserTriggerExecution(
                user_id=user.id,
                trigger_id=trigger.id,
                executed_at=datetime.utcnow(),
                execution_context=evaluation_result.user_context,
                success=False,
                result_data={"error": str(e)},
            )

            self.db.add(error_record)
            self.db.commit()

            return TriggerExecutionResult(
                success=False,
                trigger_id=trigger.id,
                user_id=user.id,
                action_taken="error",
                result_data={"error": str(e)},
                user_response_expected=False,
                next_steps=["check_logs"],
            )

    async def _execute_trigger_action(
        self,
        trigger: NarrativeTrigger,
        user: User,
        evaluation_result: TriggerEvaluationResult,
    ) -> TriggerExecutionResult:
        """Ejecuta la acción específica del trigger"""

        action_config = trigger.action_config
        action_type = trigger.action_type

        if action_type == "scene":
            return await self._execute_scene_action(
                trigger, user, action_config, evaluation_result
            )

        elif action_type == "message":
            return await self._execute_message_action(
                trigger, user, action_config, evaluation_result
            )

        elif action_type == "notification":
            return await self._execute_notification_action(
                trigger, user, action_config, evaluation_result
            )

        elif action_type == "reward":
            return await self._execute_reward_action(
                trigger, user, action_config, evaluation_result
            )

        elif action_type == "mission_unlock":
            return await self._execute_mission_unlock_action(
                trigger, user, action_config, evaluation_result
            )

        elif action_type == "level_progression":
            return await self._execute_level_progression_action(
                trigger, user, action_config, evaluation_result
            )

        elif action_type == "special_event":
            return await self._execute_special_event_action(
                trigger, user, action_config, evaluation_result
            )

        else:
            raise ValueError(f"Tipo de acción no soportado: {action_type}")

    async def _execute_scene_action(
        self,
        trigger: NarrativeTrigger,
        user: User,
        action_config: Dict,
        evaluation_result: TriggerEvaluationResult,
    ) -> TriggerExecutionResult:
        """Ejecuta una escena narrativa"""

        # Obtener template de escena
        scene_template = action_config.get("scene_template", "default_special_scene")

        # Personalizar basado en arquetipo del usuario
        user_archetype = evaluation_result.user_context.get("primary_archetype")
        personalization = action_config.get("personalization", {})

        # Generar diálogo personalizado
        if user_archetype and user_archetype in personalization:
            dialogue = personalization[user_archetype]
        else:
            dialogue = action_config.get(
                "default_dialogue", "Diana tiene algo especial que compartir contigo..."
            )

        # Crear mensaje de Lucien introduciendo la escena
        lucien_intro = f"""
{self.lucien.EMOJIS['lucien']} **Algo Inesperado Ocurre**

*[Con una mezcla de sorpresa y aprobación]*

{trigger.name} - Diana ha estado observando y ha decidido que mereces... algo especial.

*[Con elegancia teatral]*

{dialogue}

{self._get_context_aware_comment(evaluation_result.user_context)}
        """.strip()

        # ¿Diana aparece directamente?
        diana_appears = action_config.get("diana_appears", True)
        diana_message = ""

        if diana_appears:
            diana_dialogue = action_config.get("diana_dialogue", {})
            if user_archetype and user_archetype in diana_dialogue:
                diana_text = diana_dialogue[user_archetype]
            else:
                diana_text = diana_dialogue.get(
                    "default", "Has captado mi atención de una manera... especial."
                )

            diana_message = f"""

{self.lucien.EMOJIS['diana']} *Diana se materializa con una sonrisa enigmática:*

"{diana_text}"
            """.strip()

        # Recompensas
        rewards = action_config.get("rewards", {})
        rewards_text = ""

        if rewards:
            rewards_text = f"""

**Recompensas Especiales:**
"""
            if "besitos" in rewards:
                rewards_text += f"💋 **{rewards['besitos']} Besitos** - Tokens especiales de Diana\n"
            if "experience" in rewards:
                rewards_text += f"⚡ **{rewards['experience']} Experiencia** - Crecimiento personal\n"
            if "special_recognition" in rewards:
                rewards_text += f"👑 **{rewards['special_recognition']}** - Reconocimiento especial\n"

        full_message = lucien_intro + diana_message + rewards_text

        return TriggerExecutionResult(
            success=True,
            trigger_id=trigger.id,
            user_id=user.id,
            action_taken="scene_delivered",
            result_data={
                "scene_template": scene_template,
                "message_sent": full_message,
                "rewards_given": rewards,
                "diana_appeared": diana_appears,
                "personalization_used": user_archetype,
            },
            user_response_expected=action_config.get("expects_response", False),
            next_steps=action_config.get("next_steps", []),
        )

    async def _execute_message_action(
        self,
        trigger: NarrativeTrigger,
        user: User,
        action_config: Dict,
        evaluation_result: TriggerEvaluationResult,
    ) -> TriggerExecutionResult:
        """Ejecuta envío de mensaje personalizado"""

        message_template = action_config.get("message_template", "")
        user_context = evaluation_result.user_context

        # Reemplazar variables en el template
        message = self._process_message_template(message_template, user_context, user)

        return TriggerExecutionResult(
            success=True,
            trigger_id=trigger.id,
            user_id=user.id,
            action_taken="message_sent",
            result_data={"message": message, "template_used": message_template},
            user_response_expected=action_config.get("expects_response", False),
            next_steps=action_config.get("next_steps", []),
        )

    async def _execute_reward_action(
        self,
        trigger: NarrativeTrigger,
        user: User,
        action_config: Dict,
        evaluation_result: TriggerEvaluationResult,
    ) -> TriggerExecutionResult:
        """Ejecuta otorgamiento de recompensas"""

        from services.user_service import UserService

        user_service = UserService()

        rewards_given = {}

        # Otorgar besitos
        if "besitos" in action_config:
            amount = action_config["besitos"]
            user_service.add_besitos(user.id, amount, f"Trigger: {trigger.name}")
            rewards_given["besitos"] = amount

        # Otorgar experiencia
        if "experience" in action_config:
            amount = action_config["experience"]
            user_service.add_experience(user.id, amount, f"Trigger: {trigger.name}")
            rewards_given["experience"] = amount

        # Mensaje de Lucien sobre las recompensas
        lucien_message = self.lucien.trigger_reward_message(
            trigger.name, rewards_given, evaluation_result.user_context
        )

        return TriggerExecutionResult(
            success=True,
            trigger_id=trigger.id,
            user_id=user.id,
            action_taken="rewards_given",
            result_data={"rewards": rewards_given, "message": lucien_message},
            user_response_expected=False,
            next_steps=[],
        )

    # ===== CONSTRUCCIÓN DE CONTEXTO =====

    async def _build_user_context(
        self, user: User, additional_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Construye contexto completo del usuario para evaluación"""

        # Obtener estado narrativo
        narrative_state = (
            self.db.query(UserNarrativeState)
            .filter(UserNarrativeState.user_id == user.id)
            .first()
        )

        if not narrative_state:
            # Crear estado inicial si no existe
            from services.user_service import UserService

            user_service = UserService()
            narrative_state = user_service.get_or_create_narrative_state(user.id)

        # Construir contexto base
        context = {
            # Datos del usuario
            "user_id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "level": user.level,
            "besitos": user.besitos,
            "experience": user.experience,
            "created_at": user.created_at,
            "last_activity": user.last_activity,
            # Estado narrativo
            "narrative_level": (
                narrative_state.current_level.value
                if narrative_state.current_level
                else "newcomer"
            ),
            "current_scene": narrative_state.current_scene,
            "primary_archetype": (
                narrative_state.primary_archetype.value
                if narrative_state.primary_archetype
                else None
            ),
            "secondary_archetype": (
                narrative_state.secondary_archetype.value
                if narrative_state.secondary_archetype
                else None
            ),
            "diana_interest_level": narrative_state.diana_interest_level,
            "diana_trust_level": narrative_state.diana_trust_level,
            "has_divan_access": narrative_state.has_divan_access,
            "scenes_completed": (
                len(narrative_state.scenes_completed)
                if narrative_state.scenes_completed
                else 0
            ),
            "diana_interactions": narrative_state.diana_interactions,
            # Métricas de tiempo
            "days_since_registration": (datetime.utcnow() - user.created_at).days,
            "days_since_last_activity": (
                (datetime.utcnow() - user.last_activity).days
                if user.last_activity
                else 0
            ),
            "hours_since_last_interaction": 0,  # Será calculado dinámicamente
        }

        # Añadir métricas de actividad
        context.update(await self._calculate_activity_metrics(user.id))

        # Añadir métricas de misiones
        context.update(await self._calculate_mission_metrics(user.id))

        # Añadir métricas de subastas
        context.update(await self._calculate_auction_metrics(user.id))

        # Añadir métricas de juegos
        context.update(await self._calculate_game_metrics(user.id))

        # Añadir contexto temporal
        context.update(self._get_temporal_context())

        # Merge con contexto adicional
        if additional_context:
            context.update(additional_context)

        return context

    async def _calculate_activity_metrics(self, user_id: int) -> Dict[str, Any]:
        """Calcula métricas de actividad del usuario"""

        # Aquí se conectarían con los servicios correspondientes
        # Por ahora retorno valores default
        return {
            "total_commands_used": 0,
            "favorite_time_of_day": "evening",
            "avg_session_length_minutes": 15,
            "days_active_last_week": 0,
            "most_used_feature": "mission",
        }

    async def _calculate_mission_metrics(self, user_id: int) -> Dict[str, Any]:
        """Calcula métricas de misiones"""

        missions_completed = (
            self.db.query(Mission)
            .filter(and_(Mission.user_id == user_id, Mission.status == "completed"))
            .count()
        )

        missions_failed = (
            self.db.query(Mission)
            .filter(and_(Mission.user_id == user_id, Mission.status == "failed"))
            .count()
        )

        return {
            "missions_completed": missions_completed,
            "missions_failed": missions_failed,
            "mission_success_rate": missions_completed
            / max(missions_completed + missions_failed, 1),
            "missions_completed_last_week": 0,  # Requiere query temporal
            "avg_mission_completion_time_hours": 24,  # Default
        }

    async def _calculate_auction_metrics(self, user_id: int) -> Dict[str, Any]:
        """Calcula métricas de subastas"""

        # Placeholder - se implementará con AuctionService
        return {
            "auctions_participated": 0,
            "auctions_won": 0,
            "total_besitos_bid": 0,
            "highest_bid_amount": 0,
            "last_auction_participation": None,
        }

    async def _calculate_game_metrics(self, user_id: int) -> Dict[str, Any]:
        """Calcula métricas de juegos"""

        # Placeholder - se implementará con GameService
        return {
            "games_played": 0,
            "avg_game_score": 0,
            "favorite_game": None,
            "games_played_last_week": 0,
            "highest_score_achieved": 0,
        }

    def _get_temporal_context(self) -> Dict[str, Any]:
        """Obtiene contexto temporal actual"""

        now = datetime.utcnow()
        hour = now.hour

        if 6 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 18:
            time_of_day = "afternoon"
        elif 18 <= hour < 22:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        return {
            "current_hour": hour,
            "time_of_day": time_of_day,
            "day_of_week": now.strftime("%A").lower(),
            "is_weekend": now.weekday() >= 5,
            "day_of_month": now.day,
            "month": now.month,
        }

    def _get_context_value(self, context: Dict[str, Any], key: str) -> Any:
        """Obtiene valor del contexto, soportando notación de puntos"""

        if "." not in key:
            return context.get(key)

        # Soportar notación como "user.level" o "narrative.diana_trust_level"
        keys = key.split(".")
        value = context

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None

            if value is None:
                return None

        return value

    def _process_message_template(
        self, template: str, context: Dict[str, Any], user: User
    ) -> str:
        """Procesa template de mensaje con variables del contexto"""

        # Variables disponibles
        variables = {
            "user_name": user.first_name,
            "user_level": user.level,
            "besitos": user.besitos,
            "diana_trust": context.get("diana_trust_level", 0),
            "narrative_level": context.get("narrative_level", "newcomer"),
            "archetype": context.get("primary_archetype", "unknown"),
        }

        # Reemplazar variables en formato {variable}
        processed = template
        for var_name, var_value in variables.items():
            processed = processed.replace(f"{{{var_name}}}", str(var_value))

        return processed

    def _get_context_aware_comment(self, user_context: Dict[str, Any]) -> str:
        """Genera comentario de Lucien basado en el contexto del usuario"""

        trust_level = user_context.get("diana_trust_level", 0)
        archetype = user_context.get("primary_archetype")

        if trust_level >= 80:
            return "*[Con respeto genuino]*\nDiana rara vez otorga este nivel de atención. Eres... especial."
        elif trust_level >= 60:
            return "*[Con aprobación creciente]*\nDiana está genuinamente impresionada por tu progreso."
        elif archetype == "romantic":
            return "*[Con una sonrisa conocedora]*\nTu naturaleza romántica ha tocado algo en Diana que ella raramente muestra."
        elif archetype == "persistent":
            return "*[Con admiración]*\nTu persistencia finalmente ha capturado la atención completa de Diana."
        else:
            return "*[Con elegancia profesional]*\nDiana ha notado algo especial en ti que merece reconocimiento."

    # ===== MÉTODOS PÚBLICOS PARA TESTING =====

    async def test_trigger_for_user(
        self, trigger_id: int, user_id: int
    ) -> Dict[str, Any]:
        """Método para testing de triggers"""

        trigger = (
            self.db.query(NarrativeTrigger)
            .filter(NarrativeTrigger.id == trigger_id)
            .first()
        )
        user = self.db.query(User).filter(User.id == user_id).first()

        if not trigger or not user:
            return {"error": "Trigger o usuario no encontrado"}

        # Evaluar trigger
        evaluation = await self.evaluate_trigger_for_user(trigger, user)

        result = {
            "trigger_name": trigger.name,
            "user_name": user.first_name,
            "evaluation": {
                "matches": evaluation.matches,
                "details": evaluation.details,
                "missing_conditions": evaluation.missing_conditions,
            },
            "user_context": evaluation.user_context,
            "can_execute": self._can_trigger_for_user(trigger, user.id),
        }

        # Si está en modo test, también ejecutar
        if trigger.is_test_mode and evaluation.matches:
            execution = await self.execute_trigger(trigger, user, evaluation)
            result["execution"] = {
                "success": execution.success,
                "action_taken": execution.action_taken,
                "result_data": execution.result_data,
            }

        return result

    def get_trigger_execution_stats(self, days: int = 30) -> Dict[str, Any]:
        """Obtiene estadísticas de ejecución de triggers"""

        since_date = datetime.utcnow() - timedelta(days=days)

        total_executions = (
            self.db.query(UserTriggerExecution)
            .filter(UserTriggerExecution.executed_at >= since_date)
            .count()
        )

        successful_executions = (
            self.db.query(UserTriggerExecution)
            .filter(
                and_(
                    UserTriggerExecution.executed_at >= since_date,
                    UserTriggerExecution.success == True,
                )
            )
            .count()
        )

        # Top triggers por ejecuciones
        top_triggers = (
            self.db.query(
                NarrativeTrigger.name,
                func.count(UserTriggerExecution.id).label("executions"),
            )
            .join(
                UserTriggerExecution,
                NarrativeTrigger.id == UserTriggerExecution.trigger_id,
            )
            .filter(UserTriggerExecution.executed_at >= since_date)
            .group_by(NarrativeTrigger.name)
            .order_by(desc("executions"))
            .limit(10)
            .all()
        )

        return {
            "period_days": days,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / max(total_executions, 1),
            "top_triggers": [
                {"name": name, "executions": count} for name, count in top_triggers
            ],
        }
   