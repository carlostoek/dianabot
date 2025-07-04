from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.store_service import StoreService
from services.user_service import UserService
from utils.keyboards import create_store_keyboard, create_purchase_keyboard

class StoreHandlers:
    def __init__(self):
        self.router = Router()
        self.store_service = StoreService()
        self.user_service = UserService()

    def register(self, dp):
        """Registrar handlers"""
        dp.include_router(self.router)
        
        self.router.callback_query.register(
            self.handle_store_main,
            F.data == "store_main"
        )
        self.router.callback_query.register(
            self.handle_store_category,
            F.data.startswith("store_category_")
        )
        self.router.callback_query.register(
            self.handle_item_details,
            F.data.startswith("item_")
        )
        self.router.callback_query.register(
            self.handle_purchase,
            F.data.startswith("purchase_")
        )

    async def handle_store_main(self, callback: CallbackQuery, user: dict):
        """Manejar menú principal de la tienda"""
        await callback.answer()
        
        # Obtener items destacados y recomendaciones
        featured_items = await self.store_service.get_featured_items()
        recommendations = await self.store_service.get_lucien_recommendations(user.id)
        
        store_text = f"""🏪 *Tienda de Lucien*

*Lucien aparece con elegancia...*

"Bienvenido a mi colección personal. Cada item ha sido... cuidadosamente seleccionado por Diana y por mí."

💰 **Tus besitos:** {user.besitos}
🎭 **Tu nivel:** {user.level}

🔥 **Destacados hoy:**"""

        for item in featured_items[:3]:
            store_text += f"\n• {item.name} - {item.price_besitos} 💰"
        
        if recommendations:
            store_text += f"\n\n💡 **Recomendaciones de Lucien para ti:**"
            for item in recommendations:
                store_text += f"\n• {item.name} - {item.price_besitos} 💰"
        
        keyboard = create_store_keyboard(user, featured_items, recommendations)
        
        await callback.message.edit_text(
            store_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def handle_store_category(self, callback: CallbackQuery, user: dict):
        """Manejar categorías de la tienda"""
        await callback.answer()
        
        category = callback.data.replace("store_category_", "")
        items = await self.store_service.get_store_items(category, user.role)
        
        category_names = {
            "premium": "Contenido Premium",
            "videos": "Videos Exclusivos",
            "guides": "Guías y Manuales",
            "experiences": "Experiencias Únicas",
            "vip_exclusive": "Solo VIP"
        }
        
        category_text = f"""📁 *{category_names.get(category, category.title())}*

*Lucien presenta la colección...*

"Diana ha sido muy específica sobre qué incluir aquí. Cada pieza cuenta una historia."

💰 **Tus besitos:** {user.besitos}

📦 **Items disponibles:**"""

        buttons = []
        
        for item in items:
            status = "✅" if user.besitos >= item.price_besitos else "❌"
            category_text += f"\n{status} **{item.name}**\n   💰 {item.price_besitos} besitos"
            
            buttons.append({
                "text": f"{item.name} ({item.price_besitos}💰)",
                "callback": f"item_{item.id}"
            })
        
        buttons.append({"text": "🔙 Volver a Tienda", "callback": "store_main"})
        
        keyboard = create_store_keyboard(user, items, [])
        
        await callback.message.edit_text(
            category_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def handle_item_details(self, callback: CallbackQuery, user: dict):
        """Mostrar detalles de un item"""
        await callback.answer()
        
        item_id = int(callback.data.replace("item_", ""))
        item = await self.store_service.get_item_by_id(item_id)
        
        if not item:
            await callback.answer("Item no encontrado", show_alert=True)
            return
        
        can_afford = user.besitos >= item.price_besitos
        
        item_text = f"""📦 *{item.name}*

{item.description}

💰 **Precio:** {item.price_besitos} besitos
💳 **Tus besitos:** {user.besitos}
📊 **Estado:** {'✅ Puedes comprarlo' if can_afford else '❌ Besitos insuficientes'}

🎭 **Mensaje de Lucien:**
"{self._get_lucien_item_comment(item, user)}"
"""

        if item.stock > 0:
            item_text += f"\n📦 **Stock:** {item.stock} disponibles"
        elif item.stock == 0:
            item_text += f"\n📦 **Stock:** ❌ Agotado"

        keyboard = create_purchase_keyboard(item, user, can_afford)
        
        await callback.message.edit_text(
            item_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    def _get_lucien_item_comment(self, item, user):
        """Generar comentario personalizado de Lucien sobre el item"""
        comments_by_category = {
            "premium": "Diana reserva esto para quienes han demostrado... dedicación verdadera.",
            "videos": "Pocas veces la he visto tan... expresiva como en este contenido.",
            "guides": "Conocimiento que Diana mismo utiliza. Úsalo sabiamente.",
            "experiences": "Una oportunidad de conectar con Diana de manera más... íntima."
        }
        
        base_comment = comments_by_category.get(item.category, "Un item que Diana aprecia especialmente.")
        
        # Personalización por nivel
        if user.level >= 10:
            return f"{base_comment} Y para alguien de tu nivel... será especialmente revelador."
        elif user.level >= 5:
            return f"{base_comment} Tu progreso te ha ganado el acceso a esto."
        else:
            return base_comment

    async def handle_purchase(self, callback: CallbackQuery, user: dict):
        """Procesar compra de item"""
        await callback.answer()
        
        item_id = int(callback.data.replace("purchase_", ""))
        result = await self.store_service.purchase_item(user.id, item_id)
        
        if result["success"]:
            success_text = f"""🎉 *¡Compra Realizada!*

{result['message']}

💰 **Besitos restantes:** {result['remaining_besitos']}

🎭 **Lucien:**
"Excelente elección. Diana estará... complacida de que hayas adquirido esto."

📦 **Tu compra:**
{result['item'].name}

💌 *El contenido ha sido enviado a tu inventario personal.*"""

            keyboard = create_store_keyboard(user, [], [], purchase_success=True)
            
        else:
            success_text = f"""❌ *Error en la Compra*

{result['message']}

🎭 **Lucien:**
"Disculpas, pero parece que hay un... inconveniente. Quizás necesites más besitos o el item ya no está disponible."

💡 **Sugerencia:** Gana más besitos completando misiones o jugando."""

            keyboard = create_store_keyboard(user, [], [], purchase_success=False)
        
        await callback.message.edit_text(
            success_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
