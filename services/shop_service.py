from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from models.shop import (
    ShopItem,
    ShopCategory,
    ShopPurchase,
    ShopItemType,
    ShopRarity,
)
from models.user import User
from models.narrative_state import UserNarrativeState, NarrativeLevel
from config.database import get_db
from utils.lucien_voice import LucienVoice
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import random
import json


class ShopService:
    """Servicio para la tienda exclusiva de Lucien con contenido único"""

    def __init__(self):
        self.db = next(get_db())
        self.lucien = LucienVoice()

        # Configuración de la tienda
        self.BESITOS_REWARD_RATES = {
            "common": 0.1,  # 10% de besitos de vuelta
            "rare": 0.15,  # 15% de besitos de vuelta
            "epic": 0.2,  # 20% de besitos de vuelta
            "legendary": 0.3,  # 30% de besitos de vuelta
            "mythical": 0.5,  # 50% de besitos de vuelta
        }

        # Multiplicadores por nivel narrativo
        self.NARRATIVE_MULTIPLIERS = {
            NarrativeLevel.NEWCOMER: 1.0,
            NarrativeLevel.LEVEL_1_KINKY: 1.1,
            NarrativeLevel.LEVEL_2_KINKY_DEEP: 1.2,
            NarrativeLevel.LEVEL_3_KINKY_FINAL: 1.3,
            NarrativeLevel.LEVEL_4_DIVAN_ENTRY: 1.5,
            NarrativeLevel.LEVEL_5_DIVAN_DEEP: 1.7,
            NarrativeLevel.LEVEL_6_DIVAN_SUPREME: 2.0,
        }

    # ===== GESTIÓN DE CATÁLOGO =====

    def get_shop_catalog(self, user_id: int) -> Dict[str, Any]:
        """Obtiene catálogo de tienda personalizado para el usuario"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}

        from services.user_service import UserService

        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(user_id)

        # Obtener categorías disponibles
        available_categories = self._get_available_categories(user, narrative_state)

        catalog = {
            "welcome_message": self._generate_shop_welcome_message(
                user, narrative_state
            ),
            "user_besitos": user.besitos,
            "user_access_level": self._get_user_shop_access_level(narrative_state),
            "categories": [],
        }

        for category in available_categories:
            category_items = self._get_category_items(
                category.id, user, narrative_state
            )

            if category_items:  # Solo mostrar categorías con items disponibles
                catalog["categories"].append(
                    {
                        "id": category.id,
                        "name": category.name,
                        "description": category.description,
                        "icon": category.icon,
                        "unlock_level": category.unlock_narrative_level,
                        "items": category_items,
                    }
                )

        # Ofertas especiales rotativas
        special_offers = self._get_special_offers(user, narrative_state)
        if special_offers:
            catalog["special_offers"] = special_offers

        # Items destacados por Lucien
        featured_items = self._get_lucien_featured_items(user, narrative_state)
        if featured_items:
            catalog["lucien_featured"] = featured_items

        return catalog

    def get_item_details(self, item_id: int, user_id: int) -> Dict[str, Any]:
        """Obtiene detalles completos de un item"""

        item = self.db.query(ShopItem).filter(ShopItem.id == item_id).first()
        if not item:
            return {"error": "Item no encontrado"}

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}

        from services.user_service import UserService

        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(user_id)

        # Verificar acceso
        if not self._user_has_item_access(user, narrative_state, item):
            return {
                "error": "Acceso denegado",
                "message": self._generate_access_denied_message(item, narrative_state),
            }

        # Calcular precio personalizado y besitos de recompensa
        personalized_pricing = self._calculate_personalized_pricing(
            item, user, narrative_state
        )

        return {
            "item": {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "long_description": item.long_description,
                "item_type": item.item_type.value,
                "rarity": item.rarity.value,
                "preview_media": item.preview_media_url,
                "tags": item.tags or [],
            },
            "pricing": personalized_pricing,
            "availability": {
                "in_stock": item.stock_quantity > 0 if item.stock_quantity else True,
                "stock_remaining": item.stock_quantity,
                "is_limited": item.is_limited_time,
                "expires_at": item.expires_at.isoformat() if item.expires_at else None,
            },
            "user_context": {
                "can_purchase": self._can_user_purchase(item, user, narrative_state),
                "already_owned": self._user_owns_item(user_id, item_id),
                "user_besitos": user.besitos,
            },
            "lucien_commentary": self._generate_item_commentary(item, narrative_state),
        }

    # ===== SISTEMA DE COMPRAS =====

    def purchase_item(
        self, item_id: int, user_id: int, quantity: int = 1
    ) -> Dict[str, Any]:
        """Realiza compra de item en la tienda"""

        item = self.db.query(ShopItem).filter(ShopItem.id == item_id).first()
        user = self.db.query(User).filter(User.id == user_id).first()

        if not item or not user:
            return {"error": "Item o usuario no encontrado"}

        from services.user_service import UserService

        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(user_id)

        # Validar compra
        validation_result = self._validate_purchase(
            item, user, narrative_state, quantity
        )
        if not validation_result["valid"]:
            return {"error": validation_result["message"]}

        # Calcular costo total
        pricing = self._calculate_personalized_pricing(item, user, narrative_state)
        total_cost = pricing["final_price"] * quantity

        # Verificar besitos suficientes
        if user.besitos < total_cost:
            return {
                "error": "Besitos insuficientes",
                "required": total_cost,
                "available": user.besitos,
                "message": self._generate_insufficient_besitos_shop_message(
                    total_cost, user.besitos, item, user
                ),
            }

        # Procesar compra
        purchase = ShopPurchase(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
            unit_price=pricing["final_price"],
            total_price=total_cost,
            besitos_rewarded=0,  # Se calcula después
            purchase_metadata={
                "user_level": user.level,
                "narrative_level": narrative_state.current_level.value,
                "applied_discount": pricing.get("discount_percentage", 0),
                "rarity_bonus": pricing.get("rarity_bonus", 0),
            },
        )

        # Descontar besitos
        user.besitos -= total_cost

        # Actualizar stock si aplica
        if item.stock_quantity is not None:
            item.stock_quantity -= quantity

        # Calcular besitos de recompensa
        reward_besitos = self._calculate_purchase_reward_besitos(
            item, total_cost, narrative_state
        )
        purchase.besitos_rewarded = reward_besitos

        # Otorgar besitos de recompensa
        user.besitos += reward_besitos

        # Entregar contenido
        delivery_result = self._deliver_item_content(item, user, purchase)

        # Registrar compra
        self.db.add(purchase)
        self.db.commit()
        self.db.refresh(purchase)

        # Actualizar métricas de engagement
        self._update_purchase_metrics(narrative_state, purchase)

        # Verificar desbloqueos por compra
        unlocks = self._check_purchase_unlocks(user, narrative_state, item, purchase)

        # Generar mensaje de confirmación
        confirmation_message = self._generate_purchase_confirmation_message(
            item, purchase, reward_besitos, user, delivery_result
        )

        return {
            "success": True,
            "purchase_id": purchase.id,
            "item_name": item.name,
            "quantity": quantity,
            "total_cost": total_cost,
            "besitos_rewarded": reward_besitos,
            "new_besitos_balance": user.besitos,
            "content_delivered": delivery_result,
            "unlocks": unlocks,
            "message": confirmation_message,
        }

    def get_user_collection(self, user_id: int) -> Dict[str, Any]:
        """Obtiene colección de items del usuario"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}

        # Obtener compras del usuario
        purchases = (
            self.db.query(ShopPurchase)
            .filter(ShopPurchase.user_id == user_id)
            .order_by(desc(ShopPurchase.purchased_at))
            .all()
        )

        collection = {
            "total_items": len(purchases),
            "total_spent": sum(p.total_price for p in purchases),
            "total_besitos_earned": sum(p.besitos_rewarded for p in purchases),
            "items_by_category": {},
            "recent_purchases": [],
            "rarity_distribution": {},
        }

        # Agrupar por categoría y rareza
        for purchase in purchases:
            item = (
                self.db.query(ShopItem).filter(ShopItem.id == purchase.item_id).first()
            )
            if item:
                # Por categoría
                category_name = item.category.name if item.category else "Sin categoría"
                if category_name not in collection["items_by_category"]:
                    collection["items_by_category"][category_name] = []

                collection["items_by_category"][category_name].append(
                    {
                        "name": item.name,
                        "rarity": item.rarity.value,
                        "purchased_at": purchase.purchased_at.isoformat(),
                        "quantity": purchase.quantity,
                    }
                )

                # Por rareza
                rarity = item.rarity.value
                if rarity not in collection["rarity_distribution"]:
                    collection["rarity_distribution"][rarity] = 0
                collection["rarity_distribution"][rarity] += purchase.quantity

        # Compras recientes
        for purchase in purchases[:10]:
            item = (
                self.db.query(ShopItem).filter(ShopItem.id == purchase.item_id).first()
            )
            if item:
                collection["recent_purchases"].append(
                    {
                        "item_name": item.name,
                        "quantity": purchase.quantity,
                        "cost": purchase.total_price,
                        "besitos_earned": purchase.besitos_rewarded,
                        "purchased_at": purchase.purchased_at.isoformat(),
                    }
                )

        # Mensaje de Lucien sobre la colección
        collection["lucien_commentary"] = self._generate_collection_commentary(
            collection, user
        )

        return collection

    # ===== SISTEMA DE OFERTAS ESPECIALES =====

    def create_flash_sale(
        self, items_config: List[Dict[str, Any]], duration_hours: int = 24
    ) -> Dict[str, Any]:
        """Crea oferta flash temporal"""

        flash_sale_items = []

        for item_config in items_config:
            item = (
                self.db.query(ShopItem)
                .filter(ShopItem.id == item_config["item_id"])
                .first()
            )
            if item:
                # Crear item temporal con descuento
                flash_item = ShopItem(
                    name=f"⚡ FLASH: {item.name}",
                    description=item.description,
                    long_description=f"🔥 OFERTA FLASH 🔥\n\n{item.long_description}",
                    base_price=int(
                        item.base_price * (1 - item_config.get("discount", 0.3))
                    ),
                    item_type=item.item_type,
                    rarity=item.rarity,
                    category_id=item.category_id,
                    content_data=item.content_data,
                    preview_media_url=item.preview_media_url,
                    is_limited_time=True,
                    expires_at=datetime.utcnow() + timedelta(hours=duration_hours),
                    stock_quantity=item_config.get("flash_stock", 50),
                    tags=(item.tags or []) + ["flash_sale"],
                    metadata={
                        "original_item_id": item.id,
                        "flash_discount": item_config.get("discount", 0.3),
                        "flash_sale": True,
                    },
                )

                self.db.add(flash_item)
                flash_sale_items.append(flash_item)

        self.db.commit()

        return {
            "success": True,
            "items_created": len(flash_sale_items),
            "duration_hours": duration_hours,
            "flash_sale_message": self._generate_flash_sale_announcement(
                flash_sale_items, duration_hours
            ),
        }

    def create_loyalty_rewards(self, user_id: int) -> Dict[str, Any]:
        """Crea recompensas de lealtad personalizadas"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}

        from services.user_service import UserService

        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(user_id)

        # Calcular métricas de lealtad
        total_purchases = (
            self.db.query(ShopPurchase).filter(ShopPurchase.user_id == user_id).count()
        )

        total_spent = (
            self.db.query(func.sum(ShopPurchase.total_price))
            .filter(ShopPurchase.user_id == user_id)
            .scalar()
            or 0
        )

        # Determinar tipo de recompensa
        loyalty_rewards = []

        if total_purchases >= 10:
            # Usuario leal - descuento permanente
            loyalty_rewards.append(
                {
                    "type": "permanent_discount",
                    "value": 15,  # 15% descuento
                    "description": "Descuento permanente del 15% por lealtad",
                }
            )

        if total_spent >= 5000:
            # Gran gastador - acceso VIP a items exclusivos
            loyalty_rewards.append(
                {
                    "type": "vip_access",
                    "description": "Acceso exclusivo a la sección VIP de la tienda",
                }
            )

        if narrative_state.diana_trust_level >= 70:
            # Alta confianza con Diana - items especiales
            loyalty_rewards.append(
                {
                    "type": "diana_special_items",
                    "description": "Items especiales creados por Diana solo para ti",
                }
            )

        return {
            "user_loyalty_level": self._calculate_loyalty_level(
                total_purchases, total_spent
            ),
            "rewards_available": loyalty_rewards,
            "stats": {
                "total_purchases": total_purchases,
                "total_spent": total_spent,
                "diana_trust": narrative_state.diana_trust_level,
            },
            "message": self._generate_loyalty_rewards_message(loyalty_rewards, user),
        }

    # ===== ADMINISTRACIÓN DE TIENDA =====

    def add_new_item(self, item_data: Dict[str, Any]) -> ShopItem:
        """Añade nuevo item a la tienda"""

        item = ShopItem(
            name=item_data["name"],
            description=item_data["description"],
            long_description=item_data.get(
                "long_description", item_data["description"]
            ),
            base_price=item_data["base_price"],
            item_type=ShopItemType(item_data["item_type"]),
            rarity=ShopRarity(item_data["rarity"]),
            category_id=item_data.get("category_id"),
            content_data=item_data.get("content_data", {}),
            preview_media_url=item_data.get("preview_media_url"),
            access_level=item_data.get("access_level", "kinky"),
            min_user_level=item_data.get("min_user_level", 1),
            vip_only=item_data.get("vip_only", False),
            is_limited_time=item_data.get("is_limited_time", False),
            expires_at=item_data.get("expires_at"),
            stock_quantity=item_data.get("stock_quantity"),
            tags=item_data.get("tags", []),
            metadata=item_data.get("metadata", {}),
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def get_shop_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Obtiene analytics de la tienda"""

        since_date = datetime.utcnow() - timedelta(days=days)

        # Métricas básicas
        total_purchases = (
            self.db.query(ShopPurchase)
            .filter(ShopPurchase.purchased_at >= since_date)
            .count()
        )

        total_revenue = (
            self.db.query(func.sum(ShopPurchase.total_price))
            .filter(ShopPurchase.purchased_at >= since_date)
            .scalar()
            or 0
        )

        total_besitos_rewarded = (
            self.db.query(func.sum(ShopPurchase.besitos_rewarded))
            .filter(ShopPurchase.purchased_at >= since_date)
            .scalar()
            or 0
        )

        # Items más vendidos
        top_items = (
            self.db.query(
                ShopItem.name,
                func.sum(ShopPurchase.quantity).label("total_sold"),
                func.sum(ShopPurchase.total_price).label("revenue"),
            )
            .join(ShopPurchase, ShopItem.id == ShopPurchase.item_id)
            .filter(ShopPurchase.purchased_at >= since_date)
            .group_by(ShopItem.id)
            .order_by(desc("total_sold"))
            .limit(10)
            .all()
        )

        # Usuarios más activos
        top_buyers = (
            self.db.query(
                User.first_name,
                func.count(ShopPurchase.id).label("purchase_count"),
                func.sum(ShopPurchase.total_price).label("total_spent"),
            )
            .join(ShopPurchase, User.id == ShopPurchase.user_id)
            .filter(ShopPurchase.purchased_at >= since_date)
            .group_by(User.id)
            .order_by(desc("total_spent"))
            .limit(10)
            .all()
        )

        return {
            "period_days": days,
            "total_purchases": total_purchases,
            "total_revenue": total_revenue,
            "total_besitos_rewarded": total_besitos_rewarded,
            "avg_purchase_value": total_revenue / max(total_purchases, 1),
            "besitos_reward_rate": (total_besitos_rewarded / max(total_revenue, 1))
            * 100,
            "top_items": [
                {
                    "name": name,
                    "sold": sold,
                    "revenue": revenue,
                    "avg_price": revenue / max(sold, 1),
                }
                for name, sold, revenue in top_items
            ],
            "top_buyers": [
                {
                    "name": name,
                    "purchases": count,
                    "total_spent": spent,
                    "avg_per_purchase": spent / max(count, 1),
                }
                for name, count, spent in top_buyers
            ],
        }

    # ===== MÉTODOS AUXILIARES =====

    def _get_available_categories(
        self, user: User, narrative_state: UserNarrativeState
    ) -> List[ShopCategory]:
        """Obtiene categorías disponibles para el usuario"""

        # Filtrar por nivel narrativo
        available_categories = (
            self.db.query(ShopCategory).filter(ShopCategory.is_active == True).all()
        )

        # Filtrar por acceso del usuario
        filtered_categories = []
        for category in available_categories:
            if self._user_has_category_access(user, narrative_state, category):
                filtered_categories.append(category)

        return filtered_categories

    def _user_has_category_access(
        self, user: User, narrative_state: UserNarrativeState, category: ShopCategory
    ) -> bool:
        """Verifica acceso a categoría"""

        # Verificar nivel narrativo mínimo
        if category.unlock_narrative_level:
            required_level = NarrativeLevel(category.unlock_narrative_level)
            user_level_value = list(NarrativeLevel).index(narrative_state.current_level)
            required_level_value = list(NarrativeLevel).index(required_level)

            if user_level_value < required_level_value:
                return False

        # Verificar nivel de usuario
        if user.level < category.min_user_level:
            return False

        # Verificar acceso VIP
        if category.vip_only and not narrative_state.has_divan_access:
            return False

        return True

    def _get_category_items(
        self, category_id: int, user: User, narrative_state: UserNarrativeState
    ) -> List[Dict[str, Any]]:
        """Obtiene items de una categoría"""

        items = (
            self.db.query(ShopItem)
            .filter(
                and_(
                    ShopItem.category_id == category_id,
                    ShopItem.is_active == True,
                    or_(
                        ShopItem.expires_at.is_(None),
                        ShopItem.expires_at > datetime.utcnow(),
                    ),
                )
            )
            .order_by(ShopItem.featured.desc(), ShopItem.rarity.desc())
            .all()
        )

        formatted_items = []
        for item in items:
            if self._user_has_item_access(user, narrative_state, item):
                pricing = self._calculate_personalized_pricing(
                    item, user, narrative_state
                )

                formatted_items.append(
                    {
                        "id": item.id,
                        "name": item.name,
                        "description": item.description,
                        "rarity": item.rarity.value,
                        "base_price": item.base_price,
                        "final_price": pricing["final_price"],
                        "discount_percentage": pricing.get("discount_percentage", 0),
                        "besitos_reward": pricing.get("estimated_reward", 0),
                        "preview_url": item.preview_media_url,
                        "is_limited": item.is_limited_time,
                        "stock": item.stock_quantity,
                        "tags": item.tags or [],
                    }
                )

        return formatted_items

    def _user_has_item_access(
        self, user: User, narrative_state: UserNarrativeState, item: ShopItem
    ) -> bool:
        """Verifica acceso a item específico"""

        # Verificar nivel de usuario
        if user.level < item.min_user_level:
            return False

        # Verificar acceso VIP
        if item.vip_only and not narrative_state.has_divan_access:
            return False

        # Verificar nivel de acceso narrativo
        if item.access_level == "divan" and not narrative_state.has_divan_access:
            return False

        # Verificar stock
        if item.stock_quantity is not None and item.stock_quantity <= 0:
            return False

        return True

    def _calculate_personalized_pricing(
        self, item: ShopItem, user: User, narrative_state: UserNarrativeState
    ) -> Dict[str, Any]:
        """Calcula precio personalizado y recompensas"""

        base_price = item.base_price
        final_price = base_price
        discount_percentage = 0

        # Descuento por nivel narrativo
        narrative_multiplier = self.NARRATIVE_MULTIPLIERS.get(
            narrative_state.current_level, 1.0
        )
        if narrative_multiplier > 1.0:
            discount = 1 - (1 / narrative_multiplier)
            final_price = int(base_price * (1 - discount))
            discount_percentage = discount * 100

        # Descuento por lealtad
        purchase_count = (
            self.db.query(ShopPurchase).filter(ShopPurchase.user_id == user.id).count()
        )

        if purchase_count >= 10:
            additional_discount = 0.15  # 15% adicional
            final_price = int(final_price * (1 - additional_discount))
            discount_percentage += additional_discount * 100
        elif purchase_count >= 5:
            additional_discount = 0.1  # 10% adicional
            final_price = int(final_price * (1 - additional_discount))
            discount_percentage += additional_discount * 100

        # Calcular besitos de recompensa estimados
        reward_rate = self.BESITOS_REWARD_RATES.get(item.rarity.value, 0.1)
        narrative_reward_multiplier = self.NARRATIVE_MULTIPLIERS.get(
            narrative_state.current_level, 1.0
        )
        estimated_reward = int(final_price * reward_rate * narrative_reward_multiplier)

        return {
            "base_price": base_price,
            "final_price": final_price,
            "discount_percentage": round(discount_percentage, 1),
            "estimated_reward": estimated_reward,
            "rarity_bonus": reward_rate,
            "narrative_multiplier": narrative_reward_multiplier,
        }

    def _calculate_purchase_reward_besitos(
        self, item: ShopItem, total_cost: int, narrative_state: UserNarrativeState
    ) -> int:
        """Calcula besitos de recompensa por compra"""

        # Tasa base por rareza
        reward_rate = self.BESITOS_REWARD_RATES.get(item.rarity.value, 0.1)

        # Multiplicador narrativo
        narrative_multiplier = self.NARRATIVE_MULTIPLIERS.get(
            narrative_state.current_level, 1.0
        )

        # Bonus por confianza con Diana
        trust_bonus = 1.0
        if narrative_state.diana_trust_level >= 80:
            trust_bonus = 1.3
        elif narrative_state.diana_trust_level >= 60:
            trust_bonus = 1.2
        elif narrative_state.diana_trust_level >= 40:
            trust_bonus = 1.1

        # Calcular recompensa final
        reward_besitos = int(
            total_cost * reward_rate * narrative_multiplier * trust_bonus
        )

        return reward_besitos

    def _generate_shop_welcome_message(
        self, user: User, narrative_state: UserNarrativeState
    ) -> str:
        """Genera mensaje de bienvenida a la tienda"""

        access_level = self._get_user_shop_access_level(narrative_state)

        if access_level == "supreme":
            return f"""
{self.lucien.EMOJIS['lucien']} **Bienvenido a la Boutique Exclusiva de Lucien**

*[Con ceremonia y reverencia]*

{user.first_name}, has alcanzado el nivel más alto de confianza con Diana. Esta colección está reservada para el círculo más íntimo.

🔮 **Acceso Supremo Desbloqueado**
💫 **Multiplicador de Recompensas:** 2.0x
👑 **Contenido Mítico Disponible**

*[Con una sonrisa conocedora]*
Cada compra aquí no solo te recompensa generosamente... Diana ha puesto su toque personal en cada item.
            """.strip()

        elif access_level == "divan":
            return f"""
{self.lucien.EMOJIS['lucien']} **Bienvenido a la Boutique Exclusiva de Lucien**

*[Con elegancia y respeto]*

{user.first_name}, tu acceso al Diván te ha abierto las puertas a mi colección más selecta.

🗝️ **Acceso VIP Confirmado**
⚡ **Multiplicador de Recompensas:** 1.5x
💎 **Items Legendarios Disponibles**

*[Con satisfacción]*
Diana ha seleccionado personalmente estos items para quienes han ganado su confianza íntima.
            """.strip()

        else:
            return f"""
{self.lucien.EMOJIS['lucien']} **Bienvenido a la Boutique de Lucien**

*[Con hospitalidad profesional]*

{user.first_name}, mi colección exclusiva está a tu disposición. Cada item ha sido curado pensando en acercarte más a Diana.

💋 **Besitos Disponibles:** {user.besitos:,}
✨ **Recompensas por Compra:** Hasta 50% de regreso en besitos
🎁 **Contenido Exclusivo:** Solo disponible aquí

*[Con aire conspiratorio]*
Cada compra no solo te recompensa... también demuestra a Diana tu verdadera dedicación.
            """.strip()

    def _get_user_shop_access_level(self, narrative_state: UserNarrativeState) -> str:
        """Obtiene nivel de acceso del usuario a la tienda"""

        if narrative_state.current_level in [NarrativeLevel.LEVEL_6_DIVAN_SUPREME]:
            return "supreme"
        elif narrative_state.has_divan_access:
            return "divan"
        elif narrative_state.current_level in [
            NarrativeLevel.LEVEL_2_KINKY_DEEP,
            NarrativeLevel.LEVEL_3_KINKY_FINAL,
        ]:
            return "kinky_advanced"
        else:
            return "basic"

    def _generate_purchase_confirmation_message(
        self,
        item: ShopItem,
        purchase: ShopPurchase,
        reward_besitos: int,
        user: User,
        delivery_result: Dict,
    ) -> str:
        """Genera mensaje de confirmación de compra"""

        base_message = f"""
{self.lucien.EMOJIS['lucien']} **Compra Confirmada con Elegancia**

*[Con satisfacción profesional]*

**"{item.name}"** - Adquirido magistralmente.

💰 **Costo:** {purchase.total_price:,} besitos
💋 **Recompensa:** +{reward_besitos:,} besitos
📦 **Cantidad:** {purchase.quantity}
        """.strip()

        # Comentario sobre la rareza
        rarity_comment = ""
        if item.rarity == ShopRarity.LEGENDARY:
            rarity_comment = "\n\n*[Con admiración]*\nUn item legendario... Diana estará complacida por tu excelente gusto."
        elif item.rarity == ShopRarity.MYTHICAL:
            rarity_comment = "\n\n*[Con asombro contenido]*\nMítico... has adquirido algo que incluso a mí me sorprende que Diana haya decidido compartir."
        elif item.rarity == ShopRarity.EPIC:
            rarity_comment = "\n\n*[Con aprobación]*\nUn item épico que demuestra tu refinado criterio. Diana aprecia este nivel de discernimiento."

        # Información de entrega
        delivery_message = f"""

📥 **Entrega:** {delivery_result.get('message', 'Contenido entregado a tu colección privada')}

*[Con elegancia final]*
Cada compra te acerca más a Diana y demuestra tu verdadera dedicación. Estos besitos de recompensa son su forma de... agradecer tu inversión.
        """.strip()

        return base_message + rarity_comment + delivery_message

    def _generate_collection_commentary(self, collection: Dict, user: User) -> str:
        """Genera comentario de Lucien sobre la colección del usuario"""

        total_items = collection["total_items"]
        total_spent = collection["total_spent"]

        if total_items >= 50:
            return f"""
*[Con respeto genuino]*

{user.first_name}, tu colección de {total_items} items es... impresionante. Diana ha comentado que pocos demuestran tal nivel de dedicación y refinamiento.

Has invertido {total_spent:,} besitos en acercarte a ella. Eso no pasa desapercibido.
            """.strip()

        elif total_items >= 20:
            return f"""
*[Con aprobación creciente]*

Una colección sólida de {total_items} items, {user.first_name}. Diana aprecia a quienes comprenden el valor de la exclusividad.

Cada uno de tus {total_spent:,} besitos invertidos ha sido una declaración de intenciones.
            """.strip()

        elif total_items >= 5:
            return f"""
*[Con aliento]*

{total_items} items... un buen comienzo, {user.first_name}. Diana observa cómo construyes tu conexión con ella, pieza por pieza.
            """.strip()

        else:
            return f"""
*[Con hospitalidad]*

Apenas comenzando tu colección, {user.first_name}. Cada item que adquieras será un paso más hacia comprender lo que Diana verdaderamente aprecia.
            """.strip()

    # Métodos auxiliares adicionales...

    def _validate_purchase(
        self,
        item: ShopItem,
        user: User,
        narrative_state: UserNarrativeState,
        quantity: int,
    ) -> Dict[str, Any]:
        """Valida si la compra puede realizarse"""

        if not item.is_active:
            return {"valid": False, "message": "Item no disponible"}

        if item.expires_at and datetime.utcnow() > item.expires_at:
            return {"valid": False, "message": "Item expirado"}

        if item.stock_quantity is not None and item.stock_quantity < quantity:
            return {
                "valid": False,
                "message": f"Stock insuficiente (disponible: {item.stock_quantity})",
            }

        if not self._user_has_item_access(user, narrative_state, item):
            return {"valid": False, "message": "No tienes acceso a este item"}

        if quantity <= 0:
            return {"valid": False, "message": "Cantidad inválida"}

        return {"valid": True}

    def _deliver_item_content(
        self, item: ShopItem, user: User, purchase: ShopPurchase
    ) -> Dict[str, Any]:
        """Entrega el contenido del item al usuario"""

        # En implementación real, esto manejaría la entrega del contenido
        # Por ahora, registramos en el perfil del usuario

        from services.user_service import UserService

        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(user.id)

        if not narrative_state.special_recognitions:
            narrative_state.special_recognitions = []

        narrative_state.special_recognitions.append(
            {
                "type": "shop_purchase",
                "item_name": item.name,
                "rarity": item.rarity.value,
                "purchase_date": datetime.utcnow().isoformat(),
                "content_delivered": True,
            }
        )

        self.db.commit()

        return {
            "delivered": True,
            "method": "profile_collection",
            "message": "Contenido añadido a tu colección privada",
        }

    def _user_owns_item(self, user_id: int, item_id: int) -> bool:
        """Verifica si el usuario ya posee el item"""

        return (
            self.db.query(ShopPurchase)
            .filter(
                and_(ShopPurchase.user_id == user_id, ShopPurchase.item_id == item_id)
            )
            .first()
            is not None
        )
   