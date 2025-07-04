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
