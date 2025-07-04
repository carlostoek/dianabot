from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from database.models import Auction, AuctionBid, User
from config.database import get_db
from datetime import datetime, timedelta
from typing import List, Optional

class AuctionService:
    
    async def get_active_auctions(self) -> List[Auction]:
        """Obtener subastas activas"""
        async for db in get_db():
            now = datetime.now()
            result = await db.execute(
                select(Auction)
                .where(
                    and_(
                        Auction.is_active == True,
                        Auction.starts_at <= now,
                        Auction.ends_at > now
                    )
                )
                .order_by(Auction.ends_at.asc())
            )
            return result.scalars().all()

    async def get_upcoming_auctions(self) -> List[Auction]:
        """Obtener subastas próximas"""
        async for db in get_db():
            now = datetime.now()
            result = await db.execute(
                select(Auction)
                .where(
                    and_(
                        Auction.is_active == True,
                        Auction.starts_at > now
                    )
                )
                .order_by(Auction.starts_at.asc())
                .limit(5)
            )
            return result.scalars().all()

    async def place_bid(self, auction_id: int, user_id: int, amount: int) -> dict:
        """Realizar puja en subasta"""
        async for db in get_db():
            auction = await db.get(Auction, auction_id)
            user = await db.get(User, user_id)
            
            if not auction or not user:
                return {"success": False, "message": "Subasta o usuario no encontrado"}
            
            now = datetime.now()
            if now < auction.starts_at:
                return {"success": False, "message": "La subasta aún no ha comenzado"}
            
            if now > auction.ends_at:
                return {"success": False, "message": "La subasta ha terminado"}
            
            if amount <= auction.current_price:
                return {"success": False, "message": f"La puja debe ser mayor a {auction.current_price} besitos"}
            
            if user.besitos < amount:
                return {"success": False, "message": "Besitos insuficientes"}
            
            # Verificar si hay una puja anterior del mismo usuario
            previous_bid_result = await db.execute(
                select(AuctionBid)
                .where(
                    and_(
                        AuctionBid.auction_id == auction_id,
                        AuctionBid.user_id == user_id
                    )
                )
                .order_by(desc(AuctionBid.created_at))
                .limit(1)
            )
            previous_bid = previous_bid_result.scalar_one_or_none()
            
            # Devolver besitos de puja anterior
            if previous_bid:
                user.besitos += previous_bid.amount
            
            # Procesar nueva puja
            user.besitos -= amount
            auction.current_price = amount
            
            # Crear registro de puja
            bid = AuctionBid(
                auction_id=auction_id,
                user_id=user_id,
                amount=amount
            )
            db.add(bid)
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"¡Puja realizada por {amount} besitos!",
                "current_price": auction.current_price,
                "remaining_besitos": user.besitos
            }

    async def end_auction(self, auction_id: int) -> dict:
        """Finalizar subasta y determinar ganador"""
        async for db in get_db():
            auction = await db.get(Auction, auction_id)
            if not auction:
                return {"success": False, "message": "Subasta no encontrada"}
            
            # Obtener la puja más alta
            highest_bid_result = await db.execute(
                select(AuctionBid)
                .where(AuctionBid.auction_id == auction_id)
                .order_by(desc(AuctionBid.amount))
                .limit(1)
            )
            highest_bid = highest_bid_result.scalar_one_or_none()
            
            if highest_bid:
                auction.winner_id = highest_bid.user_id
                
                # Devolver besitos a todos los perdedores
                all_bids_result = await db.execute(
                    select(AuctionBid)
                    .where(
                        and_(
                            AuctionBid.auction_id == auction_id,
                            AuctionBid.user_id != highest_bid.user_id
                        )
                    )
                )
                losing_bids = all_bids_result.scalars().all()
                
                for bid in losing_bids:
                    user = await db.get(User, bid.user_id)
                    if user:
                        user.besitos += bid.amount
                
                # Crear transacción para el ganador
                from services.economy_service import EconomyService
                economy_service = EconomyService()
                await economy_service.create_transaction(
                    highest_bid.user_id, "spend", highest_bid.amount,
                    f"Ganador subasta: {auction.title}", str(auction.id)
                )
            
            auction.is_active = False
            await db.commit()
            
            return {
                "success": True,
                "winner_id": auction.winner_id,
                "winning_amount": highest_bid.amount if highest_bid else 0
            }

    async def create_auction(self, auction_data: dict) -> Auction:
        """Crear nueva subasta"""
        async for db in get_db():
            auction = Auction(
                title=auction_data["title"],
                description=auction_data.get("description", ""),
                starting_price=auction_data["starting_price"],
                current_price=auction_data["starting_price"],
                starts_at=auction_data["starts_at"],
                ends_at=auction_data["ends_at"]
            )
            db.add(auction)
            await db.commit()
            await db.refresh(auction)
            return auction

    async def get_user_bids(self, user_id: int) -> List[AuctionBid]:
        """Obtener pujas del usuario"""
        async for db in get_db():
            result = await db.execute(
                select(AuctionBid)
                .where(AuctionBid.user_id == user_id)
                .order_by(desc(AuctionBid.created_at))
            )
            return result.scalars().all()

    async def get_auction_bids(self, auction_id: int) -> List[AuctionBid]:
        """Obtener todas las pujas de una subasta"""
        async for db in get_db():
            result = await db.execute(
                select(AuctionBid)
                .where(AuctionBid.auction_id == auction_id)
                .order_by(desc(AuctionBid.amount))
            )
            return result.scalars().all()
              
