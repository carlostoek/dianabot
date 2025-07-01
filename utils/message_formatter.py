
    from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from models.user import User
from models.mission import Mission, UserMission
from models.auction import Auction


class MessageFormatter:
    """Formateador de mensajes para máxima legibilidad y engagement"""

    def __init__(self):
        self.EMOJIS = {
            "besitos": "💋",
            "level": "⭐",
            "xp": "⚡",
            "vip": "👑",
            "time": "⏰",
            "trophy": "🏆",
            "gift": "🎁",
            "fire": "🔥",
            "sparkles": "✨",
            "target": "🎯",
            "rocket": "🚀",
            "gem": "💎",
            "crown": "👑",
            "star": "🌟",
            "celebration": "🎉",
            "progress": "📈",
            "warning": "⚠️",
            "success": "✅",
            "info": "ℹ️",
            "arrow_up": "📈",
            "arrow_down": "📉",
        }

    def format_user_profile(self, user: User, stats: Dict) -> str:
        """Formatea perfil de usuario de manera atractiva y clara"""

        # Calcular progreso al siguiente nivel
        current_xp = user.experience
        next_level_xp = self._calculate_next_level_xp(user.level)
        progress_bar = self._create_visual_progress_bar(current_xp, next_level_xp)
        progress_percent = (
            (current_xp / next_level_xp * 100) if next_level_xp > 0 else 100
        )

        # Estado VIP con tiempo restante
        vip_status = self._format_vip_status(user)

        # Crear mensaje estructurado
        profile_text = f"""
{self.EMOJIS['crown']} **{user.first_name}** - Tu Aventura

━━━━━━━━━━━━━━━━━━━━
{self.EMOJIS['level']} **Nivel {user.level}** {vip_status}
{self.EMOJIS['besitos']} **{user.besitos:,} Besitos**
{self.EMOJIS['xp']} **Experiencia:** {current_xp:,}/{next_level_xp:,}

{progress_bar} {progress_percent:.1f}%

━━━━━━━━━━━━━━━━━━━━
📊 **TUS LOGROS**

🎯 Misiones completadas: **{stats.get('missions_completed', 0)}**
🎮 Juegos jugados: **{stats.get('games_played', 0)}**
🧠 Trivias correctas: **{stats.get('trivia_correct', 0)}/{stats.get('trivia_total', 0)}**
❤️ Reacciones dadas: **{stats.get('total_reactions', 0)}**
{f"{self.EMOJIS['trophy']} Subastas ganadas: **{stats.get('auctions_won', 0)}**" if stats.get('auctions_won', 0) > 0 else ""}

━━━━━━━━━━━━━━━━━━━━
{self._get_motivational_message(user)}
        """.strip()

        return profile_text

    def format_mission_detail(self, user_mission: UserMission) -> str:
        """Formatea detalles de misión de manera motivacional"""
        mission = user_mission.mission

        # Progreso visual
        progress_bar = self._create_visual_progress_bar(
            user_mission.current_progress, user_mission.target_progress
        )
        progress_percent = (
            (user_mission.current_progress / user_mission.target_progress * 100)
            if user_mission.target_progress > 0
            else 0
        )

        # Tiempo restante si aplica
        time_info = ""
        if user_mission.expires_at:
            time_left = user_mission.expires_at - datetime.utcnow()
            if time_left > timedelta(0):
                time_info = f"\n{self.EMOJIS['time']} **Tiempo restante:** {self._format_time_remaining(time_left)}"
            else:
                time_info = f"\n{self.EMOJIS['warning']} **¡Misión expirada!**"

        # Tipo de misión con emoji
        mission_type_emojis = {
            "daily": "📅",
            "weekly": "📊",
            "special": "⭐",
            "narrative": "📖",
        }
        type_emoji = mission_type_emojis.get(mission.mission_type.value, "🎯")

        mission_text = f"""
{type_emoji} **{mission.title}**

━━━━━━━━━━━━━━━━━━━━
📝 **DESCRIPCIÓN**
{mission.description}

━━━━━━━━━━━━━━━━━━━━
📊 **TU PROGRESO**
{progress_bar} **{user_mission.current_progress}/{user_mission.target_progress}** ({progress_percent:.1f}%)

━━━━━━━━━━━━━━━━━━━━
🎁 **RECOMPENSAS AL COMPLETAR**
{self.EMOJIS['besitos']} **{mission.reward_besitos} Besitos**
{f"{self.EMOJIS['xp']} **{mission.reward_experience} Experiencia**" if mission.reward_experience > 0 else ""}
{f"📜 **Nueva pieza de historia**" if mission.reward_lore_piece_id else ""}
{time_info}

━━━━━━━━━━━━━━━━━━━━
{self._get_mission_encouragement(progress_percent)}
        """.strip()

        return mission_text

    def format_auction_details(
        self,
        auction: Auction,
        user_bid: Optional[int] = None,
        is_watching: bool = False,
    ) -> str:
        """Formatea detalles de subasta de manera emocionante"""

        # Estado de la subasta
        status_emoji = {
            "active": "🔥",
            "scheduled": "⏰",
            "ended": "🏁",
            "cancelled": "❌",
        }.get(auction.status.value, "❓")

        # Tiempo
        time_info = self._format_auction_timing(auction)

        # Estado del usuario
        user_status = ""
        if user_bid:
            if user_bid == auction.current_price:
                user_status = f"\n🥇 **¡ESTÁS GANANDO!** Tu puja: {user_bid:,}{self.EMOJIS['besitos']}"
            else:
                user_status = f"\n💸 **Te superaron.** Tu puja: {user_bid:,}{self.EMOJIS['besitos']}"

        # Información de pujas
        bid_info = f"""
💰 **Puja actual:** {auction.current_price:,}{self.EMOJIS['besitos']}
📈 **Incremento mínimo:** {auction.min_bid_increment:,}{self.EMOJIS['besitos']}
{f"⚡ **Compra inmediata:** {auction.buyout_price:,}{self.EMOJIS['besitos']}" if auction.buyout_price else ""}
{f"🔒 **Precio de reserva:** {auction.reserve_price:,}{self.EMOJIS['besitos']}" if auction.reserve_price else ""}
        """.strip()

        # Items de la subasta
        items_text = ""
        if auction.items:
            items_text = "\n━━━━━━━━━━━━━━━━━━━━\n🎁 **LO QUE GANARÁS**\n"
            for item in auction.items:
                items_text += f"• {item.name}\n"

        auction_text = f"""
{status_emoji} **{auction.title}**

━━━━━━━━━━━━━━━━━━━━
📋 **DESCRIPCIÓN**
{auction.description}

━━━━━━━━━━━━━━━━━━━━
💰 **INFORMACIÓN DE PUJAS**
{bid_info}

━━━━━━━━━━━━━━━━━━━━
⏰ **TIEMPO**
{time_info}
{user_status}
{items_text}
━━━━━━━━━━━━━━━━━━━━
{self._get_auction_encouragement(auction, user_bid)}
        """.strip()

        return auction_text

    def format_game_result(
        self,
        game_type: str,
        score: int,
        besitos_earned: int,
        additional_data: Dict = None,
    ) -> str:
        """Formatea resultados de juegos de manera celebratoria"""

        # Emojis y mensajes por tipo de juego
        game_configs = {
            "trivia": {"emoji": "🧠", "name": "Trivia", "score_label": "Respuesta"},
            "number_guess": {
                "emoji": "🔢",
                "name": "Adivina el Número",
                "score_label": "Puntos",
            },
            "math": {
                "emoji": "🧮",
                "name": "Desafío Matemático",
                "score_label": "Puntos",
            },
        }

        config = game_configs.get(
            game_type, {"emoji": "🎮", "name": "Juego", "score_label": "Puntos"}
        )

        # Determinar el nivel de celebración
        celebration = self._get_celebration_level(score)

        result_text = f"""
{config['emoji']} **{config['name']} Completado!**

━━━━━━━━━━━━━━━━━━━━
{celebration['emoji']} **{celebration['message']}**

📊 **{config['score_label']}:** {score}
{self.EMOJIS['besitos']} **Besitos ganados:** {besitos_earned}

━━━━━━━━━━━━━━━━━━━━
{self._get_game_encouragement(score, game_type)}
        """.strip()

        # Añadir información adicional si existe
        if additional_data:
            if "time_taken" in additional_data:
                result_text += (
                    f"\n⚡ **Tiempo:** {additional_data['time_taken']:.1f} segundos"
                )

            if "correct_answers" in additional_data:
                total = additional_data.get("total_questions", 1)
                result_text += (
                    f"\n✅ **Correctas:** {additional_data['correct_answers']}/{total}"
                )

        return result_text

    def format_daily_gift(
        self, user: User, gift_amount: int, bonus_info: Dict = None
    ) -> str:
        """Formatea mensaje de regalo diario de manera especial"""

        # Calcular streak si existe
        streak_text = ""
        if bonus_info and "streak_days" in bonus_info:
            streak_days = bonus_info["streak_days"]
            if streak_days > 1:
                streak_text = f"\n🔥 **Racha de {streak_days} días!** ¡Sigue así!"

        # Bonus por nivel/VIP
        bonus_text = ""
        if bonus_info:
            if "level_bonus" in bonus_info:
                bonus_text += f"\n⭐ Bonus por nivel {user.level}: +{bonus_info['level_bonus']}{self.EMOJIS['besitos']}"
            if "vip_bonus" in bonus_info and user.is_vip:
                bonus_text += f"\n👑 Bonus VIP: +{bonus_info['vip_bonus']}{self.EMOJIS['besitos']}"

        gift_text = f"""
{self.EMOJIS['gift']} **¡Regalo Diario Reclamado!**

━━━━━━━━━━━━━━━━━━━━
{self.EMOJIS['celebration']} **¡Excelente, {user.first_name}!**

{self.EMOJIS['besitos']} **Has recibido: {gift_amount} Besitos**
💰 **Total ahora: {user.besitos + gift_amount:,} Besitos**
{streak_text}
{bonus_text}

━━━━━━━━━━━━━━━━━━━━
🌅 **¡Vuelve mañana para otro regalo!**

💡 **Tip:** Completa misiones y juega para ganar más besitos durante el día.
        """.strip()

        return gift_text

    def format_level_up_celebration(
        self, user: User, old_level: int, new_level: int, rewards: Dict
    ) -> str:
        """Formatea celebración de subida de nivel de manera épica"""

        # Mensaje especial basado en el nivel alcanzado
        milestone_message = self._get_level_milestone_message(new_level)

        celebration_text = f"""
{self.EMOJIS['rocket']} **¡NIVEL UP!** {self.EMOJIS['celebration']}

━━━━━━━━━━━━━━━━━━━━
🎊 **¡FELICIDADES {user.first_name.upper()}!**

{self.EMOJIS['level']} **Nivel {old_level} → Nivel {new_level}!**

━━━━━━━━━━━━━━━━━━━━
🎁 **RECOMPENSAS DESBLOQUEADAS:**

{self.EMOJIS['besitos']} **+{rewards.get('besitos', 0)} Besitos**
{self.EMOJIS['xp']} **+{rewards.get('experience', 0)} Experiencia**
{f"✨ **Nuevas funciones desbloqueadas**" if new_level in [5, 10, 15, 20] else ""}

━━━━━━━━━━━━━━━━━━━━
{milestone_message}

{self._get_next_level_preview(new_level)}
        """.strip()

        return celebration_text

    # ===== HELPER METHODS =====

    def _create_visual_progress_bar(
        self, current: int, total: int, length: int = 10
    ) -> str:
        """Crea barra de progreso visual con emojis"""
        if total == 0:
            return "▱" * length

        filled = min(length, int((current / total) * length))
        return "🟩" * filled + "⬜" * (length - filled)

    def _format_vip_status(self, user: User) -> str:
        """Formatea estado VIP del usuario"""
        if not user.is_vip:
            return ""

        if user.vip_expires:
            days_left = (user.vip_expires - datetime.utcnow()).days
            if days_left <= 3:
                return f"{self.EMOJIS['warning']} VIP ({days_left}d restantes)"
            else:
                return f"{self.EMOJIS['vip']} VIP"
        else:
            return f"{self.EMOJIS['vip']} VIP"

    def _get_motivational_message(self, user: User) -> str:
        """Genera mensaje motivacional personalizado"""
        messages = []

        if user.level < 5:
            messages.append(
                "🌟 ¡Sigue subiendo de nivel para desbloquear más funciones!"
            )
        elif user.level < 10:
            messages.append("🚀 ¡Ya eres un veterano! ¿Puedes llegar al nivel 10?")
        elif user.level < 20:
            messages.append("👑 ¡Impresionante progreso! Te acercas a la élite.")
        else:
            messages.append("🔥 ¡Eres una leyenda! Tu dedicación es inspiradora.")

        if not user.is_vip and user.level >= 3:
            messages.append("💎 Considera obtener VIP para beneficios exclusivos.")

        return "\n".join(messages)

    def _get_mission_encouragement(self, progress_percent: float) -> str:
        """Genera mensaje de aliento para misiones"""
        if progress_percent == 0:
            return "🚀 ¡Empecemos! Cada paso cuenta hacia la victoria."
        elif progress_percent < 25:
            return "💪 ¡Buen comienzo! Sigue así para obtener las recompensas."
        elif progress_percent < 50:
            return "🔥 ¡Vas por buen camino! Ya tienes un cuarto completado."
        elif progress_percent < 75:
            return "⚡ ¡Excelente progreso! Estás más cerca de la meta."
        elif progress_percent < 100:
            return "🏁 ¡Casi lo logras! El final está muy cerca."
        else:
            return "🎉 ¡Misión completada! ¡Eres increíble!"

    def _format_time_remaining(self, time_delta: timedelta) -> str:
        """Formatea tiempo restante de manera legible"""
        total_seconds = int(time_delta.total_seconds())

        if total_seconds < 60:
            return f"{total_seconds} segundos"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes} minutos"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        else:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            return f"{days}d {hours}h"

    def _calculate_next_level_xp(self, current_level: int) -> int:
        """Calcula XP necesaria para el siguiente nivel"""
        return (current_level + 1) ** 2 * 100

    def _format_auction_timing(self, auction: Auction) -> str:
        """Formatea información de tiempo de subasta"""
        now = datetime.utcnow()

        if auction.status.value == "scheduled":
            time_until_start = auction.starts_at - now
            return (
                f"🚀 **Comienza en:** {self._format_time_remaining(time_until_start)}"
            )
        elif auction.status.value == "active":
            time_until_end = auction.ends_at - now
            if time_until_end.total_seconds() > 0:
                urgency = (
                    "🔥 **¡ÚLTIMOS MINUTOS!**"
                    if time_until_end.total_seconds() < 3600
                    else "⏰ **Termina en:**"
                )
                return f"{urgency} {self._format_time_remaining(time_until_end)}"
            else:
                return "🏁 **¡Subasta terminada!**"
        elif auction.status.value == "ended":
            return (
                f"🏁 **Terminó** el {auction.ends_at.strftime('%d/%m/%Y a las %H:%M')}"
            )
        else:
            return f"❌ **Cancelada**"

    def _get_auction_encouragement(
        self, auction: Auction, user_bid: Optional[int]
    ) -> str:
        """Genera mensaje de aliento para subastas"""
        if auction.status.value != "active":
            return ""

        if not user_bid:
            return "💪 ¡Haz tu primera puja y entra en la competencia!"
        elif user_bid == auction.current_price:
            return "🏆 ¡Estás ganando! Mantente alerta por si alguien más puja."
        else:
            return "⚡ ¡No te rindas! Aún puedes recuperar el liderazgo."

    def _get_celebration_level(self, score: int) -> Dict[str, str]:
        """Determina nivel de celebración basado en el score"""
        if score >= 90:
            return {"emoji": "🏆", "message": "¡PUNTUACIÓN PERFECTA! ¡ERES UN GENIO!"}
        elif score >= 75:
            return {
                "emoji": "🌟",
                "message": "¡EXCELENTE TRABAJO! Puntuación impresionante.",
            }
        elif score >= 50:
            return {"emoji": "👍", "message": "¡BIEN HECHO! Sólido desempeño."}
        else:
            return {
                "emoji": "💪",
                "message": "¡BUEN INTENTO! La práctica hace al maestro.",
            }

    def _get_game_encouragement(self, score: int, game_type: str) -> str:
        """Genera aliento específico para cada tipo de juego"""
        base_messages = {
            "trivia": [
                "🧠 ¡Sigue desafiando tu mente!",
                "📚 Cada pregunta te hace más sabio.",
                "🎓 El conocimiento es poder!",
            ],
            "number_guess": [
                "🔮 ¡Desarrolla tu intuición!",
                "🎯 La suerte favorece a los audaces.",
                "🎲 ¡Cada intento te acerca al éxito!",
            ],
            "math": [
                "🧮 ¡Las matemáticas son tu aliado!",
                "⚡ ¡Tu mente es una calculadora perfecta!",
                "🚀 ¡Los números no tienen secretos para ti!",
            ],
        }

        messages = base_messages.get(game_type, ["🎮 ¡Sigue jugando y mejorando!"])
        import random

        return random.choice(messages)

    def _get_level_milestone_message(self, level: int) -> str:
        """Mensajes especiales para niveles importantes"""
        milestones = {
            5: "🎊 ¡Nivel 5! Ahora puedes acceder a las subastas VIP y contenido premium.",
            10: "🏅 ¡Nivel 10! Eres oficialmente un veterano de la comunidad.",
            15: "💎 ¡Nivel 15! Tu experiencia y dedicación son admirables.",
            20: "👑 ¡Nivel 20! Te acercas a la élite de usuarios.",
            25: "🌟 ¡Nivel 25! Tu compromiso con la comunidad es legendario.",
            30: "🏆 ¡Nivel 30! Eres un verdadero maestro del bot.",
            50: "⚡ ¡Nivel 50! Tu poder y influencia son extraordinarios.",
            100: "🔥 ¡NIVEL 100! ¡ERES UNA LEYENDA VIVIENTE!",
        }

        if level in milestones:
            return milestones[level]
        elif level % 10 == 0:
            return f"🎉 ¡Nivel {level}! Cada hito te acerca más a la grandeza."

        return "✨ ¡Sigue creciendo y alcanzando nuevas alturas!"

    def _get_next_level_preview(self, current_level: int) -> str:
        """Muestra lo que viene en el siguiente nivel"""
        next_level = current_level + 1
        previews = {
            5: "🔮 **Próximo:** Acceso a subastas VIP (Nivel 5)",
            10: "🎮 **Próximo:** Funciones avanzadas de juegos (Nivel 10)",
            15: "📖 **Próximo:** Contenido narrativo exclusivo (Nivel 15)",
            20: "👑 **Próximo:** Privilegios de élite (Nivel 20)",
        }

        if next_level in [5, 10, 15, 20]:
            return previews.get(next_level, "")

        return f"🚀 **Siguiente meta:** ¡Nivel {next_level}!"
   