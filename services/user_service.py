from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import User, UserRole
from config.database import get_db
from datetime import datetime, timedelta
import asyncio

class UserService:
    async def get_or_create_user(self, user_data: dict) -> User:
        """Obtener o crear usuario"""
        async for db in get_db():
            result = await db.execute(
                select(User).where(User.telegram_id == user_data["telegram_id"])
            )
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    telegram_id=user_data["telegram_id"],
                    username=user_data.get("username"),
                    first_name=user_data["first_name"],
                    last_name=user_data.get("last_name"),
                    besitos=100,
                    level=1,
                    narrative_level=1
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            else:
                # Update last activity
                user.last_activity = datetime.now()
                await db.commit()
            
            return user

    async def update_user_activity(self, user_id: int):
        """Actualizar última actividad del usuario"""
        async for db in get_db():
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(last_activity=datetime.now())
            )
            await db.commit()

    async def add_besitos(self, user_id: int, amount: int, description: str = ""):
        """Agregar besitos al usuario"""
        async for db in get_db():
            user = await db.get(User, user_id)
            if user:
                user.besitos += amount
                user.total_earned += amount
                await db.commit()
                
                # Record transaction
                from services.economy_service import EconomyService
                economy_service = EconomyService()
                await economy_service.create_transaction(
                    user_id, "earn", amount, description
                )
                
                return user.besitos
            return 0

    async def spend_besitos(self, user_id: int, amount: int, description: str = "") -> bool:
        """Gastar besitos del usuario"""
        async for db in get_db():
            user = await db.get(User, user_id)
            if user and user.besitos >= amount:
                user.besitos -= amount
                user.total_spent += amount
                await db.commit()
                
                # Record transaction
                from services.economy_service import EconomyService
                economy_service = EconomyService()
                await economy_service.create_transaction(
                    user_id, "spend", amount, description
                )
                
                return True
            return False

    async def get_user_profile(self, user_id: int) -> dict:
        """Obtener perfil completo del usuario"""
        async for db in get_db():
            user = await db.get(User, user_id)
            if user:
                next_level_xp = self.calculate_xp_for_level(user.level + 1)
                progress = (user.experience / next_level_xp) * 100 if next_level_xp > 0 else 100
                
                return {
                    "user": user,
                    "next_level_xp": next_level_xp,
                    "xp_needed": next_level_xp - user.experience,
                    "progress_percentage": progress
                }
            return None

    def calculate_xp_for_level(self, level: int) -> int:
        """Calcular XP necesaria para un nivel"""
        return level * level * 100

    async def add_experience(self, user_id: int, xp: int):
        """Agregar experiencia y verificar subida de nivel"""
        async for db in get_db():
            user = await db.get(User, user_id)
            if user:
                user.experience += xp
                
                # Check level up
                while user.experience >= self.calculate_xp_for_level(user.level + 1):
                    user.level += 1
                    # Level up bonus
                    await self.add_besitos(user_id, user.level * 10, f"Bonus nivel {user.level}")
                
                await db.commit()
                return user.level

    async def get_leaderboard(self, limit: int = 10):
        """Obtener ranking de usuarios"""
        async for db in get_db():
            result = await db.execute(
                select(User)
                .where(User.is_active == True)
                .order_by(User.level.desc(), User.experience.desc())
                .limit(limit)
            )
            return result.scalars().all()

    async def get_user_rank(self, user_id: int) -> int:
        """Obtener posición del usuario en ranking"""
        async for db in get_db():
            user = await db.get(User, user_id)
            if user:
                result = await db.execute(
                    select(User.id)
                    .where(
                        (User.level > user.level) |
                        ((User.level == user.level) & (User.experience > user.experience))
                    )
                )
                return len(result.scalars().all()) + 1
            return 999

    async def can_claim_daily_gift(self, user_id: int) -> bool:
        """Verificar si puede reclamar regalo diario"""
        async for db in get_db():
            user = await db.get(User, user_id)
            if user:
                if not user.last_daily_claim:
                    return True
                return user.last_daily_claim.date() < datetime.now().date()
            return False

    async def claim_daily_gift(self, user_id: int) -> dict:
        """Reclamar regalo diario"""
        if not await self.can_claim_daily_gift(user_id):
            return {"success": False, "message": "Ya reclamaste tu regalo hoy"}
        
        async for db in get_db():
            user = await db.get(User, user_id)
            if user:
                base_reward = 50
                level_bonus = user.level * 10
                vip_multiplier = 2 if user.is_vip else 1
                total_besitos = (base_reward + level_bonus) * vip_multiplier
                
                user.besitos += total_besitos
                user.last_daily_claim = datetime.now()
                await db.commit()
                
                return {
                    "success": True,
                    "besitos": total_besitos,
                    "base": base_reward,
                    "bonus": level_bonus,
                    "multiplier": vip_multiplier
                }
            return {"success": False, "message": "Usuario no encontrado"}
                  
