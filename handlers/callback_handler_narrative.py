from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.user_service import UserService
from utils.lucien_voice_enhanced import LucienVoiceEnhanced, InteractionPattern, UserArchetype
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CallbackHandlerNarrative:
    """CallbackHandler con sistema narrativo inmersivo integrado"""

    def __init__(self):
        try:
            self.user_service = UserService()
            self.lucien = LucienVoiceEnhanced()
            logger.info("✅ CallbackHandlerNarrative inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando CallbackHandlerNarrative: {e}")
            raise

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Router principal con narrativa inmersiva"""
        
        try:
            query = update.callback_query
            await query.answer()

            user_data = {
                "telegram_id": query.from_user.id,
                "username": query.from_user.username,
                "first_name": query.from_user.first_name or "Usuario",
                "last_name": query.from_user.last_name,
            }

            logger.info(f"🔍 Callback narrativo: {query.data} de {user_data['first_name']}")

            # Obtener usuario y estado narrativo
            user = self.user_service.get_or_create_user(user_data)
            narrative_state = self.user_service.get_or_create_narrative_state(user.id)

            callback_data = query.data

            # === NARRATIVA NIVEL 1 ===
            if callback_data == "discover_more" or callback_data == "level1_scene2":
                await self._handle_level1_scene2(update, context, user, narrative_state)
            elif callback_data == "react_to_channel":
                await self._handle_reaction_challenge(update, context, user, narrative_state)
            elif callback_data.startswith("reaction_"):
                await self._handle_reaction_result(update, context, user, narrative_state, callback_data)
            
            # === NAVEGACIÓN NARRATIVA ===
            elif callback_data == "back_to_story":
                await self._handle_back_to_current_scene(update, context, user, narrative_state)
            elif callback_data == "continue_journey":
                await self._handle_continue_narrative(update, context, user, narrative_state)
            
            # === CALLBACKS EXISTENTES (conservados) ===
            elif callback_data == "profile":
                await self._show_profile_narrative(update, context, user, narrative_state)
            elif callback_data == "missions":
                await self._show_missions_narrative(update, context, user, narrative_state)
            elif callback_data == "back_to_menu":
                await self._show_main_menu_narrative(update, context, user, narrative_state)
            
            # === CATCH-ALL ===
            else:
                await self._handle_unknown_callback_narrative(update, context, callback_data)

        except Exception as e:
            logger.error(f"❌ Error en handle_callback narrativo: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    # === NIVEL 1 - IMPLEMENTACIÓN COMPLETA ===

    async def _handle_level1_scene2(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Nivel 1, Escena 2 - Lucien presenta el primer desafío"""
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')
            
            # Detectar arquetipo del usuario (simplificado por ahora)
            user_archetype = self._detect_user_archetype(user, narrative_state)
            
            # Obtener mensaje de Lucien
            lucien_message = self.lucien.get_lucien_level1_scene2_intro(first_name, user_archetype)

            # Botones para el desafío
            keyboard = [
                [InlineKeyboardButton("💫 Reaccionar al último mensaje", callback_data="react_to_channel")],
                [InlineKeyboardButton("🤔 ¿Por qué debo reaccionar?", callback_data="why_react")],
                [InlineKeyboardButton("😏 No me gusta que me ordenen", callback_data="rebellious_response")],
                [InlineKeyboardButton("⬅️ Volver con Diana", callback_data="back_to_diana")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                lucien_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

            # Actualizar estado narrativo
            await self._update_narrative_progress(user.id, "level1_scene2_presented")

        except Exception as e:
            logger.error(f"❌ Error en _handle_level1_scene2: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_reaction_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Maneja el desafío de reacción al canal"""
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')

            # Simular el desafío de reacción
            challenge_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire expectante]*

Perfecto, {first_name}. Ahora viene la parte... interesante.

*[Señalando hacia el canal]*

Ve al último mensaje del canal y reacciona. Pero recuerda...

{self.lucien.EMOJIS['diana']} *[Diana susurra desde las sombras]*

"*No es solo una reacción. Es una declaración de intención.*"

*[Con misterio]*

"*Elige el emoji que mejor represente por qué estás aquí.*"

⏰ **Tienes 5 minutos para decidir.**

Diana estará... observando.
            """.strip()

            # Botones de simulación (en implementación real sería tracking del canal)
            keyboard = [
                [InlineKeyboardButton("❤️ Reaccionar con corazón", callback_data="reaction_heart")],
                [InlineKeyboardButton("🔥 Reaccionar con fuego", callback_data="reaction_fire")],
                [InlineKeyboardButton("👀 Reaccionar con ojos", callback_data="reaction_eyes")],
                [InlineKeyboardButton("⏰ Necesito más tiempo", callback_data="reaction_delay")],
                [InlineKeyboardButton("❌ No quiero reaccionar", callback_data="reaction_refuse")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                challenge_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

            # Guardar timestamp del desafío
            await self._save_challenge_timestamp(user.id, "reaction_challenge")

        except Exception as e:
            logger.error(f"❌ Error en _handle_reaction_challenge: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_reaction_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any, callback_data: str) -> None:
        """Procesa el resultado de la reacción del usuario"""
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')
            
            # Extraer tipo de reacción
            reaction_type = callback_data.replace("reaction_", "")
            
            # Calcular tiempo de respuesta
            reaction_time = await self._calculate_reaction_time(user.id, "reaction_challenge")
            
            # Determinar patrón de reacción
            if reaction_time < 30:  # Menos de 30 segundos
                time_pattern = "immediate"
            elif reaction_time < 180:  # Menos de 3 minutos
                time_pattern = "thoughtful"
            else:
                time_pattern = "delayed"

            # Obtener respuesta de Diana según la reacción
            if reaction_type in ["heart", "fire", "eyes"]:
                diana_response = self.lucien.get_diana_reaction_response(time_pattern, first_name)
            elif reaction_type == "delay":
                diana_response = self._get_delay_response(first_name)
            else:  # refuse
                diana_response = self._get_refusal_response(first_name)

            # Mostrar respuesta de Diana
            full_message = f"""
{diana_response['diana_message']}

{diana_response['lucien_comment']}

{self._get_reward_message(diana_response['reward_type'])}
            """.strip()

            # Botones según el resultado
            if reaction_type != "refuse":
                keyboard = [
                    [InlineKeyboardButton("🎁 Abrir Mochila del Viajero", callback_data="open_traveler_bag")],
                    [InlineKeyboardButton("🗺️ Examinar la pista", callback_data="examine_clue")],
                    [InlineKeyboardButton("💬 Hablar con Diana", callback_data="talk_to_diana")],
                    [InlineKeyboardButton("➡️ Continuar el viaje", callback_data="continue_journey")],
                ]
            else:
                keyboard = [
                    [InlineKeyboardButton("🔄 Reconsiderar mi decisión", callback_data="react_to_channel")],
                    [InlineKeyboardButton("💭 Necesito pensar más", callback_data="thinking_time")],
                    [InlineKeyboardButton("⬅️ Volver al inicio", callback_data="back_to_menu")],
                ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                full_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

            # Actualizar progreso narrativo
            await self._update_narrative_progress(user.id, f"level1_reaction_{reaction_type}")
            await self._update_user_archetype(user.id, reaction_type, time_pattern)

        except Exception as e:
            logger.error(f"❌ Error en _handle_reaction_result: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    # === MÉTODOS AUXILIARES NARRATIVOS ===

    def _detect_user_archetype(self, user: Any, narrative_state: Any) -> UserArchetype:
        """Detecta el arquetipo del usuario basado en comportamiento"""
        
        # Lógica simplificada - en implementación real sería más sofisticada
        try:
            # Analizar historial de interacciones
            interaction_count = getattr(narrative_state, 'interaction_count', 0)
            
            if interaction_count < 3:
                return UserArchetype.UNDEFINED
            
            # Por ahora retornamos Explorer como default
            return UserArchetype.EXPLORER
            
        except Exception as e:
            logger.error(f"Error detectando arquetipo: {e}")
            return UserArchetype.UNDEFINED

    async def _calculate_reaction_time(self, user_id: int, challenge_type: str) -> int:
        """Calcula el tiempo de reacción del usuario"""
        
        try:
            # En implementación real, obtendríamos el timestamp guardado
            # Por ahora simulamos
            return 45  # 45 segundos como ejemplo
            
        except Exception as e:
            logger.error(f"Error calculando tiempo de reacción: {e}")
            return 60

    async def _save_challenge_timestamp(self, user_id: int, challenge_type: str) -> None:
        """Guarda timestamp del desafío"""
        
        try:
            # En implementación real, guardaríamos en BD
            timestamp = datetime.utcnow()
            logger.info(f"📝 Challenge timestamp guardado: {user_id} - {challenge_type} - {timestamp}")
            
        except Exception as e:
            logger.error(f"Error guardando timestamp: {e}")

    async def _update_narrative_progress(self, user_id: int, progress_key: str) -> None:
        """Actualiza el progreso narrativo del usuario"""
        
        try:
            # En implementación real, actualizaríamos UserNarrativeState
            logger.info(f"📈 Progreso narrativo actualizado: {user_id} - {progress_key}")
            
        except Exception as e:
            logger.error(f"Error actualizando progreso narrativo: {e}")

    async def _update_user_archetype(self, user_id: int, reaction_type: str, time_pattern: str) -> None:
        """Actualiza el arquetipo del usuario basado en su comportamiento"""
        
        try:
            # Lógica para determinar arquetipo basado en reacción
            if time_pattern == "immediate" and reaction_type in ["heart", "fire"]:
                archetype = UserArchetype.DIRECT
            elif time_pattern == "thoughtful":
                archetype = UserArchetype.ANALYTICAL
            elif reaction_type == "eyes":
                archetype = UserArchetype.EXPLORER
            else:
                archetype = UserArchetype.UNDEFINED

            logger.info(f"🎭 Arquetipo actualizado: {user_id} - {archetype.value}")
            
        except Exception as e:
            logger.error(f"Error actualizando arquetipo: {e}")

    def _get_delay_response(self, first_name: str) -> Dict[str, str]:
        """Respuesta cuando el usuario pide más tiempo"""
        
        return {
            "diana_message": f"""
{self.lucien.EMOJIS['diana']} *[Con comprensión paciente]*

{first_name}... necesitas más tiempo.

*[Con sabiduría]*

No hay prisa en las decisiones que importan. Tómate el tiempo que necesites.

*[Con misterio]*

Estaré aquí cuando estés listo para dar ese paso.""",
            
            "lucien_comment": f"""
{self.lucien.EMOJIS['lucien']} *[Con aprobación reluctante]*

"*Al menos {first_name} es honesto sobre sus... limitaciones temporales.*"

*[Con aire profesional]*

"*Diana aprecia la honestidad más que la falsa bravura.*"
""",
            "reward_type": "patience_acknowledged"
        }

    def _get_refusal_response(self, first_name: str) -> Dict[str, str]:
        """Respuesta cuando el usuario se niega a reaccionar"""
        
        return {
            "diana_message": f"""
{self.lucien.EMOJIS['diana']} *[Con decepción sutil]*

{first_name}... decidiste no participar.

*[Con aire reflexivo]*

Interesante. A veces la resistencia dice más que la obediencia.

*[Con
