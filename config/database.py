from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config.settings import Settings

settings = Settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def init_db():
    """Inicializar base de datos"""
    from database.models import User, Admin, NarrativeState, StoreItem, Auction, Transaction
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncSession:
    """Obtener sesión de base de datos"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
