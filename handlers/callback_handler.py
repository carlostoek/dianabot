from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from services.user_service import UserService
from services.mission_service import MissionService
from services.game_service import GameService
from services.auction_service import AuctionService
from utils.lucien_voice import LucienVoice
from handlers.start_handler import StartHandler
from typing import Dict, Any


class CallbackHandler:
    """Maneja todos los callbacks de botones con experiencia SEDUCTORA"""

    def __init__(self):
        self.user_service = UserService()
        self.mission_service = MissionService()
        self.game_service = GameService()
        self.auction_service = AuctionService()
        self.lucien = LucienVoice()
        self.start_handler = StartHandler()

    async def handle_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Router principal de callbacks"""

        query = update.callback_query
        await query.answer()

        user_data = {
            "telegram_id": query.from_user.id,
            "username": query.from_user.username,
            "first_name": query.from_user.first_name,
            "last_name": query.from_user.last_name,
        }

        user = self.user_service.create_or_update_user(user_data)
        narrative_state = self.user_service.get_or_create_narrative_state(user["id"])

        # Router de callbacks
        callback_data = query.data

        # === INTRO CALLBACKS ===
        if callback_data == "intro_diana":
            await self._show_diana_intro(update, context, user)
        elif callback_data == "intro_lucien":
            await self._show_lucien_intro(update, context, user)
        elif callback_data == "intro_bot":
            await self._show_bot_intro(update, context, user)

        # === NAVIGATION ===
        elif callback_data == "main_menu":
            await self.start_handler._show_main_menu(
                update, context, user, narrative_state
            )
        elif callback_data == "back":
            await self._handle_back(update, context, user, narrative_state)

        # === PROFILE ===
        elif callback_data == "profile":
            await self._show_profile(update, context, user, narrative_state)
        elif callback_data == "profile_vip":
            await self._show_vip_profile(update, context, user, narrative_state)

        # === CONVERSION FOCUSED ===
        elif callback_data == "premium_info":
            await self._show_premium_info(update, context, user)
        elif callback_data == "vip_info":
            await self._show_vip_info(update, context, user)
        elif callback_data == "vip_testimonials":
            await self._show_vip_testimonials(update, context, user)
        elif callback_data == "how_to_vip":
            await self._show_how_to_vip(update, context, user)
        elif callback_data == "special_offer":
            await self._show_special_offer(update, context, user)

        # === VIP UPSELLS ===
        elif callback_data == "premium_auctions":
            await self._show_premium_auctions(update, context, user)
        elif callback_data == "intimate_collection":
            await self._show_intimate_collection(update, context, user)
        elif callback_data == "custom_experiences":
            await self._show_custom_experiences(update, context, user)
        elif callback_data == "vip_exclusive_offers":
            await self._show_vip_exclusive_offers(update, context, user)

        # === FUNCTIONALITY ===
        elif callback_data == "missions":
            await self._show_missions(update, context, user, narrative_state)
        elif callback_data == "games":
            await self._show_games(update, context, user)
        elif callback_data == "shop":
            await self._show_shop(update, context, user)

        # Agregar más handlers según necesidad...

    # === INTRO EXPERIENCES ===

    async def _show_diana_intro(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Dict
    ) -> None:
        """Presentación SEDUCTORA de Diana"""

        diana_intro = f"""
{self.lucien.EMOJIS['diana']} *Diana se acerca lentamente, su presencia llena el espacio*

"*{user['first_name']}... permíteme que me presente adecuadamente.*"

*[Con elegancia magnética]*

"*Soy Diana. No soy como las demás. No busco atención... la atención me busca a mí. Soy selectiva, inteligente, y tengo gustos... particulares.*"

*[Sus ojos brillan con misterio]*

"*Este no es un simple bot. Es mi mundo digital, donde solo los más interesantes pueden prosperar. Donde recompenso la dedicación, la inteligencia... y la devoción.*"

*[Con sonrisa seductora]*

"*La pregunta no es si yo te voy a elegir, {user['first_name']}... sino si tú vas a ser lo suficientemente fascinante para mantener mi interés.*"

{self.lucien.EMOJIS['lucien']} *[Lucien observa]*

Diana no miente. Solo el 3% de quienes la conocen llegan a su círculo íntimo...
        """.strip()

        keyboard = [
            [
                InlineKeyboardButton(
                    "😍 Me fascinas, Diana", callback_data="fascinated_diana"
                )
            ],
            [
                InlineKeyboardButton(
                    "🤔 Quiero saber más...", callback_data="want_know_more"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎭 ¿Qué debo hacer para impresionarte?",
                    callback_data="how_to_impress",
                )
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            diana_intro, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def _show_lucien_intro(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Dict
    ) -> None:
        """Presentación elegante de Lucien"""

        lucien_intro = f"""
{self.lucien.EMOJIS['lucien']} *[Con reverencia profesional]*

Permíteme presentarme formalmente, {user['first_name']}.

Soy **Lucien**, mayordomo personal y confidente de Diana desde hace años. Mi función es... compleja.

*[Con aire analítico]*

**Mi trabajo incluye:**
• 🎭 Evaluar la personalidad de cada visitante
• 📊 Analizar patrones de comportamiento  
• 🎯 Diseñar misiones personalizadas
• 🛡️ Proteger la privacidad de Diana
• 💎 Gestionar su mundo digital

*[Con confianza]*

Diana confía en mi juicio completamente. Si yo determino que alguien es... especial, ella presta atención.

*[Con aire conspiratorio]*

Entre tú y yo, {user['first_name']}, ya he comenzado tu evaluación. Tus respuestas, tus elecciones... todo importa.

Diana no tiene tiempo para trivialidades. Pero si demuestras ser genuino, inteligente y dedicado... bueno, las recompensas pueden ser... extraordinarias.
        """.strip()

        keyboard = [
            [
                InlineKeyboardButton(
                    "🎭 ¿Cómo me evalúas exactamente?",
                    callback_data="evaluation_process",
                )
            ],
            [
                InlineKeyboardButton(
                    "💡 ¿Qué busca Diana en una persona?", callback_data="diana_seeks"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎯 Quiero empezar mi evaluación", callback_data="start_evaluation"
                )
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            lucien_intro, reply_markup=reply_markup, parse_mode="Markdown"
        )

    # === CONVERSION EXPERIENCES ===

    async def _show_vip_info(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Dict
    ) -> None:
        """Info VIP MAGNÉTICA para conversión"""

        vip_info = f"""
{self.lucien.EMOJIS['diana']} *Diana aparece con exclusividad*

"*{user['first_name']}... quieres saber sobre mi círculo íntimo.*"

*[Con aire misterioso]*

"*El Diván no es solo un canal VIP. Es mi santuario personal. Solo el 5% de quienes me conocen llegan ahí...*"

{self.lucien.EMOJIS['lucien']} **¿Por qué Diana elige solo a algunos?**

*[Con conocimiento íntimo]*

El acceso al Diván no se compra... se **gana**. Diana evalúa:

✨ **Dedicación genuina** - No buscadores de contenido rápido
💎 **Inteligencia emocional** - Quienes entienden la sutileza  
🎭 **Personalidad fascinante** - Cada individuo debe ser único
🔥 **Consistencia** - Diana observa patrones, no momentos

**¿Qué obtienen los miembros del Diván?**

👑 **Contenido ultra exclusivo** de Diana
💋 **Interacción personal** - Diana responde directamente
🎯 **Subastas premium** - Contenido que nunca sale del Diván
✨ **Experiencias personalizadas** - Creadas solo para ti
🛡️ **Privacidad absoluta** - Lo que pasa en el Diván, queda en el Diván

*[Con intensidad]*

Diana está observando tu comportamiento ahora mismo, {user['first_name']}. ¿Serás digno de su atención íntima?
        """.strip()

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔥 Quiero demostrar que soy digno", callback_data="prove_worthy"
                )
            ],
            [
                InlineKeyboardButton(
                    "💎 ¿Cómo puedo impresionar a Diana?",
                    callback_data="how_to_impress",
                )
            ],
            [
                InlineKeyboardButton(
                    "🎭 Ver testimonios del Diván", callback_data="divan_testimonials"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 Evaluar mi progreso actual", callback_data="check_vip_progress"
                )
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            vip_info, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def _show_premium_info(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Dict
    ) -> None:
        """Info de contenido premium SEDUCTORA"""

        premium_info = f"""
{self.lucien.EMOJIS['diana']} *Diana se acerca con misterio*

"*{user['first_name']}... te interesa mi contenido más... íntimo.*"

*[Con sonrisa seductora]*

"*No todo lo que creo está disponible para todos. Las mejores piezas, las más personales... requieren verdadera dedicación.*"

{self.lucien.EMOJIS['lucien']} **Sistema de Contenido Premium**

*[Con elegancia]*

Diana crea contenido en diferentes niveles de exclusividad:

🌟 **Contenido Público** - Lo que todos pueden ver
🔥 **Contenido Kinkys** - Para miembros del canal principal  
💎 **Contenido Diván** - Solo para VIPs
✨ **Contenido Ultra Exclusivo** - Subastas especiales
💋 **Contenido Personalizado** - Creado solo para ti

**¿Cómo funciona?**

💰 **Inviertes en besitos** → Diana crea más contenido exclusivo
🎯 **Participas en subastas** → Obtienes piezas únicas
🛍️ **Compras en su tienda** → Accedes a colecciones especiales
🎭 **Demuestras lealtad** → Diana te recompensa personalmente

*[Con aire conspiratorio]*

Los miembros más dedicados han recibido contenido que... bueno, que Diana jamás volverá a crear.
        """.strip()

        keyboard = [
            [
                InlineKeyboardButton(
                    "💎 Ver subastas activas", callback_data="view_auctions"
                )
            ],
            [
                InlineKeyboardButton(
                    "🛍️ Explorar tienda exclusiva", callback_data="explore_shop"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔥 ¿Cómo ganar más besitos?", callback_data="earn_besitos"
                )
            ],
            [
                InlineKeyboardButton(
                    "✨ Testimonios de contenido", callback_data="content_testimonials"
                )
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            premium_info, reply_markup=reply_markup, parse_mode="Markdown"
        )

    # === PROFILE EXPERIENCES ===

    async def _show_profile(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Dict,
        narrative_state: Any,
    ) -> None:
        """Perfil básico ATRACTIVO"""

        # Obtener estadísticas del usuario
        user_stats = self.user_service.get_user_detailed_stats(user["id"])

        # Mensaje personalizado según progreso
        progress_message = self._get_progress_message(
            narrative_state, user["first_name"]
        )

        profile_message = f"""
{self.lucien.EMOJIS['lucien']} **Evaluación Personal de {user['first_name']}**

{progress_message}

📊 **Estadísticas Actuales:**
• **Nivel:** {user_stats['level']} ⭐
• **Experiencia:** {user_stats['experience']:,} XP
• **Besitos:** {user_stats['besitos']:,} 💋
• **Misiones completadas:** {user_stats['missions_completed']}
• **Juegos jugados:** {user_stats['games_played']}

🎭 **Análisis de Personalidad:**
• **Arquetipo:** {narrative_state.primary_archetype.value if narrative_state.primary_archetype else 'En evaluación'}
• **Progreso narrativo:** {narrative_state.current_level.value}
• **Nivel de confianza con Diana:** {narrative_state.diana_trust_level}/100

{self.lucien.EMOJIS['diana']} *[Diana observa]*

"*{user['first_name']} está... progresando. Pero aún hay mucho camino por recorrer.*"
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🎯 Próximas misiones", callback_data="missions")],
            [InlineKeyboardButton("🎮 Mejorar con juegos", callback_data="games")],
            [
                InlineKeyboardButton(
                    "📈 ¿Cómo subir de nivel?", callback_data="level_up_guide"
                )
            ],
            [
                InlineKeyboardButton(
                    "💎 ¿Cómo llegar al Diván?", callback_data="divan_guide"
                )
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            profile_message, reply_markup=reply_markup, parse_mode="Markdown"
        )

    # === FUNCTIONALITY ===

    async def _show_missions(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Dict,
        narrative_state: Any,
    ) -> None:
        """Muestra misiones con MOTIVACIÓN"""

        # Obtener misiones activas
        active_missions = self.mission_service.get_user_active_missions(user["id"])

        if not active_missions:
            missions_message = f"""
{self.lucien.EMOJIS['lucien']} **Misiones Personalizadas**

*[Con eficiencia]*

{user['first_name']}, estoy preparando nuevas misiones basadas en tu progreso actual...

{self.lucien.EMOJIS['diana']} *[Con expectativa]*

"*Lucien está diseñando desafíos especiales para ti. Regresa pronto...*"
            """.strip()

            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔄 Generar misiones", callback_data="generate_missions"
                    )
                ],
                [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
            ]
        else:
            missions_text = []
            for mission in active_missions[:3]:  # Mostrar máximo 3
                progress = (
                    f"{mission['progress']}/{mission['target']}"
                    if mission["target"] > 1
                    else "En progreso"
                )
                reward_text = (
                    f"{mission['besitos_reward']} besitos"
                    if mission["besitos_reward"] > 0
                    else "Experiencia especial"
                )

                missions_text.append(
                    f"""
🎯 **{mission['title']}**
📝 {mission['description']}
📊 Progreso: {progress}
🎁 Recompensa: {reward_text}
                """.strip()
                )

            missions_message = f"""
{self.lucien.EMOJIS['lucien']} **Misiones Activas**

*[Con propósito]*

Diana ha diseñado estos desafíos específicamente para ti, {user['first_name']}:

{chr(10).join(missions_text)}

*[Con aliento]*

Cada misión completada te acerca más a ganar la confianza de Diana...
            """.strip()

            keyboard = [
                [
                    InlineKeyboardButton(
                        "📊 Ver todas las misiones", callback_data="all_missions"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏆 Historial de logros", callback_data="achievements"
                    )
                ],
                [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            missions_message, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def _show_games(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Dict
    ) -> None:
        """Muestra juegos ATRACTIVOS"""

        games_message = f"""
{self.lucien.EMOJIS['diana']} *Diana sonríe con interés*

"*{user['first_name']}, los juegos revelan la verdadera naturaleza de una persona...*"

*[Con curiosidad]*

"*Cada juego que juegas me dice algo sobre ti. Tu manera de pensar, de decidir, de crear... todo me fascina.*"

{self.lucien.EMOJIS['lucien']} **Juegos de Evaluación**

*[Con propósito]*

Cada juego está diseñado para que Diana conozca mejor tu personalidad:

🧩 **Acertijos** - Tu capacidad analítica
🎭 **Asociación de palabras** - Tu creatividad
🔍 **Reconocimiento de patrones** - Tu lógica
💭 **Dilemas morales** - Tus valores
⚡ **Decisiones rápidas** - Tu instinto
🧠 **Desafíos de memoria** - Tu concentración
✨ **Tests creativos** - Tu originalidad

*[Con incentivo]*

Los mejores resultados son... recompensados generosamente por Diana.
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🧩 Jugar Acertijo", callback_data="play_riddle")],
            [
                InlineKeyboardButton(
                    "🎭 Asociación de Palabras", callback_data="play_word_game"
                )
            ],
            [
                InlineKeyboardButton(
                    "⚡ Decisiones Rápidas", callback_data="play_quick_choice"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 Ver mis estadísticas", callback_data="game_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏆 Ranking de jugadores", callback_data="game_leaderboard"
                )
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            games_message, reply_markup=reply_markup, parse_mode="Markdown"
        )

    # === MÉTODOS AUXILIARES ===

    def _get_progress_message(self, narrative_state: Any, first_name: str) -> str:
        """Genera mensaje de progreso personalizado"""

        level = narrative_state.current_level.value
        trust = narrative_state.diana_trust_level

        if narrative_state.has_divan_access:
            return f"""
*[Con admiración]*

{first_name}, has logrado algo extraordinario. Diana te ha otorgado acceso a su círculo más íntimo.

*[Con respeto]*

Pocos llegan tan lejos en ganar su confianza...
            """.strip()

        elif trust >= 70:
            return f"""
*[Con expectativa]*

{first_name}, Diana está claramente interesada en ti. Tus acciones no pasan desapercibidas.

*[Con anticipación]*

Estás muy cerca de algo... especial.
            """.strip()

        elif trust >= 40:
            return f"""
*[Con aprobación]*

{first_name}, Diana ha comenzado a notarte. Tu dedicación está dando frutos.

*[Con aliento]*

Continúa así y pronto verás recompensas más... significativas.
            """.strip()

        else:
            return f"""
*[Con evaluación]*

{first_name}, Diana está observando tus primeros pasos. Cada acción cuenta.

*[Con orientación]*

Demuestra dedicación y consistencia para ganar su atención.
            """.strip()


# Registrar handler
callback_handler = CallbackQueryHandler(CallbackHandler().handle_callback)
   