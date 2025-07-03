from typing import Dict, List, Optional
from sqlalchemy import and_
from models.menu_config import MenuConfig, MenuButton
from config.database import get_db


class MenuService:
    """Servicio para gestión de menús dinámicos"""

    def __init__(self):
        self.db = next(get_db())

    def get_menu_for_user(
        self, menu_key: str, user_role: str, user_level: int
    ) -> Optional[Dict]:
        """Obtiene configuración de menú para un usuario específico"""
        try:
            menu_config = (
                self.db.query(MenuConfig)
                .filter(
                    MenuConfig.menu_key == menu_key,
                    MenuConfig.user_role == user_role,
                    MenuConfig.min_level <= user_level,
                    MenuConfig.max_level >= user_level,
                    MenuConfig.is_active.is_(True),
                )
                .first()
            )

            if not menu_config:
                return None

            buttons = (
                self.db.query(MenuButton)
                .filter(
                    MenuButton.menu_config_id == menu_config.id,
                    MenuButton.min_level <= user_level,
                    MenuButton.is_active.is_(True),
                )
                .order_by(MenuButton.position_row, MenuButton.position_col)
                .all()
            )

            return {
                "title": menu_config.title,
                "description": menu_config.description,
                "buttons": [
                    {
                        "text": btn.button_text,
                        "callback_data": btn.callback_data,
                        "row": btn.position_row,
                        "col": btn.position_col,
                    }
                    for btn in buttons
                    if self._user_can_see_button(btn, user_role, user_level)
                ],
            }
        except Exception as e:
            print(f"Error getting menu for user: {e}")
            return None

    def _user_can_see_button(
        self, button: MenuButton, user_role: str, user_level: int
    ) -> bool:
        role_hierarchy = {"free": 0, "vip": 1, "admin": 2}
        required_role_level = role_hierarchy.get(button.required_role, 0)
        user_role_level = role_hierarchy.get(user_role, 0)
        return user_role_level >= required_role_level and user_level >= button.min_level

    def create_default_menus(self) -> None:
        """Crea menús por defecto del sistema"""
        try:
            free_menu = MenuConfig(
                menu_key="main_menu_free",
                title="🎭 DianaBot - Menú Principal",
                description=(
                    "*Lucien te recibe...*\n\n\"Bienvenido al mundo de Diana. Veo que eres nuevo aquí...\""
                ),
                user_role="free",
                buttons_config={
                    "show_vip_info": True,
                    "show_premium_teasers": True,
                    "limit_features": True,
                },
            )

            vip_menu = MenuConfig(
                menu_key="main_menu_vip",
                title="🎭 DianaBot - Menú VIP",
                description=(
                    "*Lucien hace una reverencia elegante...*\n\n\"Ah, un miembro VIP. Diana estará complacida...\""
                ),
                user_role="vip",
                buttons_config={
                    "show_exclusive_content": True,
                    "show_premium_features": True,
                    "hide_vip_promotion": True,
                },
            )

            self.db.add_all([free_menu, vip_menu])
            self.db.commit()

            free_buttons = [
                MenuButton(
                    menu_config_id=free_menu.id,
                    button_text="👤 Mi Perfil",
                    callback_data="user_profile",
                    position_row=0,
                    position_col=0,
                ),
                MenuButton(
                    menu_config_id=free_menu.id,
                    button_text="🎯 Misiones",
                    callback_data="user_missions",
                    position_row=0,
                    position_col=1,
                ),
                MenuButton(
                    menu_config_id=free_menu.id,
                    button_text="🎮 Juegos Básicos",
                    callback_data="user_games_free",
                    position_row=1,
                    position_col=0,
                ),
                MenuButton(
                    menu_config_id=free_menu.id,
                    button_text="🎁 Regalo Diario",
                    callback_data="user_daily_gift",
                    position_row=1,
                    position_col=1,
                ),
                MenuButton(
                    menu_config_id=free_menu.id,
                    button_text="💎 ¿Cómo ser VIP?",
                    callback_data="vip_promotion",
                    position_row=2,
                    position_col=0,
                ),
                MenuButton(
                    menu_config_id=free_menu.id,
                    button_text="📢 Canal VIP Info",
                    callback_data="vip_channel_info",
                    position_row=2,
                    position_col=1,
                ),
            ]

            vip_buttons = [
                MenuButton(
                    menu_config_id=vip_menu.id,
                    button_text="👤 Mi Perfil VIP",
                    callback_data="user_profile_vip",
                    position_row=0,
                    position_col=0,
                ),
                MenuButton(
                    menu_config_id=vip_menu.id,
                    button_text="🎯 Misiones Premium",
                    callback_data="user_missions_vip",
                    position_row=0,
                    position_col=1,
                ),
                MenuButton(
                    menu_config_id=vip_menu.id,
                    button_text="🎮 Juegos Completos",
                    callback_data="user_games",
                    position_row=1,
                    position_col=0,
                ),
                MenuButton(
                    menu_config_id=vip_menu.id,
                    button_text="🎒 Mochila Narrativa",
                    callback_data="user_backpack",
                    position_row=1,
                    position_col=1,
                ),
                MenuButton(
                    menu_config_id=vip_menu.id,
                    button_text="🏆 Subastas VIP",
                    callback_data="user_auctions",
                    position_row=2,
                    position_col=0,
                ),
                MenuButton(
                    menu_config_id=vip_menu.id,
                    button_text="👑 Contenido Exclusivo",
                    callback_data="vip_exclusive_content",
                    position_row=2,
                    position_col=1,
                ),
                MenuButton(
                    menu_config_id=vip_menu.id,
                    button_text="🏆 Ranking",
                    callback_data="user_leaderboard",
                    position_row=3,
                    position_col=0,
                ),
            ]

            self.db.add_all(free_buttons + vip_buttons)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error creating default menus: {e}")

