from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from services.channel_service import ChannelService
from services.user_service import UserService
from services.economy_service import EconomyService
from utils.keyboards import create_channel_keyboard
from utils.decorators import admin_required

class ChannelHandlers:
    def __init__(self):
        self.router = Router()
        self.channel_service = ChannelService()
        self.user_service = UserService()
        self.economy_service = EconomyService()

    def register(self, dp):
        """Registrar handlers"""
        dp.include_router(self.router)
        
        self.router.callback_query.register(
            self.handle_channel_reaction,
            F.data.startswith("channel_react_")
        )
        self.router.callback_query.register(
            self.handle_vip_promotion,
            F.data == "vip_info"
        )
        self.router.callback_query.register(
            self.handle_channel_management,
            F.data == "admin_channels"
        )
        self.router.callback_query.register(
            self.handle_create_post,
            F.data == "channel_create_post"
        )

    async def handle_channel_reaction(self, callback: CallbackQuery, user: dict):
        """Manejar reacciones en posts de canal"""
        await callback.answer()
        
        # Extraer datos de la reacción
        reaction_data = callback.data.split("_")
        post_id = int(reaction_data[2])
        reaction_type = reaction_data[3] if len(reaction_data) > 3 else "like"
        
        # Verificar si ya reaccionó
        existing_reaction = await self.channel_service.get_user_reaction(user.id, post_id)
        
        if existing_reaction:
            await callback.answer("Ya reaccionaste a este post", show_alert=True)
            return
        
        # Registrar reacción y otorgar puntos
        points_earned = await self.channel_service.process_reaction(
            user.id, post_id, reaction_type
        )
        
        if points_earned > 0:
            await self.user_service.add_besitos(
                user.id, points_earned, f"Reacción en canal: {reaction_type}"
            )
            
            await callback.answer(f"¡+{points_earned} besitos por tu reacción!", show_alert=True)
        else:
            await callback.answer("Reacción registrada", show_alert=True)

    async def handle_vip_promotion(self, callback: CallbackQuery, user: dict):
        """Mostrar información de promoción VIP"""
        await callback.answer()
        
        vip_text = f"""👑 *Únete al Diván - Canal VIP*

🌟 **Beneficios Exclusivos:**

📚 **Narrativa Avanzada:**
• Acceso a Niveles 4, 5 y 6 de la historia
• Interacciones más íntimas con Diana
• Contenido narrativo exclusivo

🏪 **Tienda Premium:**
• Descuentos especiales en items
• Acceso a productos VIP únicos
• Cashback aumentado (150% vs 100%)

🏆 **Subastas Exclusivas:**
• Participación en subastas VIP
• Contenido premium de Diana
• Experiencias personalizadas

💰 **Economía Mejorada:**
• Doble besitos en regalos diarios
• Bonus de experiencia (1.5x)
• Acceso prioritario a eventos

🎮 **Funciones Especiales:**
• Trivias narrativas avanzadas
• Badges exclusivos
• Ranking VIP separado

💎 **Precio:** Solo $15/mes

🎭 **Diana dice:**
"El Diván no es para todos... pero para aquellos que comprenden el valor de la exclusividad, las puertas están abiertas."

Tus besitos actuales: {user.besitos} 💰"""

        keyboard = create_channel_keyboard("vip_promotion", user)
        
        await callback.message.edit_text(
            vip_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    @admin_required
    async def handle_channel_management(self, callback: CallbackQuery, user: dict, admin: dict):
        """Gestión de canales"""
        await callback.answer()
        
        channel_stats = await self.channel_service.get_channel_stats()
        
        channels_text = f"""📢 *Gestión de Canales*

📊 **Estado de los Canales:**
• Los Kinkys (Free): {channel_stats.get('free_members', 0)} miembros
• El Diván (VIP): {channel_stats.get('vip_members', 0)} miembros

📈 **Engagement (Últimos 7 días):**
• Posts publicados: {channel_stats.get('posts_week', 0)}
• Total de reacciones: {channel_stats.get('reactions_week', 0)}
• Clicks en botones: {channel_stats.get('button_clicks_week', 0)}
• Nuevos miembros: {channel_stats.get('new_members_week', 0)}

🎯 **Métricas de Interacción:**
• Promedio reacciones por post: {channel_stats.get('avg_reactions_per_post', 0):.1f}
• Tasa de engagement: {channel_stats.get('engagement_rate', 0):.1f}%
• Posts más populares: {channel_stats.get('top_post_reactions', 0)} reacciones

🔧 **Herramientas Disponibles:**
• Crear post con botones interactivos
• Programar contenido automático
• Analizar rendimiento de posts
• Gestionar miembros"""

        keyboard = create_channel_keyboard("admin", user, admin)
        
        await callback.message.edit_text(
            channels_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    @admin_required
    async def handle_create_post(self, callback: CallbackQuery, user: dict, admin: dict):
        """Crear post interactivo para canal"""
        await callback.answer()
        
        post_text = f"""📝 *Crear Post Interactivo*

🎭 **Plantillas Disponibles para Posts:**

**1. Anuncio Narrativo**
- Diana revela nuevo contenido
- Botones: "Me interesa" / "Cuéntame más"
- Recompensa: 15 besitos por interacción

**2. Promoción de Tienda**
- Lucien presenta nuevos items
- Botones: "Ver tienda" / "Mis besitos"
- Recompensa: 10 besitos + descuento especial

**3. Evento de Subasta**
- Anuncio de nueva subasta
- Botones: "Participar" / "Ver detalles"
- Recompensa: 20 besitos por participar

**4. Trivia Narrativa**
- Diana hace una pregunta
- Botones: Opciones múltiples
- Recompensa: 25 besitos por respuesta correcta

**5. Mensaje de Diana**
- Contenido íntimo/personal
- Botones: Reacciones emocionales
- Recompensa: 30 besitos por reacción auténtica

🎯 **Configuración de Recompensas:**
• Reacción simple: 5-10 besitos
• Interacción con botón: 15-20 besitos
• Respuesta correcta: 25-30 besitos
• Participación en evento: 40-50 besitos

📊 **Métricas a trackear:**
• Número de interacciones
• Tiempo de engagement
• Conversión a acciones (compras/subastas)
• Comentarios y reacciones nativas"""

        keyboard = create_channel_keyboard("create_post", user, admin)
        
        await callback.message.edit_text(
            post_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
      )
      
