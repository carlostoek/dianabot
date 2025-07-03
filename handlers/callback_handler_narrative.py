from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.user_service import UserService
from services.mission_service import MissionService
from utils.lucien_voice_enhanced import (
    LucienVoiceEnhanced,
    InteractionPattern,
    UserArchetype,
)
from services.admin_service import AdminService
from models.admin import AdminPermission, AdminLevel
from utils.decorators import admin_required, super_admin_only, admin_only
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CallbackHandlerNarrative:
    """CallbackHandler con sistema narrativo inmersivo integrado"""

    def __init__(self):
        try:
            self.user_service = UserService()
            self.mission_service = MissionService()
            self.lucien = LucienVoiceEnhanced()
            self.admin_service = AdminService()  # ✅ NUEVO
            logger.info("✅ CallbackHandlerNarrative inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando CallbackHandlerNarrative: {e}")
            raise

    async def start_narrative(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Inicia la narrativa y asigna misiones diarias"""

        user_id = update.effective_user.id

        # Lógica inicial de narrativa (placeholder)

        self.mission_service.create_daily_missions_for_user(user_id)

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
                await self._handle_missions_original(update, context, user, narrative_state)
            elif callback_data == "back_to_menu":
                await self._show_main_menu_narrative(update, context, user, narrative_state)

            # === CALLBACKS DEL SISTEMA ORIGINAL ===
            elif callback_data == "premium":
                await self._handle_premium_original(update, context, user, narrative_state)
            elif callback_data == "continue_story":
                await self._handle_continue_story(update, context, user, narrative_state)

            # === CALLBACKS NARRATIVOS ===
            elif callback_data == "narrative_progress":
                await self._handle_narrative_progress(update, context, user, narrative_state)
            elif callback_data == "review_clues":
                await self._handle_unknown_callback_narrative(update, context, "review_clues")
            elif callback_data == "talk_to_diana":
                await self._handle_unknown_callback_narrative(update, context, "talk_to_diana")
            elif callback_data == "settings":
                await self._handle_unknown_callback_narrative(update, context, "settings")

            # === CALLBACKS DE ADMINISTRACIÓN ===
            elif callback_data == "admin_panel":
                await self._show_admin_panel(update, context, user, narrative_state)
            elif callback_data == "generate_vip_token":
                await self._handle_generate_vip_token(update, context, user, narrative_state)
            elif callback_data == "manage_channels":
                await self._handle_manage_channels(update, context, user, narrative_state)
            elif callback_data == "admin_analytics":
                await self._handle_admin_analytics(update, context, user, narrative_state)
            elif callback_data == "manage_admins":
                await self._handle_manage_admins(update, context, user, narrative_state)
            elif callback_data.startswith("admin_"):
                await self._handle_admin_action(update, context, user, narrative_state, callback_data)

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

*[Con paciencia enigmática]*

Pero recuerda... algunas puertas solo se abren una vez.""",

            "lucien_comment": f"""
{self.lucien.EMOJIS['lucien']} *[Con sarcasmo palpable]*

"*Ah, qué sorpresa... otro que se paraliza ante el primer desafío real.*"

*[Con desdén elegante]*

"*Diana es paciente, yo... considerably less so.*"
""",
            "reward_type": "refusal_consequence"
        }

    def _get_reward_message(self, reward_type: str) -> str:
        """Genera mensaje de recompensa según el tipo"""
        
        reward_content = self.lucien.get_reward_content(reward_type, UserArchetype.UNDEFINED)
        
        return f"""
🎁 **{reward_content['title']}**

*{reward_content['description']}*

**Contenido:** {reward_content['content']}
**Rareza:** {reward_content['rarity']}
        """.strip()

    # === CALLBACKS NARRATIVOS ADICIONALES ===

    async def _handle_open_traveler_bag(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Maneja la apertura de la Mochila del Viajero"""
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')

            bag_message = f"""
{self.lucien.EMOJIS['elegant']} **Mochila del Viajero Abierta**

{self.lucien.EMOJIS['lucien']} *[Con ceremonia]*

"*Veamos qué ha preparado Diana para ti, {first_name}...*"

*[Abriendo la mochila con dramatismo]*

🗺️ **Fragmento de Mapa Misterioso**
*Una pieza de pergamino antiguo con símbolos extraños*

📜 **Nota Personal de Diana:**
*"Para {first_name}: Este mapa está incompleto... intencionalmente. La otra mitad existe donde las reglas cambian. - D"*

🔑 **Llave Simbólica**
*Una pequeña llave dorada con la inscripción: "Para puertas que no todos pueden ver"*

{self.lucien.EMOJIS['diana']} *[Diana aparece brevemente]*

"*La verdadera pregunta no es qué contiene la mochila... sino si estás preparado para usar lo que hay dentro.*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("🗺️ Examinar el mapa", callback_data="examine_map")],
                [InlineKeyboardButton("📜 Leer nota completa", callback_data="read_diana_note")],
                [InlineKeyboardButton("🔑 Inspeccionar la llave", callback_data="inspect_key")],
                [InlineKeyboardButton("💭 ¿Qué significa todo esto?", callback_data="ask_meaning")],
                [InlineKeyboardButton("➡️ Continuar el viaje", callback_data="continue_journey")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                bag_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_open_traveler_bag: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_examine_map(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Examina el fragmento de mapa"""
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')

            map_message = f"""
🗺️ **Fragmento de Mapa Analizado**

{self.lucien.EMOJIS['lucien']} *[Con aire de detective]*

"*Interesante, {first_name}... este mapa no señala un lugar físico.*"

*[Examinando con lupa imaginaria]*

**Lo que puedes ver:**
• Símbolos que parecen... emociones
• Caminos que se bifurcan según decisiones
• Una X marcada en un lugar llamado "Comprensión Mutua"
• Coordenadas que no son geográficas: "Vulnerabilidad 40°, Confianza 60°"

{self.lucien.EMOJIS['diana']} *[Susurrando desde las sombras]*

"*Este mapa no te lleva a un lugar, {first_name}... te lleva a un estado de ser.*"

*[Con misterio profundo]*

"*Y la otra mitad... solo aparece cuando demuestras que puedes manejar esta.*"

{self.lucien.EMOJIS['lucien']} *[Con sarcasmo]*

"*Típico de Diana... hasta sus mapas son... filosóficos.*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("🧭 ¿Cómo uso este mapa?", callback_data="how_to_use_map")],
                [InlineKeyboardButton("❓ ¿Dónde está la otra mitad?", callback_data="where_other_half")],
                [InlineKeyboardButton("💡 Creo que entiendo", callback_data="understand_map")],
                [InlineKeyboardButton("🔙 Volver a la mochila", callback_data="open_traveler_bag")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                map_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_examine_map: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    # === MENÚS PRINCIPALES CON NARRATIVA ===

    async def _show_main_menu_narrative(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Menú principal con contexto narrativo"""
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')
            
            # Detectar progreso narrativo actual
            current_level = getattr(narrative_state, 'current_level', 'newcomer')
            
            # Mensaje adaptativo según progreso
            if current_level == 'newcomer':
                menu_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de recepcionista sarcástico]*

"*Oh, {first_name}... de vuelta al lobby. Qué... predecible.*"

*[Con eficiencia profesional]*

Diana está observando tu... progreso. O la falta de él.

¿Qué intentarás ahora?
                """.strip()
            else:
                menu_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con reconocimiento reluctante]*

"*{first_name}... has progresado más de lo que esperaba.*"

*[Con aire conspirativo]*

Diana ha estado... comentando sobre ti. Eso es... unusual.

¿Continuamos con tu desarrollo personal?
                """.strip()

            # Botones adaptativos según progreso
            keyboard = [
                [InlineKeyboardButton("👤 Mi Progreso Narrativo", callback_data="narrative_progress")],
                [InlineKeyboardButton("🎭 Continuar Historia", callback_data="continue_story")],
                [InlineKeyboardButton("🗺️ Revisar Pistas", callback_data="review_clues")],
                [InlineKeyboardButton("💬 Hablar con Diana", callback_data="talk_to_diana")],
                [InlineKeyboardButton("⚙️ Configuración", callback_data="settings")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                menu_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _show_main_menu_narrative: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _show_profile_narrative(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Perfil con contexto narrativo"""
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')
            
            # Obtener datos del usuario
            level = getattr(user, 'level', 1)
            besitos = getattr(user, 'besitos', 0)
            trust_level = getattr(narrative_state, 'diana_trust_level', 0)
            
            profile_message = f"""
{self.lucien.EMOJIS['lucien']} **Expediente Personal de {first_name}**

*[Consultando un elegante dossier]*

"*Veamos tu... evolución hasta ahora.*"

📊 **Estadísticas de Progreso:**
• **Nivel Narrativo:** {level}
• **Besitos de Diana:** {besitos} 💋
• **Confianza de Diana:** {trust_level}/100
• **Arquetipo Detectado:** {self._get_user_archetype_display(narrative_state)}

🎭 **Análisis de Personalidad:**
{self._get_personality_analysis(narrative_state, trust_level)}

{self.lucien.EMOJIS['diana']} *[Diana observa desde las sombras]*

"*{first_name} está... {self._get_diana_opinion_narrative(trust_level)}*"

*[Con aire evaluativo]*

"*Pero aún hay... mucho camino por recorrer.*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("📈 Ver Progreso Detallado", callback_data="detailed_progress")],
                [InlineKeyboardButton("🎭 Mi Arquetipo", callback_data="my_archetype")],
                [InlineKeyboardButton("💭 ¿Qué piensa Diana de mí?", callback_data="diana_opinion")],
                [InlineKeyboardButton("🎯 ¿Cómo mejorar?", callback_data="how_to_improve")],
                [InlineKeyboardButton("⬅️ Volver al menú", callback_data="back_to_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                profile_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _show_profile_narrative: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    # === MÉTODOS AUXILIARES PARA NARRATIVA ===

    def _get_user_archetype_display(self, narrative_state: Any) -> str:
        """Obtiene el arquetipo del usuario para mostrar"""
        
        archetype = getattr(narrative_state, 'primary_archetype', 'undefined')
        
        archetype_names = {
            'explorer': 'El Explorador 🔍',
            'direct': 'El Directo ⚡',
            'romantic': 'El Romántico 💫',
            'analytical': 'El Analítico 🧠',
            'persistent': 'El Persistente 💪',
            'patient': 'El Paciente 🕰️',
            'undefined': 'En evaluación... 🤔'
        }
        
        return archetype_names.get(archetype, 'Misterioso 🎭')

    def _get_personality_analysis(self, narrative_state: Any, trust_level: int) -> str:
        """Genera análisis de personalidad"""
        
        if trust_level < 20:
            return "*Personalidad aún en desarrollo. Diana necesita más datos para un análisis completo.*"
        elif trust_level < 50:
            return "*Muestra signos prometedores de comprensión emocional. Diana está... intrigada.*"
        elif trust_level < 80:
            return "*Demuestra madurez emocional notable. Diana ha comenzado a... confiar.*"
        else:
            return "*Excepcional comprensión de la complejidad humana. Diana está genuinamente impresionada.*"

    def _get_diana_opinion_narrative(self, trust_level: int) -> str:
        """Opinión narrativa de Diana según nivel de confianza"""
        
        if trust_level < 20:
            return "evaluando su potencial"
        elif trust_level < 50:
            return "comenzando a interesarse"
        elif trust_level < 80:
            return "genuinamente intrigada"
        else:
            return "profundamente fascinada"

    async def _send_error_message_narrative(self, update: Update) -> None:
        """Mensaje de error con narrativa"""
        
        error_message = self.lucien.get_error_message("narrativa")
        
        try:
            await update.callback_query.edit_message_text(
                error_message, 
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error enviando mensaje de error narrativo: {e}")

    async def _handle_unknown_callback_narrative(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
        """Maneja callbacks desconocidos con narrativa"""
        
        unknown_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con exasperación elegante]*

"*Oh, qué sorpresa... {callback_data} no está implementado yet.*"

*[Con sarcasmo profesional]*

"*Diana me pide que te informe que esa funcionalidad está... en desarrollo.*"

*[Con aire condescendiente]*

"*Mientras tanto, perhaps try something that actually works?*"
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🔙 Volver al menú", callback_data="back_to_menu")],
            [InlineKeyboardButton("🎭 Continuar historia", callback_data="continue_story")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            unknown_message, 
            reply_markup=reply_markup, 
            parse_mode="Markdown"
        )

    # === CALLBACKS NARRATIVOS FALTANTES ===

    async def _handle_narrative_progress(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Maneja 'narrative_progress'"""

        progress_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de evaluador]*

"*Tu progreso narrativo... veamos...*"

📊 **Estado Actual:**
• Nivel: Principiante
• Escenas completadas: 1/10
• Comprensión de Diana: 15%

*[Con sarcasmo]*

"*Básicamente... acabas de empezar.*"
        """.strip()

        keyboard = [
            [InlineKeyboardButton("⬅️ Volver", callback_data="back_to_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            progress_message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def _handle_continue_story(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Maneja 'continue_story'"""

        story_message = f"""
{self.lucien.EMOJIS['diana']} *[Diana aparece con misterio]*

"*¿Listo para continuar nuestra historia?*"

*[Con aire seductor]*

"*Cada paso que das me revela más sobre ti...*"
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🚪 Descubrir más", callback_data="level1_scene2")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="back_to_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            story_message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    # === MÉTODOS FALTANTES - AGREGAR AL FINAL DE LA CLASE ===

    async def _handle_missions_original(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Maneja el callback 'missions' del sistema original"""

        try:
            first_name = getattr(user, 'first_name', 'Usuario')

            missions_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de supervisor reluctante]*

"*Oh, {first_name}... quieres ver tus 'misiones'. Qué... ambicioso.*"

*[Consultando una lista elegante]*

🎯 **Misiones Disponibles:**

🌅 **Misión Diaria**
• Interactuar con Diana hoy
• Recompensa: 10 Besitos 💋
• Estado: Disponible

🎭 **Conocer a Diana**
• Explorar todas las introducciones
• Recompensa: 25 Besitos + Acceso especial
• Estado: En progreso

💎 **Camino al VIP**
• Completar 5 misiones principales
• Recompensa: Token VIP gratuito
• Estado: 0/5

{self.lucien.EMOJIS['diana']} *[Diana susurra desde las sombras]*

"*Cada misión completada me acerca más a ti, {first_name}...*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("✅ Completar Diaria", callback_data="complete_daily")],
                [InlineKeyboardButton("🎭 Explorar Introducciones", callback_data="intro_diana")],
                [InlineKeyboardButton("🔄 Actualizar Progreso", callback_data="refresh_missions")],
                [InlineKeyboardButton("⬅️ Volver al Menú", callback_data="back_to_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                missions_message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_missions_original: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_premium_original(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Maneja el callback 'premium' del sistema original"""

        try:
            first_name = getattr(user, 'first_name', 'Usuario')

            premium_message = f"""
{self.lucien.EMOJIS['diana']} *[Diana aparece con aire exclusivo]*

"*{first_name}... quieres ver mi contenido más... íntimo.*"

*[Con sonrisa seductora]*

"*No todo lo que creo está disponible para todos. Las mejores piezas, las más personales... requieren verdadera dedicación.*"

💎 **Contenido Premium Disponible:**

📸 **Fotos Exclusivas**
• Sesión "Elegancia Nocturna"
• Precio: 50 Besitos 💋
• Estado: Disponible

🎥 **Videos Personalizados**
• Saludo con tu nombre
• Precio: 100 Besitos 💋
• Estado: Disponible

✨ **Experiencias VIP**
• Chat privado 30 min
• Precio: 200 Besitos 💋
• Estado: Solo VIP

{self.lucien.EMOJIS['lucien']} *[Con aire profesional]*

"*Los precios reflejan la exclusividad, {first_name}.*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("👑 Obtener Acceso VIP", callback_data="get_vip")],
                [InlineKeyboardButton("📸 Vista Previa", callback_data="vip_preview")],
                [InlineKeyboardButton("💬 Testimonios", callback_data="testimonials")],
                [InlineKeyboardButton("💰 ¿Cómo ganar besitos?", callback_data="earn_besitos")],
                [InlineKeyboardButton("⬅️ Volver al Menú", callback_data="back_to_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                premium_message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_premium_original: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    # === MÉTODOS DE ADMINISTRACIÓN ===

    async def _show_admin_panel(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
    ) -> None:
        """Muestra panel de administración"""

        try:
            user_telegram_id = update.effective_user.id
            first_name = getattr(user, "first_name", "Usuario")

            if not self.admin_service.is_admin(user_telegram_id):
                await self._send_no_admin_access_message(update, first_name)
                return

            admin = self.admin_service.get_admin(user_telegram_id)
            admin_stats = self.admin_service.get_admin_statistics(user_telegram_id)

            admin_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de autoridad]*

"*Ah, {first_name}... bienvenido al centro de control.*"

👑 **Panel de Administración**

**Tu información:**
• Nivel: {admin.admin_level.value.title()}
• Comandos usados: {admin_stats['activity']['total_commands']}
• Última actividad: {admin.last_activity.strftime('%d/%m/%Y %H:%M') if admin.last_activity else 'N/A'}

**Permisos disponibles:**
{self._format_admin_permissions(admin)}

*[Con aire profesional]*

"*¿Qué deseas administrar hoy?*"
            """.strip()

            keyboard = []
            if admin.can_generate_vip_tokens:
                keyboard.append([InlineKeyboardButton("🎫 Generar Token VIP", callback_data="generate_vip_token")])
            if admin.can_manage_channels:
                keyboard.append([InlineKeyboardButton("📺 Gestionar Canales", callback_data="manage_channels")])
            if admin.can_access_analytics:
                keyboard.append([InlineKeyboardButton("📊 Ver Analytics", callback_data="admin_analytics")])
            if admin.can_manage_users:
                keyboard.append([InlineKeyboardButton("👥 Gestionar Usuarios", callback_data="manage_users")])
            if admin.can_manage_admins:
                keyboard.append([InlineKeyboardButton("👑 Gestionar Admins", callback_data="manage_admins")])

            keyboard.append([InlineKeyboardButton("📋 Mi Actividad", callback_data="admin_my_activity")])
            keyboard.append([InlineKeyboardButton("⬅️ Volver al Menú", callback_data="back_to_menu")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                admin_message,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"❌ Error en _show_admin_panel: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_generate_vip_token(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
    ) -> None:
        """Maneja la generación de tokens VIP"""

        try:
            user_telegram_id = update.effective_user.id
            first_name = getattr(user, 'first_name', 'Usuario')

            if not self.admin_service.has_permission(
                user_telegram_id, AdminPermission.GENERATE_VIP_TOKENS
            ):
                await self._send_no_permission_message(update, first_name, "generar tokens VIP")
                return

            can_generate = self.admin_service.can_perform_action(
                user_telegram_id, "generate_vip_token"
            )
            if not can_generate["allowed"]:
                await self._send_limit_reached_message(update, first_name, can_generate["reason"])
                return

            token_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de autoridad]*

"*{first_name}, vas a generar un token VIP.*"

🎫 **Generador de Tokens VIP**

*[Con aire profesional]*

"*Selecciona el tipo de token que deseas crear:*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("⚡ Token Rápido (24h)", callback_data="admin_token_quick")],
                [InlineKeyboardButton("📅 Token Semanal (7 días)", callback_data="admin_token_weekly")],
                [InlineKeyboardButton("⬅️ Volver al Panel", callback_data="admin_panel")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                token_message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_generate_vip_token: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_manage_channels(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
    ) -> None:
        """Maneja la gestión de canales"""

        try:
            user_telegram_id = update.effective_user.id
            first_name = getattr(user, "first_name", "Usuario")

            if not self.admin_service.has_permission(
                user_telegram_id, AdminPermission.MANAGE_CHANNELS
            ):
                await self._send_no_permission_message(update, first_name, "gestionar canales")
                return

            channels_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de supervisor]*

"*{first_name}, aquí tienes el control de los canales.*"

📺 **Gestión de Canales**

**Canales activos:**
• Canal Gratuito: Los Kinkys
• Canal VIP: El Diván
• Solicitudes pendientes: [Número]

*[Con aire eficiente]*

"*¿Qué deseas hacer?*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("📋 Ver Solicitudes Pendientes", callback_data="admin_pending_requests")],
                [InlineKeyboardButton("✅ Aprobar Solicitudes", callback_data="admin_approve_requests")],
                [InlineKeyboardButton("❌ Rechazar Solicitudes", callback_data="admin_reject_requests")],
                [InlineKeyboardButton("📊 Estadísticas de Canales", callback_data="admin_channel_stats")],
                [InlineKeyboardButton("⚙️ Configurar Auto-aprobación", callback_data="admin_auto_approval")],
                [InlineKeyboardButton("⬅️ Volver al Panel", callback_data="admin_panel")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                channels_message,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_manage_channels: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_admin_analytics(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
    ) -> None:
        """Muestra analytics para administradores"""

        try:
            user_telegram_id = update.effective_user.id
            first_name = getattr(user, "first_name", "Usuario")

            if not self.admin_service.has_permission(
                user_telegram_id, AdminPermission.ACCESS_ANALYTICS
            ):
                await self._send_no_permission_message(update, first_name, "acceder a analytics")
                return

            analytics_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire analítico]*

"*{first_name}, aquí tienes los números que importan.*"

📊 **Analytics del Sistema**

**Usuarios:**
• Total de usuarios: [Número]
• Usuarios activos (7 días): [Número]
• Usuarios VIP: [Número]

**Actividad:**
• Misiones completadas hoy: [Número]
• Tokens VIP generados: [Número]
• Mensajes en canales: [Número]

**Narrativa:**
• Usuarios en Nivel 1: [Número]
• Usuarios en El Diván: [Número]
• Progreso promedio: [Porcentaje]%

*[Con aire profesional]*

"*Los datos nunca mienten.*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("📈 Analytics Detallados", callback_data="admin_detailed_analytics")],
                [InlineKeyboardButton("👥 Estadísticas de Usuarios", callback_data="admin_user_stats")],
                [InlineKeyboardButton("📺 Estadísticas de Canales", callback_data="admin_channel_analytics")],
                [InlineKeyboardButton("🎯 Estadísticas de Misiones", callback_data="admin_mission_stats")],
                [InlineKeyboardButton("⬅️ Volver al Panel", callback_data="admin_panel")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                analytics_message,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_admin_analytics: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_manage_admins(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
    ) -> None:
        """Placeholder para gestionar administradores"""

        await self._handle_unknown_callback_narrative(update, context, "manage_admins")

    async def _handle_admin_action(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
        callback_data: str,
    ) -> None:
        """Maneja acciones específicas de administración"""

        try:
            user_telegram_id = update.effective_user.id
            first_name = getattr(user, "first_name", "Usuario")

            if callback_data == "admin_token_quick":
                await self._generate_quick_vip_token(update, context, user_telegram_id)
            elif callback_data == "admin_token_weekly":
                await self._generate_weekly_vip_token(update, context, user_telegram_id)
            elif callback_data == "admin_my_activity":
                await self._show_admin_activity(update, context, user_telegram_id)
            else:
                await self._handle_unknown_callback_narrative(update, context, callback_data)

        except Exception as e:
            logger.error(f"❌ Error en _handle_admin_action: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    # === MÉTODOS AUXILIARES DE ADMINISTRACIÓN ===

    def _format_admin_permissions(self, admin) -> str:
        """Formatea los permisos del admin para mostrar"""

        permissions = []
        if admin.can_generate_vip_tokens:
            permissions.append("🎫 Generar tokens VIP")
        if admin.can_manage_channels:
            permissions.append("📺 Gestionar canales")
        if admin.can_manage_users:
            permissions.append("👥 Gestionar usuarios")
        if admin.can_access_analytics:
            permissions.append("📊 Ver analytics")
        if admin.can_manage_admins:
            permissions.append("👑 Gestionar admins")
        if admin.can_modify_system:
            permissions.append("⚙️ Configurar sistema")

        return "\n".join(f"• {perm}" for perm in permissions) if permissions else "• Sin permisos especiales"

    async def _send_no_admin_access_message(self, update, first_name: str):
        """Envía mensaje cuando el usuario no es admin"""

        message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de superioridad]*

"*Oh, {first_name}... qué adorable.*"

*[Con desdén elegante]*

"*¿Realmente creías que podrías acceder al panel de administración?*"

*[Con sarcasmo refinado]*

"*Esto es solo para personas... importantes. Y claramente, tú no lo eres.*"
        """.strip()

        keyboard = [[InlineKeyboardButton("⬅️ Volver al Menú", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def _send_no_permission_message(self, update, first_name: str, action: str):
        """Mensaje cuando falta permiso"""

        message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de reproche]*

"*{first_name}, no tienes permiso para {action}.*"
        """.strip()

        keyboard = [[InlineKeyboardButton("⬅️ Volver", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def _send_limit_reached_message(self, update, first_name: str, reason: str):
        """Indica que se alcanzó un límite"""

        message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de advertencia]*

"*{first_name}, {reason}.*"
        """.strip()

        keyboard = [[InlineKeyboardButton("⬅️ Volver", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def _generate_quick_vip_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_telegram_id: int) -> None:
        """Genera un token VIP rápido (24h)"""

        try:
            result = self.admin_service.generate_vip_token(user_telegram_id, "quick")

            if result.get("success"):
                await update.callback_query.edit_message_text(
                    f"🎫 **Token VIP Generado**\n\n"
                    f"Token: `{result['token']}`\n"
                    f"Expira: {result['expiry']}",
                    parse_mode="Markdown"
                )
            else:
                await update.callback_query.edit_message_text(
                    f"❌ Error: {result.get('error', 'Error desconocido')}",
                    parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"❌ Error en _generate_quick_vip_token: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _generate_weekly_vip_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_telegram_id: int) -> None:
        """Genera un token VIP semanal (7 días)"""

        try:
            result = self.admin_service.generate_vip_token(user_telegram_id, "weekly")

            if result.get("success"):
                await update.callback_query.edit_message_text(
                    f"🎫 **Token VIP Generado**\n\n"
                    f"Token: `{result['token']}`\n"
                    f"Expira: {result['expiry']}",
                    parse_mode="Markdown"
                )
            else:
                await update.callback_query.edit_message_text(
                    f"❌ Error: {result.get('error', 'Error desconocido')}",
                    parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"❌ Error en _generate_weekly_vip_token: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _show_admin_activity(self, update, context, telegram_id: int):
        """Muestra actividad del administrador"""

        stats = self.admin_service.get_admin_statistics(telegram_id)
        message = f"""
**Tu actividad**

• Comandos usados: {stats['activity']['total_commands']}
• Último comando: {stats['activity']['last_command'] or 'N/A'}
        """.strip()

        keyboard = [[InlineKeyboardButton("⬅️ Volver", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

