from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import User, Transaction, Purchase, StoreItem
from config.database import get_db
from datetime import datetime, timedelta
from typing import Dict, List

class EconomyService:
    
    async def create_transaction(self, user_id: int, transaction_type: str, amount: int, description: str = "", reference_id: str = None):
        """Crear registro de transacción"""
        async for db in get_db():
            transaction = Transaction(
                user_id=user_id,
                type=transaction_type,
                amount=amount,
                description=description,
                reference_id=reference_id
            )
            db.add(transaction)
            await db.commit()
            return transaction

    async def track_activity(self, user_id: int, activity_type: str):
        """Rastrear actividad del usuario para recompensas"""
        activity_rewards = {
            "Message": 1,  # 1 besito por mensaje
            "CallbackQuery": 2,  # 2 besitos por interacción
            "channel_reaction": 5,  # 5 besitos por reacción en canal
            "trivia_participation": 10  # 10 besitos por participar en trivia
        }
        
        reward = activity_rewards.get(activity_type, 0)
        if reward > 0:
            from services.user_service import UserService
            user_service = UserService()
            await user_service.add_besitos(user_id, reward, f"Actividad: {activity_type}")

    async def calculate_purchase_cashback(self, user_id: int, purchase_amount: float) -> int:
        """Calcular cashback por compra externa"""
        from config.settings import Settings
        settings = Settings()
        
        cashback_besitos = int(purchase_amount * settings.PURCHASE_CASHBACK_RATE)
        
        # Bonus por nivel VIP
        async for db in get_db():
            user = await db.get(User, user_id)
            if user and user.is_vip:
                cashback_besitos = int(cashback_besitos * 1.5)  # 50% bonus para VIP
        
        return cashback_besitos

    async def process_external_purchase(self, user_id: int, purchase_data: dict) -> dict:
        """Procesar compra externa y otorgar cashback"""
        amount = purchase_data.get("amount", 0)
        description = purchase_data.get("description", "Compra externa")
        
        cashback = await self.calculate_purchase_cashback(user_id, amount)
        
        if cashback > 0:
            from services.user_service import UserService
            user_service = UserService()
            await user_service.add_besitos(user_id, cashback, f"Cashback: {description}")
            
            await self.create_transaction(
                user_id, "earn", cashback, f"Cashback: {description}", 
                purchase_data.get("reference_id")
            )
        
        return {
            "success": True,
            "cashback_besitos": cashback,
            "message": f"¡Recibiste {cashback} besitos de cashback!"
        }

    async def get_user_economy_stats(self, user_id: int) -> dict:
        """Obtener estadísticas económicas del usuario"""
        async for db in get_db():
            user = await db.get(User, user_id)
            if not user:
                return {}
            
            # Transacciones del último mes
            last_month = datetime.now() - timedelta(days=30)
            
            earned_result = await db.execute(
                select(func.sum(Transaction.amount))
                .where(
                    Transaction.user_id == user_id,
                    Transaction.type == "earn",
                    Transaction.created_at >= last_month
                )
            )
            earned_month = earned_result.scalar() or 0
            
            spent_result = await db.execute(
                select(func.sum(Transaction.amount))
                .where(
                    Transaction.user_id == user_id,
                    Transaction.type == "spend",
                    Transaction.created_at >= last_month
                )
            )
            spent_month = spent_result.scalar() or 0
            
            return {
                "current_besitos": user.besitos,
                "total_earned": user.total_earned,
                "total_spent": user.total_spent,
                "earned_this_month": earned_month,
                "spent_this_month": spent_month,
                "net_worth": user.total_earned - user.total_spent
            }

    async def get_transaction_history(self, user_id: int, limit: int = 20) -> List[Transaction]:
        """Obtener historial de transacciones"""
        async for db in get_db():
            result = await db.execute(
                select(Transaction)
                .where(Transaction.user_id == user_id)
                .order_by(Transaction.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()

    async def create_referral_bonus(self, referrer_id: int, referred_id: int) -> dict:
        """Crear bonus por referido"""
        bonus_amount = 200  # 200 besitos por referido
        
        from services.user_service import UserService
        user_service = UserService()
        
        # Bonus para quien refiere
        await user_service.add_besitos(
            referrer_id, bonus_amount, 
            f"Bonus por referir usuario {referred_id}"
        )
        
        # Bonus para el referido
        await user_service.add_besitos(
            referred_id, bonus_amount // 2, 
            "Bonus de bienvenida por referido"
        )
        
        return {
            "referrer_bonus": bonus_amount,
            "referred_bonus": bonus_amount // 2
        }
      
