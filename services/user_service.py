from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from models.user import User
from models.narrative_state import (
    UserNarrativeState,
    NarrativeLevel,
    UserArchetype,
    EmotionalResponse,
)
from models.mission import Mission
from config.database import get_db
from utils.lucien_voice import LucienVoice
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import random


class UserService:
    """Servicio para gestión de usuarios y progreso narrativo"""

    def __init__(self):
        self.db = next(get_db())
        self.lucien = LucienVoice()

    def get_or_create_user(
        self,
        user_data_or_id: Any,
        first_name: str = None,
        username: str = None,
        last_name: str = None,
    ):
        """Obtiene o crea un usuario a partir de un diccionario o parámetros."""

        if isinstance(user_data_or_id, dict):
            telegram_id = user_data_or_id.get("telegram_id")
            first_name = user_data_or_id.get("first_name")
            username = user_data_or_id.get("username")
            last_name = user_data_or_id.get("last_name")
        else:
            telegram_id = user_data_or_id

        return self._get_or_create_user(
            telegram_id,
            first_name,
            username,
            last_name,
        )

    # ===== GESTIÓN DE USUARIOS =====

    def _get_or_create_user(
        self,
        telegram_id: int,
        first_name: str,
        username: str = None,
        last_name: str = None,
    ) -> User:
        """Obtiene o crea un usuario"""

        user = self.db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
                level=1,
                besitos=0,
                experience=0,
                last_activity=datetime.utcnow(),
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            # Crear estado narrativo inicial
            self.get_or_create_narrative_state(user.id)

            # Log de nuevo usuario
            print(
                f"🆕 Nuevo usuario creado: {first_name} (@{username}) - ID: {user.id}"
            )

        else:
            # Actualizar última actividad y info si cambió
            user.last_activity = datetime.utcnow()
            if user.first_name != first_name:
                user.first_name = first_name
            if user.username != username:
                user.username = username
            self.db.commit()

        return user

    def update_user_activity(self, user_id: int, action: str = None) -> None:
        """Actualiza la actividad del usuario"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_activity = datetime.utcnow()

            # Tracking de acciones para análisis narrativo
            if action:
                narrative_state = self.get_or_create_narrative_state(user_id)
                if not narrative_state.engagement_metrics:
                    narrative_state.engagement_metrics = {}

                if "daily_actions" not in narrative_state.engagement_metrics:
                    narrative_state.engagement_metrics["daily_actions"] = {}

                today = datetime.utcnow().strftime("%Y-%m-%d")
                if today not in narrative_state.engagement_metrics["daily_actions"]:
                    narrative_state.engagement_metrics["daily_actions"][today] = {}

                if (
                    action
                    not in narrative_state.engagement_metrics["daily_actions"][today]
                ):
                    narrative_state.engagement_metrics["daily_actions"][today][
                        action
                    ] = 0

                narrative_state.engagement_metrics["daily_actions"][today][action] += 1

            self.db.commit()

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Obtiene usuario por ID de Telegram"""
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()

    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Obtiene perfil completo del usuario con contexto narrativo"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}

        narrative_state = self.get_or_create_narrative_state(user_id)

        # Calcular estadísticas
        days_registered = (datetime.utcnow() - user.created_at).days
        level_progress = self._calculate_level_progress(user.experience)

        # Generar mensaje de perfil con voz de Lucien
        profile_message = self._generate_profile_message(
            user, narrative_state, days_registered, level_progress
        )

        return {
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "username": user.username,
                "level": user.level,
                "besitos": user.besitos,
                "experience": user.experience,
                "days_registered": days_registered,
            },
            "narrative": {
                "current_level": (
                    narrative_state.current_level.value
                    if narrative_state.current_level
                    else "newcomer"
                ),
                "diana_interest": narrative_state.diana_interest_level,
                "diana_trust": narrative_state.diana_trust_level,
                "archetype": (
                    narrative_state.primary_archetype.value
                    if narrative_state.primary_archetype
                    else "unknown"
                ),
                "has_divan_access": narrative_state.has_divan_access,
                "scenes_completed": (
                    len(narrative_state.scenes_completed)
                    if narrative_state.scenes_completed
                    else 0
                ),
            },
            "progress": level_progress,
            "message": profile_message,
        }

    # ===== GESTIÓN DE ESTADO NARRATIVO =====

    def get_or_create_narrative_state(self, user_id: int) -> UserNarrativeState:
        """Obtiene o crea estado narrativo del usuario"""

        narrative_state = (
            self.db.query(UserNarrativeState)
            .filter(UserNarrativeState.user_id == user_id)
            .first()
        )

        if not narrative_state:
            narrative_state = UserNarrativeState(
                user_id=user_id,
                current_level=NarrativeLevel.NEWCOMER,
                scenes_completed=[],
                choices_made={},
                response_patterns={},
                engagement_metrics={},
                personality_insights={},
                diana_interest_level=0,
                diana_trust_level=0,
                diana_vulnerability_shown=0,
            )
            self.db.add(narrative_state)
            self.db.commit()
            self.db.refresh(narrative_state)

        return narrative_state

    def update_narrative_progress(
        self,
        user_id: int,
        scene_completed: str,
        choice_made: str = None,
        emotional_response: EmotionalResponse = None,
    ) -> Dict[str, Any]:
        """Actualiza progreso narrativo del usuario"""

        narrative_state = self.get_or_create_narrative_state(user_id)
        user = self.db.query(User).filter(User.id == user_id).first()

        # Añadir escena completada
        if not narrative_state.scenes_completed:
            narrative_state.scenes_completed = []
        narrative_state.scenes_completed.append(scene_completed)

        # Registrar elección
        if choice_made:
            if not narrative_state.choices_made:
                narrative_state.choices_made = {}
            narrative_state.choices_made[scene_completed] = choice_made

        # Analizar respuesta emocional
        if emotional_response:
            self._analyze_emotional_response(narrative_state, emotional_response)

        # Evaluar progreso y posibles cambios de nivel
        progression_result = self._evaluate_narrative_progression(narrative_state, user)

        narrative_state.updated_at = datetime.utcnow()
        self.db.commit()

        return progression_result

    def determine_user_archetype(
        self, user_id: int, responses: Dict[str, Any]
    ) -> UserArchetype:
        """Determina arquetipo del usuario basado en respuestas y comportamiento"""

        narrative_state = self.get_or_create_narrative_state(user_id)

        # Puntuaciones por arquetipo
        scores = {
            UserArchetype.EXPLORER: 0,
            UserArchetype.DIRECT: 0,
            UserArchetype.ROMANTIC: 0,
            UserArchetype.ANALYTICAL: 0,
            UserArchetype.PERSISTENT: 0,
            UserArchetype.PATIENT: 0,
        }

        # Analizar respuestas del perfil de deseo
        for question, response in responses.items():
            if question == "approach_style":
                if "details" in response.lower() or "everything" in response.lower():
                    scores[UserArchetype.EXPLORER] += 3
                elif "direct" in response.lower() or "straight" in response.lower():
                    scores[UserArchetype.DIRECT] += 3
                elif "romantic" in response.lower() or "seduction" in response.lower():
                    scores[UserArchetype.ROMANTIC] += 3

            elif question == "response_time":
                if "immediately" in response.lower():
                    scores[UserArchetype.DIRECT] += 2
                elif "think" in response.lower() or "consider" in response.lower():
                    scores[UserArchetype.ANALYTICAL] += 2
                elif "patient" in response.lower() or "wait" in response.lower():
                    scores[UserArchetype.PATIENT] += 2

        # Analizar patrones de comportamiento
        engagement_metrics = narrative_state.engagement_metrics or {}

        # Persistencia: múltiples intentos
        daily_actions = engagement_metrics.get("daily_actions", {})
        total_actions = sum(
            sum(day_actions.values()) for day_actions in daily_actions.values()
        )
        if total_actions > 20:
            scores[UserArchetype.PERSISTENT] += 2

        # Explorer: interacciones con múltiples funciones
        unique_actions = set()
        for day_actions in daily_actions.values():
            unique_actions.update(day_actions.keys())
        if len(unique_actions) > 5:
            scores[UserArchetype.EXPLORER] += 2

        # Determinar arquetipo dominante
        primary_archetype = max(scores, key=scores.get)

        # Determinar arquetipo secundario (si hay empate o puntuación alta)
        scores_sorted = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        secondary_archetype = None
        if len(scores_sorted) > 1 and scores_sorted[1][1] >= scores_sorted[0][1] * 0.8:
            secondary_archetype = scores_sorted[1][0]

        # Actualizar estado narrativo
        narrative_state.primary_archetype = primary_archetype
        narrative_state.secondary_archetype = secondary_archetype

        # Añadir insight de personalidad
        if not narrative_state.personality_insights:
            narrative_state.personality_insights = {}

        narrative_state.personality_insights["archetype_analysis"] = {
            "scores": {arch.value: score for arch, score in scores.items()},
            "determined_at": datetime.utcnow().isoformat(),
            "confidence": scores[primary_archetype] / max(sum(scores.values()), 1),
        }

        self.db.commit()

        return primary_archetype

    # ===== GESTIÓN DE RECURSOS =====

    def add_besitos(
        self, user_id: int, amount: int, reason: str = "System"
    ) -> Dict[str, Any]:
        """Añade besitos al usuario con mensaje de Lucien"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}

        old_amount = user.besitos
        user.besitos += amount
        self.db.commit()

        # Generar mensaje de Lucien
        message = self._generate_besitos_message(
            amount, old_amount, user.besitos, reason, user
        )

        return {
            "success": True,
            "old_amount": old_amount,
            "amount_added": amount,
            "new_amount": user.besitos,
            "message": message,
        }

    def spend_besitos(
        self, user_id: int, amount: int, reason: str = "Purchase"
    ) -> Dict[str, Any]:
        """Gasta besitos del usuario"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}

        if user.besitos < amount:
            return {
                "error": "Besitos insuficientes",
                "required": amount,
                "available": user.besitos,
                "message": self._generate_insufficient_besitos_message(
                    amount, user.besitos, user
                ),
            }

        old_amount = user.besitos
        user.besitos -= amount
        self.db.commit()

        message = self._generate_spend_besitos_message(
            amount, old_amount, user.besitos, reason, user
        )

        return {
            "success": True,
            "old_amount": old_amount,
            "amount_spent": amount,
            "new_amount": user.besitos,
            "message": message,
        }

    def add_experience(
        self, user_id: int, amount: int, reason: str = "Activity"
    ) -> Dict[str, Any]:
        """Añade experiencia y verifica subida de nivel"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}

        old_experience = user.experience
        old_level = user.level

        user.experience += amount

        # Verificar subida de nivel
        new_level = self._calculate_level_from_experience(user.experience)
        level_up = False

        if new_level > old_level:
            user.level = new_level
            level_up = True

        self.db.commit()

        # Generar mensaje
        message = self._generate_experience_message(
            amount,
            old_experience,
            user.experience,
            reason,
            level_up,
            old_level,
            new_level,
            user,
        )

        return {
            "success": True,
            "old_experience": old_experience,
            "amount_added": amount,
            "new_experience": user.experience,
            "level_up": level_up,
            "old_level": old_level,
            "new_level": user.level,
            "message": message,
        }

    # ===== ANÁLISIS Y ESTADÍSTICAS =====

    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas completas del usuario"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}

        narrative_state = self.get_or_create_narrative_state(user_id)

        # Misiones completadas
        missions_completed = (
            self.db.query(Mission)
            .filter(and_(Mission.user_id == user_id, Mission.status == "completed"))
            .count()
        )

        # Días activo
        days_registered = (datetime.utcnow() - user.created_at).days
        days_since_last_activity = (
            (datetime.utcnow() - user.last_activity).days if user.last_activity else 0
        )

        return {
            "user_info": {
                "level": user.level,
                "besitos": user.besitos,
                "experience": user.experience,
                "days_registered": days_registered,
                "days_since_last_activity": days_since_last_activity,
            },
            "narrative_progress": {
                "current_level": narrative_state.current_level.value,
                "diana_interest": narrative_state.diana_interest_level,
                "diana_trust": narrative_state.diana_trust_level,
                "scenes_completed": (
                    len(narrative_state.scenes_completed)
                    if narrative_state.scenes_completed
                    else 0
                ),
                "archetype": (
                    narrative_state.primary_archetype.value
                    if narrative_state.primary_archetype
                    else None
                ),
            },
            "activity": {
                "missions_completed": missions_completed,
                "engagement_score": self._calculate_engagement_score(narrative_state),
            },
        }

    def get_leaderboard(
        self, category: str = "level", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene leaderboard de usuarios"""

        if category == "level":
            user = (
                self.db.query(User)
                .filter(User.is_active == True)
                .order_by(desc(User.level), desc(User.experience))
                .limit(limit)
                .all()
            )
        elif category == "besitos":
            user = (
                self.db.query(User)
                .filter(User.is_active == True)
                .order_by(desc(User.besitos))
                .limit(limit)
                .all()
            )
        elif category == "experience":
            user = (
                self.db.query(User)
                .filter(User.is_active == True)
                .order_by(desc(User.experience))
                .limit(limit)
                .all()
            )
        else:
            return []

        leaderboard = []
        for i, user in enumerate(user, 1):
            narrative_state = self.get_or_create_narrative_state(user.id)
            leaderboard.append(
                {
                    "position": i,
                    "name": user.first_name,
                    "level": user.level,
                    "besitos": user.besitos,
                    "experience": user.experience,
                    "narrative_level": narrative_state.current_level.value,
                    "archetype": (
                        narrative_state.primary_archetype.value
                        if narrative_state.primary_archetype
                        else "unknown"
                    ),
                }
            )

        return leaderboard

    def get_user_detailed_stats(self, user_id: int) -> Dict[str, Any]:
        """Devuelve estadísticas detalladas del usuario (dummy)."""

        # Placeholder: datos simulados
        return {"level": 1, "xp": 100, "missions_completed": 5}

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Devuelve estadísticas básicas del usuario (dummy)."""

        # Placeholder
        return {"health": 100, "energy": 50}

    # ===== MÉTODOS AUXILIARES =====

    def _calculate_level_from_experience(self, experience: int) -> int:
        """Calcula nivel basado en experiencia"""
        # Fórmula: cada nivel requiere 100 * nivel anterior de experiencia
        # Nivel 1: 0-99, Nivel 2: 100-299, Nivel 3: 300-599, etc.

        level = 1
        required_exp = 0

        while experience >= required_exp:
            required_exp += level * 100
            if experience >= required_exp:
                level += 1
            else:
                break

        return level

    def _calculate_level_progress(self, experience: int) -> Dict[str, Any]:
        """Calcula progreso hacia el siguiente nivel"""

        current_level = self._calculate_level_from_experience(experience)

        # Calcular experiencia necesaria para el nivel actual
        exp_for_current_level = sum(i * 100 for i in range(1, current_level))

        # Calcular experiencia necesaria para el siguiente nivel
        exp_for_next_level = exp_for_current_level + (current_level * 100)

        # Progreso en el nivel actual
        exp_in_current_level = experience - exp_for_current_level
        exp_needed_for_next = current_level * 100

        progress_percentage = (exp_in_current_level / exp_needed_for_next) * 100

        return {
            "current_level": current_level,
            "experience_in_level": exp_in_current_level,
            "experience_needed_for_next": exp_needed_for_next - exp_in_current_level,
            "progress_percentage": min(progress_percentage, 100),
            "next_level": current_level + 1,
        }

    def _analyze_emotional_response(
        self, narrative_state: UserNarrativeState, response: EmotionalResponse
    ) -> None:
        """Analiza respuesta emocional para determinar patrones"""

        if not narrative_state.response_patterns:
            narrative_state.response_patterns = {}

        response_key = response.value
        if response_key not in narrative_state.response_patterns:
            narrative_state.response_patterns[response_key] = 0

        narrative_state.response_patterns[response_key] += 1

        # Determinar respuesta emocional dominante
        dominant_response = max(
            narrative_state.response_patterns, key=narrative_state.response_patterns.get
        )
        narrative_state.dominant_emotional_response = EmotionalResponse(
            dominant_response
        )

    def _evaluate_narrative_progression(
        self, narrative_state: UserNarrativeState, user: User
    ) -> Dict[str, Any]:
        """Evalúa si el usuario debe progresar a siguiente nivel narrativo"""

        current_level = narrative_state.current_level
        scenes_completed = (
            len(narrative_state.scenes_completed)
            if narrative_state.scenes_completed
            else 0
        )

        progression_result = {
            "level_changed": False,
            "old_level": current_level.value if current_level else "newcomer",
            "new_level": None,
            "message": None,
            "unlocked_features": [],
        }

        # Lógica de progresión por nivel
        if current_level == NarrativeLevel.NEWCOMER and scenes_completed >= 1:
            new_level = NarrativeLevel.LEVEL_1_KINKY

        elif current_level == NarrativeLevel.LEVEL_1_KINKY and scenes_completed >= 3:
            new_level = NarrativeLevel.LEVEL_2_KINKY_DEEP

        elif (
            current_level == NarrativeLevel.LEVEL_2_KINKY_DEEP and scenes_completed >= 5
        ):
            new_level = NarrativeLevel.LEVEL_3_KINKY_FINAL

        elif (
            current_level == NarrativeLevel.LEVEL_3_KINKY_FINAL
            and self._check_divan_eligibility(narrative_state, user)
        ):
            new_level = NarrativeLevel.LEVEL_4_DIVAN_ENTRY
            narrative_state.has_divan_access = True
            narrative_state.divan_unlock_date = datetime.utcnow()
            progression_result["unlocked_features"].append("divan_access")

        elif (
            current_level == NarrativeLevel.LEVEL_4_DIVAN_ENTRY
            and scenes_completed >= 8
        ):
            new_level = NarrativeLevel.LEVEL_5_DIVAN_DEEP

        elif (
            current_level == NarrativeLevel.LEVEL_5_DIVAN_DEEP
            and narrative_state.diana_trust_level >= 80
        ):
            new_level = NarrativeLevel.LEVEL_6_DIVAN_SUPREME
            progression_result["unlocked_features"].append("inner_circle")

        else:
            return progression_result  # Sin progresión

        # Aplicar progresión
        narrative_state.current_level = new_level
        progression_result["level_changed"] = True
        progression_result["new_level"] = new_level.value
        progression_result["message"] = self._generate_level_progression_message(
            current_level, new_level, user
        )

        return progression_result

    def _check_divan_eligibility(
        self, narrative_state: UserNarrativeState, user: User
    ) -> bool:
        """Verifica elegibilidad para acceso al Diván"""

        return (
            narrative_state.diana_interest_level >= 50
            and narrative_state.diana_trust_level >= 30
            and user.level >= 5
            and len(narrative_state.scenes_completed) >= 5
        )

    def _calculate_engagement_score(self, narrative_state: UserNarrativeState) -> int:
        """Calcula puntuación de engagement del usuario"""

        score = 0

        # Scenes completed
        score += len(narrative_state.scenes_completed) * 10

        # Diana levels
        score += narrative_state.diana_interest_level
        score += narrative_state.diana_trust_level

        # Activity patterns
        engagement_metrics = narrative_state.engagement_metrics or {}
        daily_actions = engagement_metrics.get("daily_actions", {})
        total_actions = sum(
            sum(day_actions.values()) for day_actions in daily_actions.values()
        )
        score += min(total_actions, 100)  # Cap at 100

        return score

    # ===== GENERADORES DE MENSAJES CON VOZ DE LUCIEN =====

    def _generate_profile_message(
        self,
        user: User,
        narrative_state: UserNarrativeState,
        days_registered: int,
        level_progress: Dict,
    ) -> str:
        """Genera mensaje de perfil con voz de Lucien"""

        trust_level = narrative_state.diana_trust_level
        archetype = narrative_state.primary_archetype

        base_message = f"""
{self.lucien.EMOJIS['lucien']} **Perfil de {user.first_name}**

*[Consultando elegantemente sus registros]*

Veamos qué tenemos aquí... {days_registered} días desde que cruzaste el umbral hacia Diana. 

**Tu Progreso:**
🎭 **Nivel Narrativo:** {narrative_state.current_level.value.replace('_', ' ').title()}
👑 **Nivel General:** {user.level} ({level_progress['progress_percentage']:.1f}% hacia nivel {level_progress['next_level']})
💋 **Besitos:** {user.besitos:,}
⚡ **Experiencia:** {user.experience:,}

**Tu Relación con Diana:**
💫 **Interés de Diana:** {narrative_state.diana_interest_level}/100
🗝️ **Confianza de Diana:** {trust_level}/100
        """.strip()

        # Comentario personalizado según el nivel de confianza
        if trust_level >= 80:
            personal_comment = f"""

*[Con respeto genuino]*
Diana confía en ti de maneras que... bueno, que reserva para muy pocos. Has alcanzado un nivel de comprensión que me impresiona incluso a mí.
            """.strip()
        elif trust_level >= 60:
            personal_comment = f"""

*[Con aprobación creciente]*
Diana está genuinamente intrigada por ti. Hay algo en tu aproximación que ha capturado su atención de manera... especial.
            """.strip()
        elif trust_level >= 30:
            personal_comment = f"""

*[Con interés profesional]*
Diana te está evaluando. Cada interacción es una oportunidad de demostrar que mereces más de su atención.
            """.strip()
        else:
            personal_comment = f"""

*[Con aire alentador]*
Diana mantiene su distancia habitual, pero eso no significa que no esté observando. La paciencia es una virtud que ella valora.
            """.strip()

        # Comentario sobre arquetipo
        archetype_comment = ""
        if archetype:
            archetype_comments = {
                UserArchetype.EXPLORER: "*[Con admiración]*\nTu naturaleza exploradora fascina a Diana. Siempre buscando cada detalle, cada secreto...",
                UserArchetype.ROMANTIC: "*[Con sonrisa conocedora]*\nDiana aprecia tu romanticismo auténtico. Hay poesía en cómo te aproximas a ella...",
                UserArchetype.DIRECT: "*[Con respeto]*\nTu honestidad directa ha capturado la atención de Diana. Nada de juegos innecesarios...",
                UserArchetype.ANALYTICAL: "*[Con aprobación intelectual]*\nTu mente analítica intriga a Diana. Buscas comprender, no solo poseer...",
                UserArchetype.PERSISTENT: "*[Con admiración]*\nTu persistencia ha impresionado a Diana. Pocos mantienen esa dedicación...",
                UserArchetype.PATIENT: "*[Con respeto profundo]*\nTu paciencia es una cualidad que Diana encuentra... seductora.",
            }
            archetype_comment = f"""

🎭 **Tu Arquetipo:** {archetype.value.title()}
{archetype_comments.get(archetype, "")}
            """.strip()

        return base_message + personal_comment + archetype_comment

    def _generate_besitos_message(
        self, amount: int, old_amount: int, new_amount: int, reason: str, user: User
    ) -> str:
        """Genera mensaje para ganancia de besitos"""

        if amount >= 100:
            reaction = "*[Con sorpresa genuina]*\n¡Vaya! Una cantidad considerable. Diana debe estar... muy complacida."
        elif amount >= 50:
            reaction = "*[Con aprobación]*\nUna ganancia respetable. Diana aprecia este nivel de dedicación."
        else:
            reaction = "*[Con elegancia]*\nCada besito cuenta. Diana valora incluso los gestos más pequeños."

        return f"""
{self.lucien.EMOJIS['lucien']} **Besitos Recibidos**

{reaction}

💋 **+{amount:,} Besitos** por: {reason}
**Total:** {old_amount:,} → {new_amount:,}

*[Ajustándose los guantes]*
Diana observa cada besito que ganas. Son más que simples tokens... son señales de tu creciente proximidad a ella.
        """.strip()

    def _generate_spend_besitos_message(
        self, amount: int, old_amount: int, new_amount: int, reason: str, user: User
    ) -> str:
        """Genera mensaje para gasto de besitos"""

        return f"""
{self.lucien.EMOJIS['lucien']} **Inversión Realizada**

*[Con aire profesional]*

Has invertido **{amount:,} besitos** en: {reason}
**Saldo:** {old_amount:,} → {new_amount:,}

*[Con sonrisa sutil]*
Diana aprecia a quienes saben cuándo y cómo invertir en acercarse a ella. Cada gasto es una declaración de intenciones.
        """.strip()

    def _generate_insufficient_besitos_message(
        self, required: int, available: int, user: User
    ) -> str:
        """Genera mensaje para besitos insuficientes"""

        return f"""
{self.lucien.EMOJIS['lucien']} **Fondos Insuficientes**

*[Con aire comprensivo]*

Necesitas **{required:,} besitos** pero solo tienes **{available:,}**.

*[Con consejo elegante]*
Diana valora la paciencia y la dedicación. Continúa completando misiones y participando para ganar más besitos. Cada esfuerzo te acerca más a ella.

**Diferencia:** {required - available:,} besitos
        """.strip()

    def _generate_experience_message(
        self,
        amount: int,
        old_exp: int,
        new_exp: int,
        reason: str,
        level_up: bool,
        old_level: int,
        new_level: int,
        user: User,
    ) -> str:
        """Genera mensaje para ganancia de experiencia"""

        base_message = f"""
{self.lucien.EMOJIS['lucien']} **Crecimiento Personal**

*[Con satisfacción]*

⚡ **+{amount} Experiencia** por: {reason}
**Total:** {old_exp:,} → {new_exp:,}
        """.strip()

        if level_up:
            level_message = f"""

🎉 **¡SUBIDA DE NIVEL!**

*[Con ceremonia elegante]*

¡Has ascendido del **Nivel {old_level}** al **Nivel {new_level}**!

Diana ha notado tu crecimiento. Cada nivel que alcanzas te permite acceder a nuevas profundidades de conexión con ella.

*[Con orgullo discreto]*
El crecimiento personal es lo que más aprecia Diana. No solo buscas placeres superficiales, sino verdadera evolución.
            """.strip()

            return base_message + level_message

        return (
            base_message
            + "\n\n*[Con aliento]*\nCada experiencia te hace más digno de la atención de Diana."
        )

    def _generate_level_progression_message(
        self, old_level: NarrativeLevel, new_level: NarrativeLevel, user: User
    ) -> str:
        """Genera mensaje para progresión narrativa"""

        progression_messages = {
            NarrativeLevel.LEVEL_1_KINKY: f"""
{self.lucien.EMOJIS['lucien']} **Bienvenido a Los Kinkys**

*[Con ceremonia]*

{user.first_name}, has dado el primer paso real hacia Diana. Ya no eres solo un observador... eres un participante.

*[Con elegancia]*
En Los Kinkys, Diana comenzará a evaluarte más profundamente. Cada acción, cada elección... todo cuenta.
            """.strip(),
            NarrativeLevel.LEVEL_4_DIVAN_ENTRY: f"""
{self.lucien.EMOJIS['diana']} **Acceso al Diván Desbloqueado**

*[Con ceremonia solemne]*

{user.first_name}... Diana ha decidido que mereces conocer su espacio más íntimo.

**Bienvenido al Diván.**

*[Con respeto genuino]*
Pocos llegan hasta aquí. Has demostrado comprensión, paciencia y una conexión auténtica que Diana encuentra... irresistible.

**Nuevas características desbloqueadas:**
🔮 Interacciones más íntimas con Diana
👑 Subastas VIP exclusivas  
💫 Contenido que Diana no comparte con cualquiera
            """.strip(),
            NarrativeLevel.LEVEL_6_DIVAN_SUPREME: f"""
{self.lucien.EMOJIS['intimate']} **Círculo Íntimo de Diana**

*[Con reverencia]*

{user.first_name}... has alcanzado algo extraordinario.

Diana ha decidido incluirte en su **Círculo Íntimo**.

*[Con emoción contenida]*
En todos mis años como su mayordomo, he visto a muy pocos llegar a este nivel de comprensión y conexión mutua.

**Felicidades. Has logrado lo que muchos buscan pero pocos encuentran: verdadera intimidad con Diana.**
            """.strip(),
        }

        return progression_messages.get(
            new_level, f"Has progresado a: {new_level.value}"
        )
   