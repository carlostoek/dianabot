from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Enum,
    JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base
import enum


class AuctionStatus(enum.Enum):
    SCHEDULED = "scheduled"  # Programada para el futuro
    ACTIVE = "active"  # En curso
    ENDED = "ended"  # Terminada
    CANCELLED = "cancelled"  # Cancelada
    PAUSED = "paused"  # Pausada temporalmente


class AuctionType(enum.Enum):
    NORMAL = "normal"  # Subasta normal
    SEALED_BID = "sealed"  # Ofertas selladas
    DUTCH = "dutch"  # Subasta holandesa (precio baja)
    RESERVE = "reserve"  # Con precio de reserva


class ItemType(enum.Enum):
    VIP_ACCESS = "vip_access"
    CUSTOM_ROLE = "custom_role"
    EXCLUSIVE_CONTENT = "exclusive_content"
    BESITOS = "besitos"
    LORE_PIECE = "lore_piece"
    CUSTOM_ITEM = "custom_item"


class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Configuración
    auction_type = Column(Enum(AuctionType), default=AuctionType.NORMAL)
    status = Column(Enum(AuctionStatus), default=AuctionStatus.SCHEDULED)

    # Precios
    starting_price = Column(Integer, nullable=False)  # Precio inicial en besitos
    reserve_price = Column(Integer, nullable=True)  # Precio de reserva
    current_price = Column(Integer, nullable=False)  # Precio actual
    buyout_price = Column(Integer, nullable=True)  # Precio de compra inmediata

    # Configuración de pujas
    min_bid_increment = Column(Integer, default=10)  # Incremento mínimo
    max_bid_increment = Column(Integer, nullable=True)  # Incremento máximo

    # Restricciones
    vip_only = Column(Boolean, default=True)
    min_level_required = Column(Integer, default=1)
    max_participants = Column(Integer, nullable=True)

    # Tiempo
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    auto_extend = Column(
        Boolean, default=True
    )  # Extender si hay puja en últimos minutos
    extension_time = Column(Integer, default=300)  # Segundos de extensión

    # Ganador
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    winning_bid = Column(Integer, nullable=True)

    # Metadatos
    item_data = Column(JSON)  # Información específica del item
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    bids = relationship(
        "AuctionBid", back_populates="auction", order_by="AuctionBid.amount.desc()"
    )
    winner = relationship("User", foreign_keys=[winner_id])
    creator = relationship("User", foreign_keys=[created_by])
    items = relationship("AuctionItem", back_populates="auction")


class AuctionItem(Base):
    __tablename__ = "auction_items"

    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("auctions.id"), nullable=False)

    item_type = Column(Enum(ItemType), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    quantity = Column(Integer, default=1)

    # Datos específicos del item
    item_data = Column(JSON)  # ej: {"vip_days": 30, "role_name": "Collector"}

    # Estado
    is_delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime, nullable=True)

    # Relación
    auction = relationship("Auction", back_populates="items")


class AuctionBid(Base):
    __tablename__ = "auction_bids"

    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("auctions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    amount = Column(Integer, nullable=False)
    is_auto_bid = Column(Boolean, default=False)  # Si es puja automática
    max_auto_bid = Column(Integer, nullable=True)  # Límite de puja automática

    # Estado
    is_winning = Column(Boolean, default=False)
    is_refunded = Column(Boolean, default=False)

    # Metadatos
    bid_data = Column(JSON)  # Información adicional
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    auction = relationship("Auction", back_populates="bids")
    user = relationship("User", back_populates="auction_bids")


class AuctionWatch(Base):
    __tablename__ = "auction_watches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    auction_id = Column(Integer, ForeignKey("auctions.id"), nullable=False)

    notify_on_outbid = Column(Boolean, default=True)
    notify_on_ending = Column(Boolean, default=True)
    notify_minutes_before = Column(Integer, default=30)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    user = relationship("User")
    auction = relationship("Auction")
   