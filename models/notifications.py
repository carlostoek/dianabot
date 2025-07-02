from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from database_init import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    notification_type = Column(String(50))
    message = Column(String(255))
    tone = Column(String(50))
    character = Column(String(50))
    was_delivered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", primaryjoin="Notification.user_id==User.telegram_id")
