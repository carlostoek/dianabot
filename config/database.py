from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config.settings import Settings
import os

settings = Settings()

# Determinar el driver correcto basado en la URL de la base de datos
database_url = settings.DATABASE_URL

# Si no hay URL específica, usar SQLite por defecto
if not database_url or database_url == "":
    database_url = "sqlite+aiosqlite:///diana.db"

# Configurar engine con parámetros apropiados
if database_url.startswith("sqlite"):
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False}
    )
elif database_url.startswith("postgresql"):
    # Asegurar que use asyncpg en lugar de psycopg2
    if "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
else:
    # Fallback a SQLite
    database_url = "sqlite+aiosqlite:///diana.db"
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False}
    )

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def init_db():
    """Inicializar base de datos"""
    try:
        from database.models import (
            User, Admin, NarrativeState, StoreItem, Auction, 
            AuctionBid, Transaction, Purchase, Badge, UserBadge,
            ChannelPost, UserReaction, ContentTemplate, StoryScene
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Base de datos inicializada correctamente")
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        # En caso de error, intentar con SQLite
        global engine, AsyncSessionLocal
        
        sqlite_url = "sqlite+aiosqlite:///diana.db"
        engine = create_async_engine(
            sqlite_url,
            echo=False,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False}
        )
        
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Fallback a SQLite completado")

async def get_db() -> AsyncSession:
    """Obtener sesión de base de datos"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
            
