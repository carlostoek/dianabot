from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any

def create_start_keyboard(user, is_new: bool = False) -> InlineKeyboardMarkup:
    """Crear teclado de inicio personalizado"""
    buttons = []
    
    if is_new:
        buttons.extend([
            [InlineKeyboardButton("✨ Conocer a Diana", callback_data="narrative_1_1")],
            [InlineKeyboardButton("🎭 ¿Quién es Lucien?", callback_data="intro_lucien")],
            [InlineKeyboardButton("🔥 Explorar DianaBot", callback_data="intro_bot")]
        ])
    else:
        buttons.extend([
            [
                InlineKeyboardButton("👤 Mi Perfil", callback_data="user_profile"),
                InlineKeyboardButton("🎯 Misiones", callback_data="user_missions")
            ],
            [
                InlineKeyboardButton("🎮 Juegos", callback_data="user_games"),
                InlineKeyboardButton("🎒 Mochila", callback_data="user_backpack")
            ],
            [
                InlineKeyboardButton("🏪 Tienda de Lucien", callback_data="store_main"),
                InlineKeyboardButton("🏆 Subastas", callback_data="auction_main")
            ]
        ])
        
        if user.is_vip or user.level >= 5:
            buttons.append([InlineKeyboardButton("👑 Contenido VIP", callback_data="vip_content")])
    
    # Administradores
    if hasattr(user, 'is_admin') and user.is_admin:
        buttons.append([InlineKeyboardButton("🏛️ Panel Admin", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_narrative_keyboard(buttons_config: List[Dict]) -> InlineKeyboardMarkup:
    """Crear teclado para narrativa"""
    if isinstance(buttons_config, str):
        # Casos especiales
        if buttons_config == "vip_promotion":
            return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("💎 Obtener VIP", callback_data="vip_info")],
                [InlineKeyboardButton("🔙 Volver", callback_data="narrative_menu")]
            ])
    
    buttons = []
    for button_config in buttons_config:
        if isinstance(button_config, dict):
            buttons.append([InlineKeyboardButton(
                button_config["text"], 
                callback_data=button_config["callback"]
            )])
    
    # Siempre agregar navegación
    buttons.append([InlineKeyboardButton("📚 Menú Narrativa", callback_data="narrative_menu")])
    buttons.append([InlineKeyboardButton("🏠 Menú Principal", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_store_keyboard(user, featured_items: List = None, recommendations: List = None, purchase_success: bool = None) -> InlineKeyboardMarkup:
    """Crear teclado para la tienda"""
    buttons = []
    
    if purchase_success is True:
        buttons.extend([
            [InlineKeyboardButton("📦 Mi Inventario", callback_data="user_inventory")],
            [InlineKeyboardButton("🛒 Seguir Comprando", callback_data="store_main")]
        ])
    elif purchase_success is False:
        buttons.extend([
            [InlineKeyboardButton("💰 Ganar Besitos", callback_data="earn_besitos")],
            [InlineKeyboardButton("🔙 Volver a Tienda", callback_data="store_main")]
        ])
    else:
        # Menú principal de tienda
        buttons.extend([
            [
                InlineKeyboardButton("🔥 Destacados", callback_data="store_category_premium"),
                InlineKeyboardButton("🎬 Videos", callback_data="store_category_videos")
            ],
            [
                InlineKeyboardButton("📚 Guías", callback_data="store_category_guides"),
                InlineKeyboardButton("🌟 Experiencias", callback_data="store_category_experiences")
            ]
        ])
        
        if user.is_vip:
            buttons.append([InlineKeyboardButton("👑 Solo VIP", callback_data="store_category_vip_exclusive")])
        
        buttons.append([InlineKeyboardButton("📦 Mi Inventario", callback_data="user_inventory")])
    
    buttons.append([InlineKeyboardButton("🏠 Menú Principal", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_purchase_keyboard(item, user, can_afford: bool) -> InlineKeyboardMarkup:
    """Crear teclado para compra de item"""
    buttons = []
    
    if can_afford and item.stock != 0:
        buttons.append([InlineKeyboardButton(
            f"💳 Comprar por {item.price_besitos} 💰", 
            callback_data=f"purchase_{item.id}"
        )])
    
    buttons.extend([
        [InlineKeyboardButton("🔙 Volver", callback_data="store_main")],
        [InlineKeyboardButton("💰 ¿Cómo ganar besitos?", callback_data="earn_besitos_info")]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_trivia_keyboard(question_data: Dict) -> InlineKeyboardMarkup:
    """Crear teclado para trivia narrativa"""
    buttons = []
    
    for i, option in enumerate(question_data["options"]):
        buttons.append([InlineKeyboardButton(
            f"{chr(65+i)}. {option}", 
            callback_data=f"trivia_answer_{question_data['id']}_{i}"
        )])
    
    buttons.extend([
        [InlineKeyboardButton("💡 Pista", callback_data=f"trivia_hint_{question_data['id']}")],
        [InlineKeyboardButton("❌ Salir", callback_data="narrative_menu")]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_auction_keyboard(auction, user_bids: List = None) -> InlineKeyboardMarkup:
    """Crear teclado para subastas"""
    buttons = []
    
    if auction.is_active:
        min_bid = auction.current_price + 10
        buttons.extend([
            [InlineKeyboardButton(f"💰 Pujar {min_bid} besitos", callback_data=f"bid_{auction.id}_{min_bid}")],
            [InlineKeyboardButton("💎 Puja personalizada", callback_data=f"custom_bid_{auction.id}")]
        ])
    
    buttons.extend([
        [InlineKeyboardButton("📊 Ver historial", callback_data=f"auction_history_{auction.id}")],
        [InlineKeyboardButton("🔙 Volver", callback_data="auction_main")]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
  
