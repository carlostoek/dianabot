from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from models.user import User
from models.mission import Mission, UserMission, MissionStatus
from models.auction import Auction
from typing import List, Optional, Dict, Any


class UserKeyboards:
    """Teclados intuitivos optimizados para usuarios no técnicos"""

    def __init__(self):
        # Emojis consistentes para toda la experiencia
        self.EMOJIS = {
            # Navegación principal
            "home": "🏠",
            "back": "◀️",
            "next": "▶️",
            "up": "⬆️",
            "down": "⬇️",
            "refresh": "🔄",
            "close": "❌",
            "menu": "📋",
            # Acciones principales
            "play": "🎮",
            "missions": "🎯",
            "bag": "🎒",
            "gift": "🎁",
            "shop": "🛒",
            "auctions": "🏆",
            "profile": "👤",
            "stats": "📊",
            "help": "❓",
            "settings": "⚙️",
            # Estados y feedback
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "new": "🆕",
            "hot": "🔥",
            "cool": "😎",
            "love": "💕",
            # Recursos del juego
            "besitos": "💋",
            "level": "⭐",
            "xp": "⚡",
            "vip": "👑",
            "time": "⏰",
            "count": "🔢",
            # Juegos y actividades
            "trivia": "🧠",
            "numbers": "🔢",
            "math": "🧮",
            "memory": "🧩",
            "treasure": "💎",
            # Narrativa
            "story": "📖",
            "scroll": "📜",
            "map": "🗺️",
            "key": "🗝️",
            "secret": "🤫",
            # Social
            "friends": "👥",
            "chat": "💬",
            "reaction": "❤️",
            "share": "📤",
        }

    def main_menu_keyboard(self, user: User) -> InlineKeyboardMarkup:
        """Menú principal - Diseñado para máxima claridad"""

        # Calcular progreso del usuario para mostrar motivación
        progress_bar = self._create_progress_bar(
            user.experience, self._calculate_xp_for_next_level(user.level)
        )

        buttons = []

        # Primera fila - Actividades principales (las más usadas arriba)
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{self.EMOJIS['missions']} Misiones {self._get_missions_count_badge(user.id)}",
                    callback_data="user_missions",
                ),
                InlineKeyboardButton(
                    f"{self.EMOJIS['play']} Juegos", callback_data="user_games"
                ),
            ]
        )

        # Segunda fila - Progreso y recompensas
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{self.EMOJIS['bag']} Mi Mochila", callback_data="user_backpack"
                ),
                InlineKeyboardButton(
                    f"{self.EMOJIS['gift']} Regalo Diario {self._get_daily_gift_status(user)}",
                    callback_data="user_daily_gift",
                ),
            ]
        )

        # Tercera fila - Social y premium
        row_3 = []
        if user.is_vip or user.level >= 5:
            row_3.append(
                InlineKeyboardButton(
                    f"{self.EMOJIS['auctions']} Subastas VIP",
                    callback_data="user_auctions",
                )
            )

        row_3.append(
            InlineKeyboardButton(
                f"{self.EMOJIS['stats']} Ranking", callback_data="user_leaderboard"
            )
        )

        if row_3:
            buttons.append(row_3)

        # Cuarta fila - Perfil y ayuda
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{self.EMOJIS['profile']} Mi Perfil", callback_data="user_profile"
                ),
                InlineKeyboardButton(
                    f"{self.EMOJIS['help']} Ayuda", callback_data="user_help"
                ),
            ]
        )

        return InlineKeyboardMarkup(buttons)

    def missions_keyboard(
        self, user_missions: List[UserMission], show_completed: bool = False
    ) -> InlineKeyboardMarkup:
        """Menú de misiones - Organizado por prioridad y claridad"""
        buttons = []

        # Filtrar y organizar misiones
        active_missions = [
            um for um in user_missions if um.status == MissionStatus.ACTIVE
        ]
        completed_missions = [
            um for um in user_missions if um.status == MissionStatus.COMPLETED
        ]

        if not show_completed:
            # Mostrar misiones activas con progreso visual
            if active_missions:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            f"{self.EMOJIS['info']} Tienes {len(active_missions)} misiones activas",
                            callback_data="missions_info",
                        )
                    ]
                )

                for i, um in enumerate(active_missions[:5]):  # Máximo 5 para no saturar
                    mission = um.mission
                    progress_emoji = self._get_mission_progress_emoji(um)
                    progress_text = f"{um.current_progress}/{um.target_progress}"

                    # Tipo de misión con emoji específico
                    type_emoji = {
                        "daily": "📅",
                        "weekly": "📊",
                        "special": "⭐",
                        "narrative": "📖",
                    }.get(mission.mission_type.value, "🎯")

                    button_text = f"{type_emoji} {mission.title[:25]}... {progress_emoji} {progress_text}"

                    buttons.append(
                        [
                            InlineKeyboardButton(
                                button_text, callback_data=f"mission_detail_{um.id}"
                            )
                        ]
                    )
            else:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            f"{self.EMOJIS['info']} No tienes misiones activas",
                            callback_data="missions_refresh",
                        )
                    ]
                )

            # Controles de navegación
            nav_buttons = []
            if completed_missions:
                nav_buttons.append(
                    InlineKeyboardButton(
                        f"{self.EMOJIS['success']} Ver Completadas ({len(completed_missions)})",
                        callback_data="missions_completed",
                    )
                )

            nav_buttons.append(
                InlineKeyboardButton(
                    f"{self.EMOJIS['refresh']} Buscar Nuevas",
                    callback_data="missions_refresh",
                )
            )

            if nav_buttons:
                # Dividir en filas de máximo 2 botones
                for i in range(0, len(nav_buttons), 2):
                    buttons.append(nav_buttons[i : i + 2])

        else:
            # Mostrar misiones completadas
            if completed_missions:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            f"{self.EMOJIS['success']} {len(completed_missions)} misiones completadas",
                            callback_data="missions_completed_info",
                        )
                    ]
                )

                for um in completed_missions[-5:]:  # Últimas 5 completadas
                    mission = um.mission
                    buttons.append(
                        [
                            InlineKeyboardButton(
                                f"✅ {mission.title[:30]}...",
                                callback_data=f"mission_detail_{um.id}",
                            )
                        ]
                    )

            buttons.append(
                [
                    InlineKeyboardButton(
                        f"{self.EMOJIS['back']} Ver Activas",
                        callback_data="missions_active",
                    )
                ]
            )

        # Botón de regreso siempre visible
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{self.EMOJIS['home']} Menú Principal",
                    callback_data="user_main_menu",
                )
            ]
        )

        return InlineKeyboardMarkup(buttons)

    def games_menu_keyboard(self, user: User) -> InlineKeyboardMarkup:
        """Menú de juegos - Diseñado para ser atractivo y fácil"""
        buttons = []

        # Header motivacional
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{self.EMOJIS['play']} ¡Hora de Jugar y Ganar {self.EMOJIS['besitos']}!",
                    callback_data="games_info",
                )
            ]
        )

        # Juegos principales - organizados por dificultad
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{self.EMOJIS['trivia']} Trivia Rápida",
                    callback_data="game_trivia_quick",
                ),
                InlineKeyboardButton(
                    f"{self.EMOJIS['numbers']} Adivina el Número",
                    callback_data="game_number_guess",
                ),
            ]
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    f"{self.EMOJIS['math']} Desafío Matemático",
                    callback_data="game_math",
                ),
                InlineKeyboardButton(
                    f"{self.EMOJIS['memory']} Próximamente...",
                    callback_data="game_coming_soon",
                ),
            ]
        )

        # Información de progreso del usuario en juegos
        if user.level >= 5:
            buttons.append(
                [
                    InlineKeyboardButton(
                        f"{self.EMOJIS['stats']} Mis Estadísticas de Juegos",
                        callback_data="games_stats",
                    ),
                    InlineKeyboardButton(
                        f"{self.EMOJIS['friends']} Ranking de Jugadores",
                        callback_data="games_leaderboard",
                    ),
                ]
            )

        # Navegación
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{self.EMOJIS['home']} Menú Principal",
                    callback_data="user_main_menu",
                )
            ]
        )

        return InlineKeyboardMarkup(buttons)

    def trivia_keyboard(
        self, question_data: Dict, user_level: int
    ) -> InlineKeyboardMarkup:
        """Teclado para trivia - Opciones claras y grandes"""
        buttons = []

        # Header con información
        buttons.append(
            [
                InlineKeyboardButton(
                    f"🧠 Trivia - Nivel {user_level} | Recompensa: {question_data['reward_besitos']}{self.EMOJIS['besitos']}",
                    callback_data="trivia_info",
                )
            ]
        )

        # Opciones de respuesta - usar letras para claridad
        option_letters = ["🅰️", "🅱️", "🅲️", "🅳️"]
        answers = question_data["answers"]

        for i, answer in enumerate(answers):
            # Truncar respuestas largas para que se vean bien
            display_answer = answer if len(answer) <= 30 else answer[:27] + "..."

            buttons.append(
                [
                    InlineKeyboardButton(
                        f"{option_letters[i]} {display_answer}",
                        callback_data=f"trivia_answer_{i}_{question_data['id']}",
                    )
                ]
            )

        # Opciones adicionales
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{self.EMOJIS['help']} Pista (-{question_data['reward_besitos']//2}{self.EMOJIS['besitos']})",
                    callback_data=f"trivia_hint_{question_data['id']}",
                ),
                InlineKeyboardButton(
                    f"{self.EMOJIS['close']} Salir", callback_data="games_menu"
                ),
            ]
        )

        return InlineKeyboardMarkup(buttons)

    def auction_keyboard(
        self, auction: Auction, user: User, user_highest_bid: Optional[int] = None
    ) -> InlineKeyboardMarkup:
        """Teclado para subastas - Enfocado en la acción"""
        buttons = []

        # Estado de la subasta
        time_left = self._format_auction_time_left(auction.ends_at)
        status_emoji = "🔥" if time_left < "1h" else "⏰"

        buttons.append(
            [
                InlineKeyboardButton(
                    f"{status_emoji} Termina en: {time_left}",
                    callback_data=f"auction_info_{auction.id}",
                )
            ]
        )

        # Puja actual y estado del usuario
        if user_highest_bid:
            if user_highest_bid == auction.current_price:
                status_text = f"🥇 ¡Estás Ganando! Puja: {auction.current_price:,}{self.EMOJIS['besitos']}"
            else:
                status_text = f"💸 Te Superaron. Nueva puja: {auction.current_price:,}{self.EMOJIS['besitos']}"
        else:
            status_text = (
                f"💰 Puja Actual: {auction.current_price:,}{self.EMOJIS['besitos']}"
            )

        buttons.append(
            [
                InlineKeyboardButton(
                    status_text, callback_data=f"auction_info_{auction.id}"
                )
            ]
        )

        # Botones de puja - opciones rápidas y claras
        if auction.status.value == "active":
            min_bid = auction.current_price + auction.min_bid_increment

            # Verificar si el usuario puede pujar
            if user.besitos >= min_bid:
                # Opciones de puja inteligentes
                quick_bids = self._calculate_smart_bid_options(auction, user.besitos)

                for i in range(0, len(quick_bids), 2):
                    row = []
                    for j in range(i, min(i + 2, len(quick_bids))):
                        bid_amount = quick_bids[j]
                        row.append(
                            InlineKeyboardButton(
                                f"Pujar {bid_amount:,}{self.EMOJIS['besitos']}",
                                callback_data=f"auction_bid_{auction.id}_{bid_amount}",
                            )
                        )
                    buttons.append(row)

                # Puja personalizada
                buttons.append(
                    [
                        InlineKeyboardButton(
                            f"✏️ Puja Personalizada (mín: {min_bid:,})",
                            callback_data=f"auction_custom_bid_{auction.id}",
                        )
                    ]
                )

                # Auto-puja para usuarios avanzados (nivel 10+)
                if user.level >= 10:
                    buttons.append(
                        [
                            InlineKeyboardButton(
                                f"🤖 Auto-Puja (Máximo)",
                                callback_data=f"auction_auto_bid_{auction.id}",
                            )
                        ]
                    )
            else:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            f"💸 Necesitas más {self.EMOJIS['besitos']} (tienes {user.besitos:,})",
                            callback_data="user_earn_besitos_help",
                        )
                    ]
                )

        # Acciones adicionales
        action_buttons = []
        action_buttons.append(
            InlineKeyboardButton(
                f"{self.EMOJIS['info']} Detalles",
                callback_data=f"auction_details_{auction.id}",
            )
        )

        # Solo mostrar "seguir" si no está siguiendo ya
        action_buttons.append(
            InlineKeyboardButton(
                f"👁️ Seguir Subasta", callback_data=f"auction_watch_{auction.id}"
            )
        )

        buttons.append(action_buttons)

        # Navegación
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{self.EMOJIS['back']} Otras Subastas",
                    callback_data="user_auctions",
                ),
                InlineKeyboardButton(
                    f"{self.EMOJIS['home']} Menú Principal",
                    callback_data="user_main_menu",
                ),
            ]
        )

        return InlineKeyboardMarkup(buttons)

    def profile_keyboard(self, user: User) -> InlineKeyboardMarkup:
        """Teclado de perfil - Información organizada y acciones claras"""
        buttons = []

        # Acciones principales del perfil
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{self.EMOJIS['stats']} Estadísticas Detalladas",
                    callback_data="profile_detailed_stats",
                ),
                InlineKeyboardButton(
                    f"{self.EMOJIS['bag']} Mi Mochila", callback_data="user_backpack"
                ),
            ]
        )

        # Configuración y personalización
        config_row = []
        config_row.append(
            InlineKeyboardButton(
                f"{self.EMOJIS['settings']} Configuración",
                callback_data="profile_settings",
            )
        )

        if user.level >= 5:
            config_row.append(
                InlineKeyboardButton(
                    f"{self.EMOJIS['friends']} Mis Logros",
                    callback_data="profile_achievements",
                )
            )

        buttons.append(config_row)

        # Información VIP si aplica
        if user.is_vip:
            buttons.append(
                [
                    InlineKeyboardButton(
                        f"{self.EMOJIS['vip']} Estado VIP - Ver Beneficios",
                        callback_data="profile_vip_status",
                    )
                ]
            )
        elif user.level >= 3:
            buttons.append(
                [
                    InlineKeyboardButton(
                        f"✨ ¿Cómo obtener VIP?", callback_data="profile_vip_info"
                    )
                ]
            )

        # Navegación
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{self.EMOJIS['home']} Menú Principal",
                    callback_data="user_main_menu",
                )
            ]
        )

        return InlineKeyboardMarkup(buttons)

    def backpack_keyboard(
        self,
        lore_pieces_count: int,
        has_combinations: bool = False,
        can_combine: bool = False,
    ) -> InlineKeyboardMarkup:
        """Teclado de mochila narrativa - Enfocado en la historia"""
        buttons = []

        if lore_pieces_count == 0:
            # Mochila vacía - guiar al usuario
            buttons.append(
                [
                    InlineKeyboardButton(
                        f"{self.EMOJIS['info']} Tu mochila está vacía",
                        callback_data="backpack_info",
                    )
                ]
            )

            buttons.append(
                [
                    InlineKeyboardButton(
                        f"{self.EMOJIS['missions']} Completa Misiones para Pistas",
                        callback_data="user_missions",
                    ),
                    InlineKeyboardButton(
                        f"{self.EMOJIS['play']} Juega para Descubrir",
                        callback_data="user_games",
                    ),
                ]
            )
        else:
            # Mostrar contenido de la mochila
            buttons.append(
                [
                    InlineKeyboardButton(
                        f"{self.EMOJIS['scroll']} Tienes {lore_pieces_count} pistas históricas",
                        callback_data="backpack_list_all",
                    )
                ]
            )

            # Organizar por categorías
            buttons.append(
                [
                    InlineKeyboardButton(
                        f"{self.EMOJIS['story']} Leer Historia Principal",
                        callback_data="backpack_story_main",
                    ),
                    InlineKeyboardButton(
                        f"{self.EMOJIS['secret']} Historias Secretas",
                        callback_data="backpack_story_secret",
                    ),
                ]
            )

            # Combinaciones si están disponibles
            if has_combinations:
                if can_combine:
                    buttons.append(
                        [
                            InlineKeyboardButton(
                                f"✨ ¡Combinar Pistas Disponible! {self.EMOJIS['key']}",
                                callback_data="backpack_combine",
                            )
                        ]
                    )
                else:
                    buttons.append(
                        [
                            InlineKeyboardButton(
                                f"{self.EMOJIS['info']} Ver Combinaciones Posibles",
                                callback_data="backpack_combinations_info",
                            )
                        ]
                    )

            # Progreso narrativo
            buttons.append(
                [
                    InlineKeyboardButton(
                        f"{self.EMOJIS['map']} Mi Progreso en la Historia",
                        callback_data="backpack_progress",
                    )
                ]
            )

        # Navegación
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{self.EMOJIS['home']} Menú Principal",
                    callback_data="user_main_menu",
                )
            ]
        )

        return InlineKeyboardMarkup(buttons)

    # ===== HELPER METHODS PARA UX =====

    def _create_progress_bar(self, current: int, total: int, length: int = 10) -> str:
        """Crea barra de progreso visual"""
        if total == 0:
            return "▱" * length

        filled = int((current / total) * length)
        return "▰" * filled + "▱" * (length - filled)

    def _get_missions_count_badge(self, user_id: int) -> str:
        """Badge con número de misiones activas"""
        # Esto se implementaría con una consulta real
        # Por ahora retornamos un placeholder
        return "🔴" if True else ""  # Indicador de nuevas misiones

    def _get_daily_gift_status(self, user: User) -> str:
        """Estado del regalo diario"""
        # Verificar si puede reclamar (implementar lógica real)
        can_claim = True  # Placeholder
        return "🆕" if can_claim else "⏳"

    def _get_mission_progress_emoji(self, user_mission) -> str:
        """Emoji de progreso de misión"""
        progress_percent = (
            user_mission.current_progress / user_mission.target_progress
        ) * 100

        if progress_percent == 0:
            return "⭕"
        elif progress_percent < 25:
            return "🔴"
        elif progress_percent < 50:
            return "🟠"
        elif progress_percent < 75:
            return "🟡"
        elif progress_percent < 100:
            return "🟢"
        else:
            return "✅"

    def _calculate_xp_for_next_level(self, current_level: int) -> int:
        """Calcula XP necesaria para siguiente nivel"""
        return (current_level + 1) ** 2 * 100

    def _format_auction_time_left(self, end_time) -> str:
        """Formatea tiempo restante de subasta de manera amigable"""
        from datetime import datetime

        now = datetime.utcnow()
        if end_time <= now:
            return "¡Terminada!"

        diff = end_time - now
        total_seconds = diff.total_seconds()

        if total_seconds < 3600:  # Menos de 1 hora
            minutes = int(total_seconds // 60)
            return f"{minutes}min"
        elif total_seconds < 86400:  # Menos de 1 día
            hours = int(total_seconds // 3600)
            return f"{hours}h"
        else:
            days = int(total_seconds // 86400)
            return f"{days}d"

    def _calculate_smart_bid_options(self, auction, user_besitos: int) -> List[int]:
        """Calcula opciones inteligentes de puja"""
        min_bid = auction.current_price + auction.min_bid_increment
        max_affordable = min(user_besitos, auction.buyout_price or user_besitos)

        # Opciones inteligentes
        options = []

        # Puja mínima
        if min_bid <= max_affordable:
            options.append(min_bid)

        # Puja agresiva (+50% del incremento)
        aggressive = auction.current_price + int(auction.min_bid_increment * 1.5)
        if aggressive <= max_affordable and aggressive not in options:
            options.append(aggressive)

        # Puja dominante (+100% del incremento)
        dominant = auction.current_price + (auction.min_bid_increment * 2)
        if dominant <= max_affordable and dominant not in options:
            options.append(dominant)

        # Buyout si existe y es asequible
        if auction.buyout_price and auction.buyout_price <= max_affordable:
            options.append(auction.buyout_price)

        return options[:3]  # Máximo 3 opciones

    def confirmation_keyboard(
        self,
        confirm_data: str,
        cancel_data: str,
        confirm_text: str = "✅ Confirmar",
        cancel_text: str = "❌ Cancelar",
    ) -> InlineKeyboardMarkup:
        """Teclado de confirmación estándar"""
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(confirm_text, callback_data=confirm_data),
                    InlineKeyboardButton(cancel_text, callback_data=cancel_data),
                ]
            ]
        )

    def back_to_menu_keyboard(
        self, menu_data: str = "user_main_menu", text: str = None
    ) -> InlineKeyboardMarkup:
        """Teclado simple de regreso al menú"""
        if not text:
            text = f"{self.EMOJIS['home']} Menú Principal"

        return InlineKeyboardMarkup(
            [[InlineKeyboardButton(text, callback_data=menu_data)]]
        )

    def pagination_keyboard(
        self,
        current_page: int,
        total_pages: int,
        base_callback: str,
        additional_buttons: List = None,
    ) -> InlineKeyboardMarkup:
        """Teclado de paginación intuitivo"""
        buttons = []

        # Información de página actual
        if total_pages > 1:
            buttons.append(
                [
                    InlineKeyboardButton(
                        f"📄 Página {current_page} de {total_pages}",
                        callback_data="page_info",
                    )
                ]
            )

            # Controles de navegación
            nav_buttons = []

            if current_page > 1:
                nav_buttons.append(
                    InlineKeyboardButton(
                        f"{self.EMOJIS['back']} Anterior",
                        callback_data=f"{base_callback}_{current_page - 1}",
                    )
                )

            if current_page < total_pages:
                nav_buttons.append(
                    InlineKeyboardButton(
                        f"Siguiente {self.EMOJIS['next']}",
                        callback_data=f"{base_callback}_{current_page + 1}",
                    )
                )

            if nav_buttons:
                buttons.append(nav_buttons)

        # Botones adicionales si se proporcionan
        if additional_buttons:
            for button_row in additional_buttons:
                buttons.append(button_row)

        return InlineKeyboardMarkup(buttons)


class AdminKeyboards:
    """Teclados para administradores - Enfocados en eficiencia"""

    def __init__(self):
        self.user_kb = UserKeyboards()
        self.EMOJIS = self.user_kb.EMOJIS

    def admin_main_keyboard(self) -> InlineKeyboardMarkup:
        """Panel principal de administración"""
        buttons = [
            [
                InlineKeyboardButton(
                    "👥 Gestión de Usuarios", callback_data="admin_users"
                ),
                InlineKeyboardButton(
                    "📺 Gestión de Canales", callback_data="admin_channels"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎯 Gestión de Misiones", callback_data="admin_missions"
                ),
                InlineKeyboardButton(
                    "🏆 Gestión de Subastas", callback_data="admin_auctions"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎮 Gestión de Juegos", callback_data="admin_games"
                ),
                InlineKeyboardButton(
                    "📖 Gestión de Historia", callback_data="admin_lore"
                ),
            ],
            [
                InlineKeyboardButton("📊 Estadísticas", callback_data="admin_stats"),
                InlineKeyboardButton("⚙️ Configuración", callback_data="admin_config"),
            ],
            [
                InlineKeyboardButton(
                    "🔔 Notificaciones", callback_data="admin_notifications"
                ),
                InlineKeyboardButton(
                    "💬 Mensajes Masivos", callback_data="admin_broadcast"
                ),
            ],
        ]

        return InlineKeyboardMarkup(buttons)

    def quick_actions_keyboard(self) -> InlineKeyboardMarkup:
        """Acciones rápidas para administradores"""
        buttons = [
            [
                InlineKeyboardButton(
                    "🚀 Misión Diaria", callback_data="admin_quick_daily_mission"
                ),
                InlineKeyboardButton(
                    "🎁 Regalo Masivo", callback_data="admin_quick_mass_gift"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📢 Anuncio Urgente", callback_data="admin_quick_announcement"
                ),
                InlineKeyboardButton(
                    "🔄 Refrescar Sistema", callback_data="admin_quick_refresh"
                ),
            ],
        ]

        return InlineKeyboardMarkup(buttons)
   