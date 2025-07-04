from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from services.user_service import UserService
from services.admin_service import AdminService
from services.analytics_service import AnalyticsService
from services.store_service import StoreService
from services.auction_service import AuctionService
from utils.keyboards import create_admin_keyboard
from utils.decorators import admin_required, super_admin_required

class AdminHandlers:
    def __init__(self):
        self.router = Router()
        self.user_service = UserService()
        self.admin_service = AdminService()
        self.analytics_service = AnalyticsService()
        self.store_service = StoreService()
        self.auction_service = AuctionService()

    def register(self, dp):
        """Registrar handlers"""
        dp.include_router(self.router)
        
        # Comandos admin
        self.router.message.register(
            self.handle_admin_panel,
            Command("admin")
        )
        
        # Callbacks admin
        self.router.callback_query.register(
            self.handle_admin_main,
            F.data == "admin_panel"
        )
        self.router.callback_query.register(
            self.handle_user_management,
            F.data == "admin_users"
        )
        self.router.callback_query.register(
            self.handle_analytics,
            F.data == "admin_analytics"
        )
        self.router.callback_query.register(
            self.handle_store_management,
            F.data == "admin_store"
        )
        self.router.callback_query.register(
            self.handle_auction_management,
            F.data == "admin_auctions"
        )
        self.router.callback_query.register(
            self.handle_broadcast,
            F.data == "admin_broadcast"
        )

    @admin_required
    async def handle_admin_panel(self, message: Message, user: dict, admin: dict):
        """Panel principal de administración"""
        admin_text = f"""🏛️ *Panel de Administración*

Bienvenido/a al Diván, {admin['name']}
Rol: {admin['role'].title()}

📊 **Estado del Sistema:**
• Usuarios totales: {await self.user_service.get_total_users_count()}
• Usuarios activos hoy: {await self.user_service.get_active_users_today()}
• VIP activos: {await self.user_service.get_vip_count()}

🎭 **Acceso disponible:**"""

        if admin['role'] == 'super_admin':
            admin_text += "\n• ✅ Acceso completo al sistema"
        else:
            admin_text += "\n• ✅ Gestión de usuarios y contenido"

        keyboard = create_admin_keyboard(admin)
        
        await message.answer(
            admin_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    @admin_required
    async def handle_admin_main(self, callback: CallbackQuery, user: dict, admin: dict):
        """Menú principal de administración"""
        await callback.answer()
        
        stats = await self.analytics_service.get_system_stats()
        
        admin_text = f"""🏛️ *Panel de Control*

📊 **Estadísticas en Tiempo Real:**
• Usuarios totales: {stats.get('total_users', 0)}
• Usuarios en línea: {stats.get('online_users', 0)}
• Transacciones hoy: {stats.get('transactions_today', 0)}
• Besitos en circulación: {stats.get('total_besitos', 0):,}

🎯 **Métricas de Actividad:**
• Narrativa completada: {stats.get('narrative_completed', 0)}%
• Compras realizadas: {stats.get('purchases_today', 0)}
• Subastas activas: {stats.get('active_auctions', 0)}

Selecciona un módulo para gestionar:"""

        keyboard = create_admin_keyboard(admin, main_panel=True)
        
        await callback.message.edit_text(
            admin_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    @admin_required
    async def handle_user_management(self, callback: CallbackQuery, user: dict, admin: dict):
        """Gestión de usuarios"""
        await callback.answer()
        
        user_stats = await self.analytics_service.get_user_analytics()
        
        users_text = f"""👥 *Gestión de Usuarios*

📊 **Estadísticas de Usuarios:**
• Total registrados: {user_stats.get('total_users', 0)}
• Nuevos esta semana: {user_stats.get('new_users_week', 0)}
• Usuarios VIP: {user_stats.get('vip_users', 0)}
• Usuarios activos: {user_stats.get('active_users', 0)}

🎯 **Segmentación por Nivel:**"""

        level_distribution = user_stats.get('level_distribution', {})
        for level, count in level_distribution.items():
            users_text += f"\n• Nivel {level}: {count} usuarios"

        users_text += f"\n\n🏆 **Top 5 Usuarios por Besitos:**"
        top_users = user_stats.get('top_users_besitos', [])
        for i, top_user in enumerate(top_users[:5], 1):
            users_text += f"\n{i}. {top_user['name']} - {top_user['besitos']:,} 💰"

        keyboard = create_admin_keyboard(admin, section="users")
        
        await callback.message.edit_text(
            users_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    @admin_required
    async def handle_analytics(self, callback: CallbackQuery, user: dict, admin: dict):
        """Dashboard de analytics"""
        await callback.answer()
        
        analytics = await self.analytics_service.get_detailed_analytics()
        
        analytics_text = f"""📊 *Analytics Detallado*

💰 **Economía del Sistema:**
• Besitos totales emitidos: {analytics.get('total_besitos_issued', 0):,}
• Besitos en circulación: {analytics.get('besitos_circulation', 0):,}
• Transacciones completadas: {analytics.get('total_transactions', 0)}
• Valor promedio de transacción: {analytics.get('avg_transaction', 0):.1f} 💰

🛒 **Tienda de Lucien:**
• Ventas totales: {analytics.get('total_sales', 0):,} 💰
• Items más vendidos: {analytics.get('top_selling_item', 'N/A')}
• Tasa de conversión: {analytics.get('conversion_rate', 0):.1f}%

🏆 **Subastas:**
• Subastas completadas: {analytics.get('completed_auctions', 0)}
• Valor promedio de puja: {analytics.get('avg_bid_value', 0):,} 💰
• Participación promedio: {analytics.get('avg_participation', 0):.1f}%

📚 **Narrativa:**
• Usuarios en Nivel 1: {analytics.get('level_1_users', 0)}
• Usuarios en Nivel 4+: {analytics.get('vip_level_users', 0)}
• Tasa de progresión: {analytics.get('progression_rate', 0):.1f}%"""

        keyboard = create_admin_keyboard(admin, section="analytics")
        
        await callback.message.edit_text(
            analytics_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    @admin_required
    async def handle_store_management(self, callback: CallbackQuery, user: dict, admin: dict):
        """Gestión de la tienda"""
        await callback.answer()
        
        store_stats = await self.analytics_service.get_store_analytics()
        
        store_text = f"""🏪 *Gestión de Tienda de Lucien*

📊 **Métricas de Ventas (Últimos 7 días):**
• Ingresos totales: {store_stats.get('revenue_week', 0):,} 💰
• Productos vendidos: {store_stats.get('items_sold_week', 0)}
• Clientes únicos: {store_stats.get('unique_customers_week', 0)}

💎 **Productos Destacados:**"""

        top_products = store_stats.get('top_products', [])
        for i, product in enumerate(top_products[:5], 1):
            store_text += f"\n{i}. {product['name']} - {product['sales']} ventas"

        store_text += f"""

📦 **Inventario:**
• Total de productos: {store_stats.get('total_products', 0)}
• Productos activos: {store_stats.get('active_products', 0)}
• Productos agotados: {store_stats.get('out_of_stock', 0)}

🎯 **Recomendaciones:**
• Productos para restockear: {store_stats.get('restock_needed', 0)}
• Nuevas categorías sugeridas: Content personalizado"""

        keyboard = create_admin_keyboard(admin, section="store")
        
        await callback.message.edit_text(
            store_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    @admin_required
    async def handle_auction_management(self, callback: CallbackQuery, user: dict, admin: dict):
        """Gestión de subastas"""
        await callback.answer()
        
        auction_stats = await self.analytics_service.get_auction_analytics()
        active_auctions = await self.auction_service.get_active_auctions()
        
        auction_text = f"""🏆 *Gestión de Subastas*

📊 **Estado Actual:**
• Subastas activas: {len(active_auctions)}
• Participantes únicos: {auction_stats.get('unique_participants', 0)}
• Valor total en juego: {auction_stats.get('total_bid_value', 0):,} 💰

🔥 **Subastas Activas:**"""

        for auction in active_auctions[:3]:
            time_left = (auction.ends_at - auction.created_at).total_seconds() / 3600
            auction_text += f"\n• {auction.title}: {auction.current_price:,} 💰 ({time_left:.1f}h restantes)"

        auction_text += f"""

📈 **Métricas de Rendimiento:**
• Tasa de participación: {auction_stats.get('participation_rate', 0):.1f}%
• Valor promedio de puja: {auction_stats.get('avg_bid', 0):,} 💰
• Subastas completadas esta semana: {auction_stats.get('completed_week', 0)}

🎯 **Próximas Subastas:**"""

        upcoming = await self.auction_service.get_upcoming_auctions()
        for auction in upcoming[:2]:
            hours_to_start = (auction.starts_at - auction.created_at).total_seconds() / 3600
            auction_text += f"\n• {auction.title} (en {hours_to_start:.1f}h)"

        keyboard = create_admin_keyboard(admin, section="auctions")
        
        await callback.message.edit_text(
            auction_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    @super_admin_required
    async def handle_broadcast(self, callback: CallbackQuery, user: dict, admin: dict):
        """Sistema de broadcast"""
        await callback.answer()
        
        broadcast_stats = await self.analytics_service.get_broadcast_stats()
        
        broadcast_text = f"""📢 *Sistema de Mensajes Masivos*

👥 **Audiencia Disponible:**
• Usuarios totales: {broadcast_stats.get('total_users', 0)}
• Usuarios activos (7 días): {broadcast_stats.get('active_users', 0)}
• Usuarios VIP: {broadcast_stats.get('vip_users', 0)}
• Usuarios por nivel narrativo:
  - Nivel 1-3: {broadcast_stats.get('free_users', 0)} usuarios
  - Nivel 4-6: {broadcast_stats.get('vip_narrative_users', 0)} usuarios

📊 **Historial de Broadcasts (Último mes):**
• Mensajes enviados: {broadcast_stats.get('messages_sent_month', 0)}
• Tasa de apertura: {broadcast_stats.get('open_rate', 0):.1f}%
• Tasa de interacción: {broadcast_stats.get('interaction_rate', 0):.1f}%

⚠️ **Importante:** Los mensajes masivos deben ser usados responsablemente para mantener el engagement y evitar que usuarios abandonen el bot.

🎭 **Plantillas Disponibles:**
• Anuncio de nueva función
• Promoción de tienda
• Evento especial
• Actualización narrativa"""

        keyboard = create_admin_keyboard(admin, section="broadcast")
        
        await callback.message.edit_text(
            broadcast_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
      )
      
