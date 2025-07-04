from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database.models import StoreItem, Purchase, User
from config.database import get_db
from typing import List, Optional

class StoreService:
    
    async def get_store_items(self, category: str = None, user_role: str = "free") -> List[StoreItem]:
        """Obtener items de la tienda"""
        async for db in get_db():
            query = select(StoreItem).where(StoreItem.is_active == True)
            
            if category:
                query = query.where(StoreItem.category == category)
            
            # Filtrar por rol de usuario
            if user_role == "free":
                query = query.where(StoreItem.category != "vip_exclusive")
            
            result = await db.execute(query.order
            result = await db.execute(query.order_by(StoreItem.created_at.desc()))
            return result.scalars().all()

    async def get_item_by_id(self, item_id: int) -> Optional[StoreItem]:
        """Obtener item por ID"""
        async for db in get_db():
            return await db.get(StoreItem, item_id)

    async def purchase_item(self, user_id: int, item_id: int) -> dict:
        """Procesar compra de item"""
        async for db in get_db():
            item = await db.get(StoreItem, item_id)
            user = await db.get(User, user_id)
            
            if not item or not user:
                return {"success": False, "message": "Item o usuario no encontrado"}
            
            if not item.is_active:
                return {"success": False, "message": "Item no disponible"}
            
            if item.stock == 0:
                return {"success": False, "message": "Item agotado"}
            
            if user.besitos < item.price_besitos:
                return {"success": False, "message": "Besitos insuficientes"}
            
            # Procesar compra
            user.besitos -= item.price_besitos
            user.total_spent += item.price_besitos
            
            # Reducir stock si no es ilimitado
            if item.stock > 0:
                item.stock -= 1
            
            # Crear registro de compra
            purchase = Purchase(
                user_id=user_id,
                item_id=item_id,
                price_paid=item.price_besitos
            )
            db.add(purchase)
            
            await db.commit()
            
            # Crear transacción
            from services.economy_service import EconomyService
            economy_service = EconomyService()
            await economy_service.create_transaction(
                user_id, "spend", item.price_besitos, 
                f"Compra: {item.name}", str(purchase.id)
            )
            
            return {
                "success": True,
                "message": f"¡Compraste {item.name}!",
                "item": item,
                "remaining_besitos": user.besitos
            }

    async def get_user_purchases(self, user_id: int) -> List[Purchase]:
        """Obtener compras del usuario"""
        async for db in get_db():
            result = await db.execute(
                select(Purchase)
                .where(Purchase.user_id == user_id)
                .order_by(Purchase.created_at.desc())
            )
            return result.scalars().all()

    async def create_store_item(self, item_data: dict) -> StoreItem:
        """Crear nuevo item en la tienda"""
        async for db in get_db():
            item = StoreItem(
                name=item_data["name"],
                description=item_data.get("description", ""),
                price_besitos=item_data["price_besitos"],
                category=item_data.get("category", "general"),
                content_url=item_data.get("content_url"),
                content_type=item_data.get("content_type", "text"),
                stock=item_data.get("stock", -1)
            )
            db.add(item)
            await db.commit()
            await db.refresh(item)
            return item

    async def get_featured_items(self, limit: int = 5) -> List[StoreItem]:
        """Obtener items destacados"""
        async for db in get_db():
            result = await db.execute(
                select(StoreItem)
                .where(
                    and_(
                        StoreItem.is_active == True,
                        StoreItem.category.in_(["featured", "premium"])
                    )
                )
                .order_by(StoreItem.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()

    async def get_lucien_recommendations(self, user_id: int) -> List[StoreItem]:
        """Obtener recomendaciones personalizadas de Lucien"""
        async for db in get_db():
            user = await db.get(User, user_id)
            if not user:
                return []
            
            # Lógica de recomendación basada en nivel y arquetipo
            recommended_categories = []
            
            if user.level < 5:
                recommended_categories.extend(["beginner", "basic"])
            elif user.level < 10:
                recommended_categories.extend(["intermediate", "advanced"])
            else:
                recommended_categories.extend(["expert", "premium"])
            
            if user.user_archetype:
                recommended_categories.append(user.user_archetype)
            
            result = await db.execute(
                select(StoreItem)
                .where(
                    and_(
                        StoreItem.is_active == True,
                        StoreItem.category.in_(recommended_categories)
                    )
                )
                .limit(3)
            )
            return result.scalars().all()
            
