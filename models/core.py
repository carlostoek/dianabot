from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime

from database_init import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(64))
    first_name = Column(String(64))
    is_onboarded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
