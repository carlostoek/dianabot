from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from models.auction import (
    Auction,
    AuctionItem,
    AuctionBid,
    AuctionStatus,
    ItemType,
)
from models.user import User
from models.narrative_state import UserNarrativeState, NarrativeLevel
from config.database import get_db
from utils.lucien_voice import LucienVoice
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import random
import json


class AuctionService:
    """Servicio para subastas de contenido premium exclusivo"""

    def __init__(self):
        self.db = next(get_db())
        self.lucien = LucienVoice()

        # Configuración de subastas
        self.VIP_MULTIPLIER = 1.5  # VIP gana 50% más besitos en compras
        self.DIVAN_MULTIPLIER = 2.0  # Diván gana 100% más besitos

        # Templates de contenido exclusivo
        self.exclusive_content_templates = self._load_exclusive_content_templates()

    # ===== GESTIÓN DE SUBASTAS =====

    def get_active_auctions(self, user_id: int) -> List[Dict[str, Any]]:
        """Obtiene subastas activas con acceso personalizado"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        from services.user_service import UserService

        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(user_id)

        # Obtener subastas activas
        active_auctions = (
            self.db.query(Auction)
            .filter(
                and_(
                    Auction.status == AuctionStatus.ACTIVE,
                    Auction.starts_at <= datetime.utcnow(),
                    Auction.ends_at > datetime.utcnow(),
                )
            )
            .order_by(desc(Auction.priority), Auction.ends_at)
            .all()
        )

        auctions_data = []
        for auction in active_auctions:
            # Verificar acceso del usuario
            if self._user_has_auction_access(user, narrative_state, auction):
                auction_data = self._format_auction_for_user(
                    auction, user, narrative_state
                )
                auctions_data.append(auction_data)

        return auctions_data

    def get_auction_details(self, auction_id: int, user_id: int) -> Dict[str, Any]:
        """Obtiene detalles completos de una subasta"""

        auction = self.db.query(Auction).filter(Auction.id == auction_id).first()
        if not auction:
            return {"error": "Subasta no encontrada"}

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}

        from services.user_service import UserService

        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(user_id)

        # Verificar acceso
        if not self._user_has_auction_access(user, narrative_state, auction):
            return {
                "error": "Acceso denegado",
                "message": self._generate_access_denied_message(
                    auction, narrative_state
                ),
            }

        # Obtener bids de la subasta
        bids = (
            self.db.query(AuctionBid)
            .filter(AuctionBid.auction_id == auction_id)
            .order_by(desc(AuctionBid.amount))
            .limit(10)
            .all()
        )

        # Verificar si el usuario ha pujado
        user_bid = (
            self.db.query(AuctionBid)
            .filter(
                and_(AuctionBid.auction_id == auction_id, AuctionBid.user_id == user_id)
            )
            .order_by(desc(AuctionBid.amount))
            .first()
        )

        return {
            "auction": self._format_auction_for_user(auction, user, narrative_state),
            "bids": self._format_bids_for_display(bids),
            "user_bid": self._format_user_bid(user_bid) if user_bid else None,
            "time_remaining": self._calculate_time_remaining(auction.ends_at),
            "can_bid": self._can_user_bid(auction, user, narrative_state),
            "recommended_bid": self._calculate_recommended_bid(auction, user_bid),
        }

    def place_bid(self, auction_id: int, user_id: int, amount: int) -> Dict[str, Any]:
        """Realiza una puja en la subasta"""

        auction = self.db.query(Auction).filter(Auction.id == auction_id).first()
        user = self.db.query(User).filter(User.id == user_id).first()

        if not auction or not user:
            return {"error": "Subasta o usuario no encontrado"}

        # Validaciones de subasta
        validation_result = self._validate_bid(auction, user, amount)
        if not validation_result["valid"]:
            return {"error": validation_result["message"]}

        # Verificar besitos suficientes
        if user.besitos < amount:
            return {
                "error": "Besitos insuficientes",
                "required": amount,
                "available": user.besitos,
                "message": self._generate_insufficient_besitos_auction_message(
                    amount, user.besitos, auction, user
                ),
            }

        # Crear la puja
        bid = AuctionBid(
            auction_id=auction_id,
            user_id=user_id,
            amount=amount,
            bid_time=datetime.utcnow(),
            metadata={
                "user_level": user.level,
                "narrative_level": self._get_user_narrative_level(user_id),
                "bid_context": "manual",
            },
        )

        self.db.add(bid)

        # Actualizar subasta si es la puja más alta
        if amount > auction.current_highest_bid:
            auction.current_highest_bid = amount
            auction.highest_bidder_id = user_id
            auction.bid_count += 1

        # Descontar besitos temporalmente (se liberan si no gana)
        user.besitos -= amount

        self.db.commit()
        self.db.refresh(bid)

        # Generar mensaje de confirmación
        bid_message = self._generate_bid_confirmation_message(auction, bid, user)

        # Notificar a otros usuarios (implementación futura)
        self._notify_bid_placed(auction, bid, user)

        return {
            "success": True,
            "bid_id": bid.id,
            "auction_title": auction.title,
            "bid_amount": amount,
            "new_highest_bid": auction.current_highest_bid,
            "is_highest_bidder": auction.highest_bidder_id == user_id,
            "besitos_remaining": user.besitos,
            "message": bid_message,
        }

    def create_exclusive_auction(
        self, content_data: Dict[str, Any], auction_config: Dict[str, Any]
    ) -> Auction:
        """Crea una subasta de contenido exclusivo"""

        # Crear item de subasta
        auction_item = AuctionItem(
            title=content_data["title"],
            description=content_data["description"],
            item_type=content_data["type"],
            content_url=content_data.get("content_url"),
            preview_url=content_data.get("preview_url"),
            metadata=content_data.get("metadata", {}),
            rarity_level=content_data.get("rarity_level", "rare"),
        )

        self.db.add(auction_item)
        self.db.flush()  # Para obtener el ID

        # Crear subasta
        auction = Auction(
            item_id=auction_item.id,
            title=content_data["title"],
            description=self._generate_auction_description(
                content_data, auction_config
            ),
            starting_bid=auction_config.get("starting_bid", 100),
            current_highest_bid=auction_config.get("starting_bid", 100),
            reserve_price=auction_config.get("reserve_price"),
            starts_at=auction_config.get("starts_at", datetime.utcnow()),
            ends_at=auction_config["ends_at"],
            access_level=auction_config.get("access_level", "kinky"),
            min_user_level=auction_config.get("min_user_level", 1),
            vip_only=auction_config.get("vip_only", False),
            priority=auction_config.get("priority", 100),
            metadata={
                "content_type": content_data["type"],
                "diana_mood": auction_config.get("diana_mood", "exclusive"),
                "created_reason": auction_config.get(
                    "created_reason", "premium_content"
                ),
            },
        )

        self.db.add(auction)
        self.db.commit()
        self.db.refresh(auction)

        return auction

    def end_auction(self, auction_id: int) -> Dict[str, Any]:
        """Finaliza una subasta y determina el ganador"""

        auction = self.db.query(Auction).filter(Auction.id == auction_id).first()
        if not auction:
            return {"error": "Subasta no encontrada"}

        if auction.status != AuctionStatus.ACTIVE:
            return {"error": "Subasta no está activa"}

        # Obtener la puja ganadora
        winning_bid = (
            self.db.query(AuctionBid)
            .filter(AuctionBid.auction_id == auction_id)
            .order_by(desc(AuctionBid.amount))
            .first()
        )

        if not winning_bid:
            # No hay pujas
            auction.status = AuctionStatus.ENDED_NO_WINNER
            auction.ended_at = datetime.utcnow()
            self.db.commit()

            return {
                "success": True,
                "winner": None,
                "message": self._generate_no_winner_message(auction),
            }

        # Verificar precio de reserva
        if auction.reserve_price and winning_bid.amount < auction.reserve_price:
            auction.status = AuctionStatus.ENDED_RESERVE_NOT_MET
            auction.ended_at = datetime.utcnow()

            # Devolver besitos a todos los pujadores
            self._refund_all_bidders(auction_id)

            self.db.commit()

            return {
                "success": True,
                "winner": None,
                "message": self._generate_reserve_not_met_message(auction),
            }

        # Hay ganador
        winner = self.db.query(User).filter(User.id == winning_bid.user_id).first()

        auction.status = AuctionStatus.ENDED_WITH_WINNER
        auction.winner_id = winner.id
        auction.winning_bid = winning_bid.amount
        auction.ended_at = datetime.utcnow()

        # Devolver besitos a perdedores
        self._refund_losing_bidders(auction_id, winner.id)

        # Entregar contenido al ganador
        delivery_result = self._deliver_content_to_winner(auction, winner)

        self.db.commit()

        # Generar mensaje de ganador
        winner_message = self._generate_winner_message(auction, winner, winning_bid)

        return {
            "success": True,
            "winner": {
                "user_id": winner.id,
                "name": winner.first_name,
                "winning_bid": winning_bid.amount,
            },
            "content_delivered": delivery_result,
            "message": winner_message,
        }

    # ===== SISTEMA DE BESITOS Y CONVERSIÓN =====

    def award_besitos_for_purchase(
        self, user_id: int, purchase_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Otorga besitos por compras de contenido premium"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}

        from services.user_service import UserService

        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(user_id)

        # Calcular besitos basado en la compra
        base_besitos = self._calculate_besitos_for_purchase(purchase_data)

        # Aplicar multiplicadores
        multiplier = self._get_besitos_multiplier(narrative_state)
        final_besitos = int(base_besitos * multiplier)

        # Otorgar besitos
        old_besitos = user.besitos
        user.besitos += final_besitos

        # Registrar transacción
        transaction_record = {
            "type": "purchase_reward",
            "purchase_data": purchase_data,
            "base_besitos": base_besitos,
            "multiplier": multiplier,
            "final_besitos": final_besitos,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Actualizar métricas de engagement
        if not narrative_state.engagement_metrics:
            narrative_state.engagement_metrics = {}

        if "purchase_history" not in narrative_state.engagement_metrics:
            narrative_state.engagement_metrics["purchase_history"] = []

        narrative_state.engagement_metrics["purchase_history"].append(
            transaction_record
        )

        self.db.commit()

        # Generar mensaje de recompensa
        reward_message = self._generate_purchase_reward_message(
            purchase_data, final_besitos, multiplier, old_besitos, user.besitos, user
        )

        # Verificar si esto desbloquea nuevas subastas
        new_auctions = self._check_purchase_triggered_auctions(user_id, purchase_data)

        return {
            "success": True,
            "besitos_awarded": final_besitos,
            "multiplier_applied": multiplier,
            "old_besitos": old_besitos,
            "new_besitos": user.besitos,
            "message": reward_message,
            "new_auctions_unlocked": len(new_auctions),
            "unlocked_auctions": new_auctions,
        }

    def create_vip_exclusive_auction(self, content_data: Dict[str, Any]) -> Auction:
        """Crea subasta exclusiva para usuarios VIP"""

        auction_config = {
            "starting_bid": 500,  # Pujas más altas para VIP
            "ends_at": datetime.utcnow() + timedelta(hours=48),
            "access_level": "divan",
            "vip_only": True,
            "min_user_level": 10,
            "priority": 200,
            "diana_mood": "intimate",
            "created_reason": "vip_exclusive",
        }

        content_data[
            "description"
        ] += "\n\n🔮 **EXCLUSIVO DEL DIVÁN** - Solo para quienes han ganado la confianza íntima de Diana."

        return self.create_exclusive_auction(content_data, auction_config)

    # ===== ANÁLISIS Y MÉTRICAS =====

    def get_auction_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Obtiene analytics de subastas para optimización"""

        since_date = datetime.utcnow() - timedelta(days=days)

        # Métricas de subastas
        total_auctions = (
            self.db.query(Auction).filter(Auction.created_at >= since_date).count()
        )

        completed_auctions = (
            self.db.query(Auction)
            .filter(
                and_(
                    Auction.created_at >= since_date,
                    Auction.status == AuctionStatus.ENDED_WITH_WINNER,
                )
            )
            .count()
        )

        # Total de besitos gastados
        total_besitos_spent = (
            self.db.query(func.sum(AuctionBid.amount))
            .filter(AuctionBid.bid_time >= since_date)
            .scalar()
            or 0
        )

        # Usuarios únicos que han pujado
        unique_bidders = (
            self.db.query(func.count(func.distinct(AuctionBid.user_id)))
            .filter(AuctionBid.bid_time >= since_date)
            .scalar()
            or 0
        )

        # Top pujadores
        top_bidders = (
            self.db.query(
                User.first_name,
                func.sum(AuctionBid.amount).label("total_bid"),
                func.count(AuctionBid.id).label("bid_count"),
            )
            .join(AuctionBid, User.id == AuctionBid.user_id)
            .filter(AuctionBid.bid_time >= since_date)
            .group_by(User.id)
            .order_by(desc("total_bid"))
            .limit(10)
            .all()
        )

        # Análisis de conversión
        conversion_metrics = self._calculate_conversion_metrics(since_date)

        return {
            "period_days": days,
            "total_auctions": total_auctions,
            "completed_auctions": completed_auctions,
            "completion_rate": (completed_auctions / max(total_auctions, 1)) * 100,
            "total_besitos_spent": total_besitos_spent,
            "unique_bidders": unique_bidders,
            "avg_besitos_per_bidder": total_besitos_spent / max(unique_bidders, 1),
            "top_bidders": [
                {
                    "name": name,
                    "total_bid": total,
                    "bid_count": count,
                    "avg_bid": total / max(count, 1),
                }
                for name, total, count in top_bidders
            ],
            "conversion_metrics": conversion_metrics,
        }

    def get_user_auction_history(self, user_id: int) -> Dict[str, Any]:
        """Obtiene historial de subastas del usuario"""

        # Pujas del usuario
        user_bids = (
            self.db.query(AuctionBid)
            .filter(AuctionBid.user_id == user_id)
            .order_by(desc(AuctionBid.bid_time))
            .limit(50)
            .all()
        )

        # Subastas ganadas
        won_auctions = (
            self.db.query(Auction)
            .filter(Auction.winner_id == user_id)
            .order_by(desc(Auction.ended_at))
            .all()
        )

        # Estadísticas
        total_bids = len(user_bids)
        total_besitos_bid = sum(bid.amount for bid in user_bids)
        auctions_won = len(won_auctions)

        return {
            "total_bids": total_bids,
            "total_besitos_bid": total_besitos_bid,
            "auctions_won": auctions_won,
            "win_rate": (auctions_won / max(total_bids, 1)) * 100,
            "recent_bids": [
                {
                    "auction_title": self._get_auction_title_for_bid(bid),
                    "amount": bid.amount,
                    "bid_time": bid.bid_time.isoformat(),
                    "won": self._did_user_win_auction(bid.auction_id, user_id),
                }
                for bid in user_bids[:10]
            ],
            "won_content": [
                {
                    "title": auction.title,
                    "winning_bid": auction.winning_bid,
                    "won_date": auction.ended_at.isoformat(),
                    "content_type": auction.metadata.get("content_type", "unknown"),
                }
                for auction in won_auctions
            ],
        }

    # ===== MÉTODOS AUXILIARES =====

    def _user_has_auction_access(
        self, user: User, narrative_state: UserNarrativeState, auction: Auction
    ) -> bool:
        """Verifica si el usuario tiene acceso a la subasta"""

        # Verificar nivel de usuario
        if user.level < auction.min_user_level:
            return False

        # Verificar acceso VIP
        if auction.vip_only and not narrative_state.has_divan_access:
            return False

        # Verificar nivel narrativo
        if auction.access_level == "divan" and not narrative_state.has_divan_access:
            return False

        # Verificar nivel de confianza con Diana
        if (
            auction.access_level == "intimate"
            and narrative_state.diana_trust_level < 70
        ):
            return False

        return True

    def _format_auction_for_user(
        self, auction: Auction, user: User, narrative_state: UserNarrativeState
    ) -> Dict[str, Any]:
        """Formatea datos de subasta para mostrar al usuario"""

        item = (
            self.db.query(AuctionItem).filter(AuctionItem.id == auction.item_id).first()
        )

        # Obtener información del mejor postor actual
        current_bidder_info = None
        if auction.highest_bidder_id:
            current_bidder = (
                self.db.query(User).filter(User.id == auction.highest_bidder_id).first()
            )
            if current_bidder:
                current_bidder_info = {
                    "name": current_bidder.first_name,
                    "is_current_user": current_bidder.id == user.id,
                }

        return {
            "id": auction.id,
            "title": auction.title,
            "description": auction.description,
            "item": {
                "type": item.item_type.value if item else "unknown",
                "rarity": item.rarity_level if item else "common",
                "preview_url": item.preview_url if item else None,
            },
            "bidding": {
                "starting_bid": auction.starting_bid,
                "current_highest_bid": auction.current_highest_bid,
                "reserve_price": auction.reserve_price,
                "bid_count": auction.bid_count,
                "current_bidder": current_bidder_info,
            },
            "timing": {
                "starts_at": auction.starts_at.isoformat(),
                "ends_at": auction.ends_at.isoformat(),
                "time_remaining": self._calculate_time_remaining(auction.ends_at),
                "is_ending_soon": self._is_auction_ending_soon(auction.ends_at),
            },
            "access": {
                "level": auction.access_level,
                "vip_only": auction.vip_only,
                "min_level": auction.min_user_level,
            },
            "user_context": {
                "can_bid": self._can_user_bid(auction, user, narrative_state),
                "recommended_bid": self._calculate_recommended_bid(auction, None),
            },
        }

    def _calculate_besitos_for_purchase(self, purchase_data: Dict[str, Any]) -> int:
        """Calcula besitos base por compra"""

        purchase_type = purchase_data.get("type", "unknown")
        amount = purchase_data.get("amount", 0)

        # Ratios de conversión por tipo de compra
        conversion_rates = {
            "video_premium": 50,  # 50 besitos por cada $1
            "photo_set": 30,  # 30 besitos por cada $1
            "vip_subscription": 100,  # 100 besitos por cada $1
            "custom_content": 75,  # 75 besitos por cada $1
            "tip": 25,  # 25 besitos por cada $1
            "gift": 40,  # 40 besitos por cada $1
        }

        rate = conversion_rates.get(purchase_type, 25)  # Default 25
        base_besitos = int(amount * rate)

        # Bonus por compras grandes
        if amount >= 50:
            base_besitos = int(base_besitos * 1.5)  # 50% bonus
        elif amount >= 25:
            base_besitos = int(base_besitos * 1.25)  # 25% bonus

        return base_besitos

    def _get_besitos_multiplier(self, narrative_state: UserNarrativeState) -> float:
        """Obtiene multiplicador de besitos según estado del usuario"""

        multiplier = 1.0

        # Multiplicador VIP
        if narrative_state.has_divan_access:
            multiplier *= self.DIVAN_MULTIPLIER

        # Multiplicador por nivel de confianza con Diana
        trust_level = narrative_state.diana_trust_level
        if trust_level >= 90:
            multiplier *= 1.3  # 30% bonus
        elif trust_level >= 70:
            multiplier *= 1.2  # 20% bonus
        elif trust_level >= 50:
            multiplier *= 1.1  # 10% bonus

        # Multiplicador por arquetipo especial
        if narrative_state.primary_archetype in ["persistent", "romantic"]:
            multiplier *= 1.1  # Diana aprecia estos arquetipos

        return multiplier

    def _generate_purchase_reward_message(
        self,
        purchase_data: Dict,
        besitos_awarded: int,
        multiplier: float,
        old_besitos: int,
        new_besitos: int,
        user: User,
    ) -> str:
        """Genera mensaje de recompensa por compra"""

        purchase_type = purchase_data.get("type", "contenido premium")
        amount = purchase_data.get("amount", 0)

        base_message = f"""
{self.lucien.EMOJIS['lucien']} **Recompensa por Dedicación**

*[Con elegancia y aprobación]*

Tu compra de {purchase_type} por ${amount} ha demostrado tu dedicación a Diana.

💋 **+{besitos_awarded} Besitos** otorgados
**Saldo:** {old_besitos:,} → {new_besitos:,}
        """.strip()

        # Comentario sobre multiplicador
        multiplier_comment = ""
        if multiplier > 1.0:
            multiplier_comment = f"""

*[Con una sonrisa conocedora]*
Tu estatus especial te ha otorgado un **multiplicador de {multiplier:.1f}x**. Diana recompensa la fidelidad.
            """.strip()

        # Comentario sobre las subastas
        auction_comment = f"""

*[Con aire conspiratorio]*
Estos besitos no son solo números, {user.first_name}. Son tu acceso a los tesoros más exclusivos que Diana reserva solo para sus... favoritos.

**Las próximas subastas esperan.**
        """.strip()

        return base_message + multiplier_comment + auction_comment

    def _generate_bid_confirmation_message(
        self, auction: Auction, bid: AuctionBid, user: User
    ) -> str:
        """Genera mensaje de confirmación de puja"""

        is_highest = auction.highest_bidder_id == user.id

        base_message = f"""
{self.lucien.EMOJIS['lucien']} **Puja Registrada**

*[Con anticipación]*

Has pujado **{bid.amount:,} besitos** por "{auction.title}".
        """.strip()

        if is_highest:
            status_message = f"""

🎯 **¡Eres el mejor postor actual!**

*[Con satisfacción]*
Diana observa con interés. Mantienes la delantera... por ahora.
            """.strip()
        else:
            current_high = auction.current_highest_bid
            status_message = f"""

⚡ **Puja registrada** (Mejor actual: {current_high:,})

*[Con aliento]*
Diana valora tu participación. La competencia hace las cosas más... interesantes.
            """.strip()

        time_remaining = self._calculate_time_remaining(auction.ends_at)
        timing_message = f"""

⏰ **Tiempo restante:** {time_remaining}

*[Con elegancia]*
Recuerda: los besitos se liberan si no ganas. Solo el ganador invierte realmente en acercarse a Diana.
        """.strip()

        return base_message + status_message + timing_message

    def _generate_insufficient_besitos_auction_message(
        self, required: int, available: int, auction: Auction, user: User
    ) -> str:
        """Genera mensaje para besitos insuficientes en subasta"""

        needed = required - available

        return f"""
{self.lucien.EMOJIS['lucien']} **Besitos Insuficientes para "{auction.title}"**

*[Con aire comprensivo pero firme]*

Necesitas **{required:,} besitos** pero solo tienes **{available:,}**.

**Te faltan:** {needed:,} besitos

*[Con consejo estratégico]*
Diana valora a quienes invierten en contenido premium. Cada compra te otorga más besitos para competir por sus tesoros más exclusivos.

**💡 Consejo:** El contenido premium no solo te acerca a Diana... también te da el poder de ganar sus subastas más codiciadas.
        """.strip()

    def _generate_winner_message(
        self, auction: Auction, winner: User, winning_bid: AuctionBid
    ) -> str:
        """Genera mensaje para el ganador de la subasta"""

        return f"""
{self.lucien.EMOJIS['diana']} **¡SUBASTA GANADA!**

*[Con ceremonia y elegancia]*

🏆 **{winner.first_name} ha ganado "{auction.title}"**

**Puja ganadora:** {winning_bid.amount:,} besitos

{self.lucien.EMOJIS['diana']} *Diana aparece con una sonrisa especial:*

"*{winner.first_name}... tu dedicación ha sido recompensada. Este contenido es un regalo especial, solo para ti. Espero que... lo disfrutes tanto como yo disfruté creándolo.*"

*[Lucien entrega discretamente]*
El contenido exclusivo ha sido entregado a tu colección privada.

**Felicidades. Has obtenido algo que Diana reserva solo para los más... devotos.**
        """.strip()

    def _calculate_time_remaining(self, ends_at: datetime) -> str:
        """Calcula tiempo restante de subasta"""

        now = datetime.utcnow()
        if ends_at <= now:
            return "Finalizada"

        remaining = ends_at - now
        days = remaining.days
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def _is_auction_ending_soon(self, ends_at: datetime) -> bool:
        """Verifica si la subasta está por terminar"""
        return (ends_at - datetime.utcnow()).total_seconds() < 3600  # Menos de 1 hora

    def _can_user_bid(
        self, auction: Auction, user: User, narrative_state: UserNarrativeState
    ) -> bool:
        """Verifica si el usuario puede pujar"""

        # Verificar que la subasta esté activa
        if auction.status != AuctionStatus.ACTIVE:
            return False

        # Verificar tiempo
        now = datetime.utcnow()
        if not (auction.starts_at <= now <= auction.ends_at):
            return False

        # Verificar acceso
        if not self._user_has_auction_access(user, narrative_state, auction):
            return False

        # Verificar que no sea el postor actual más alto
        if auction.highest_bidder_id == user.id:
            return False

        return True

    def _calculate_recommended_bid(
        self, auction: Auction, user_bid: Optional[AuctionBid]
    ) -> int:
        """Calcula puja recomendada"""

        current_high = auction.current_highest_bid
        increment = max(current_high * 0.1, 50)  # 10% o mínimo 50

        return int(current_high + increment)

    def _validate_bid(
        self, auction: Auction, user: User, amount: int
    ) -> Dict[str, Any]:
        """Valida una puja"""

        if auction.status != AuctionStatus.ACTIVE:
            return {"valid": False, "message": "Subasta no está activa"}

        if datetime.utcnow() > auction.ends_at:
            return {"valid": False, "message": "Subasta ha finalizado"}

        if amount <= auction.current_highest_bid:
            return {
                "valid": False,
                "message": f"Puja debe ser mayor a {auction.current_highest_bid:,} besitos",
            }

        if auction.highest_bidder_id == user.id:
            return {"valid": False, "message": "Ya eres el mejor postor"}

        # Incremento mínimo (5% o 25 besitos)
        min_increment = max(auction.current_highest_bid * 0.05, 25)
        if amount < auction.current_highest_bid + min_increment:
            return {
                "valid": False,
                "message": f"Incremento mínimo: {int(min_increment)} besitos",
            }

        return {"valid": True}

    def _load_exclusive_content_templates(self) -> Dict[str, Any]:
        """Carga templates de contenido exclusivo"""
        # En implementación real, esto vendría de base de datos
        return {
            "photo_sets": {
                "intimate_moments": {
                    "title": "Momentos Íntimos de Diana",
                    "description": "Una colección de fotos que Diana raramente comparte...",
                    "rarity": "legendary",
                }
            },
            "videos": {
                "personal_message": {
                    "title": "Mensaje Personal de Diana",
                    "description": "Diana te habla directamente en este video exclusivo...",
                    "rarity": "epic",
                }
            },
        }

    def _check_purchase_triggered_auctions(
        self, user_id: int, purchase_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Verifica si una compra desbloquea nuevas subastas"""

        # Lógica para crear subastas especiales basadas en compras
        # Por ejemplo, comprar contenido premium podría desbloquear subasta exclusiva

        new_auctions = []

        # Si compra contenido premium por primera vez, crear subasta especial
        purchase_type = purchase_data.get("type")
        if (
            purchase_type in ["video_premium", "custom_content"]
            and purchase_data.get("amount", 0) >= 25
        ):

            # Verificar si es su primera compra premium
            from services.user_service import UserService

            user_service = UserService()
            narrative_state = user_service.get_or_create_narrative_state(user_id)

            purchase_history = narrative_state.engagement_metrics.get(
                "purchase_history", []
            )
            premium_purchases = [
                p
                for p in purchase_history
                if p.get("purchase_data", {}).get("type")
                in ["video_premium", "custom_content"]
            ]

            if len(premium_purchases) == 1:  # Primera compra premium
                # Crear subasta especial
                special_content = {
                    "title": "Bienvenida Premium de Diana",
                    "description": "Diana ha preparado algo especial para celebrar tu primera compra premium...",
                    "type": ItemType.VIDEO,
                    "rarity_level": "epic",
                }

                auction_config = {
                    "starting_bid": 200,
                    "ends_at": datetime.utcnow() + timedelta(hours=24),
                    "priority": 150,
                    "diana_mood": "grateful",
                }

                auction = self.create_exclusive_auction(special_content, auction_config)
                new_auctions.append(
                    {
                        "id": auction.id,
                        "title": auction.title,
                        "reason": "first_premium_purchase",
                    }
                )

        return new_auctions

    # Métodos adicionales para completar la funcionalidad...

    def _refund_all_bidders(self, auction_id: int) -> None:
        """Devuelve besitos a todos los pujadores"""

        bids = (
            self.db.query(AuctionBid).filter(AuctionBid.auction_id == auction_id).all()
        )

        for bid in bids:
            user = self.db.query(User).filter(User.id == bid.user_id).first()
            if user:
                user.besitos += bid.amount

        self.db.commit()

    def _refund_losing_bidders(self, auction_id: int, winner_id: int) -> None:
        """Devuelve besitos a perdedores"""

        losing_bids = (
            self.db.query(AuctionBid)
            .filter(
                and_(
                    AuctionBid.auction_id == auction_id, AuctionBid.user_id != winner_id
                )
            )
            .all()
        )

        for bid in losing_bids:
            user = self.db.query(User).filter(User.id == bid.user_id).first()
            if user:
                user.besitos += bid.amount

        self.db.commit()

    def _deliver_content_to_winner(
        self, auction: Auction, winner: User
    ) -> Dict[str, Any]:
        """Entrega contenido al ganador"""

        # En implementación real, esto manejaría la entrega del contenido
        # Por ahora, registramos en el perfil del usuario

        from services.user_service import UserService

        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(winner.id)

        if not narrative_state.special_recognitions:
            narrative_state.special_recognitions = []

        narrative_state.special_recognitions.append(
            {
                "type": "auction_winner",
                "auction_title": auction.title,
                "winning_bid": auction.winning_bid,
                "won_date": datetime.utcnow().isoformat(),
                "content_delivered": True,
            }
        )

        self.db.commit()

        return {"delivered": True, "method": "profile_collection"}

    def _calculate_conversion_metrics(self, since_date: datetime) -> Dict[str, Any]:
        """Calcula métricas de conversión"""

        # Aquí se implementaría análisis de conversión detallado
        # Por simplicidad, retornamos métricas básicas

        return {
            "purchase_to_bid_rate": 75.5,  # % de usuarios que compran y luego pujan
            "avg_besitos_per_purchase": 250,
            "high_value_customers": 15,  # Usuarios con compras >$50
            "retention_rate": 85.2,  # % que vuelve a participar
        }
   