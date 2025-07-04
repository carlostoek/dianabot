from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///diana.db")

print(f"🔧 Configurando base de datos: {DATABASE_URL}")

# Crear engine
try:
    if DATABASE_URL.startswith("sqlite"):
        engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False}
        )
    elif DATABASE_URL.startswith("postgresql"):
        # Asegurar que use asyncpg
        if "+asyncpg" not in DATABASE_URL:
            DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        
        engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
    else:
        # Fallback a SQLite
        DATABASE_URL = "sqlite+aiosqlite:///diana.db"
        engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False}
        )
        
    print(f"✅ Database engine created: {DATABASE_URL}")
    
except Exception as e:
    print(f"❌ Error creating engine: {e}")
    # Fallback final a SQLite
    DATABASE_URL = "sqlite+aiosqlite:///diana.db"
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False}
    )
    print(f"✅ Fallback to SQLite: {DATABASE_URL}")

# Crear session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base para modelos
Base = declarative_base()

async def init_db():
    """Inicializar base de datos"""
    try:
        print("📋 Importando modelos...")
        
        # Importar modelos uno por uno para mejor debugging
        try:
            from database.models import User
            print("✅ User model imported")
        except Exception as e:
            print(f"❌ Error importing User: {e}")
            
        try:
            from database.models import Admin
            print("✅ Admin model imported")
        except Exception as e:
            print(f"❌ Error importing Admin: {e}")
            
        try:
            from database.models import NarrativeState
            print("✅ NarrativeState model imported")
        except Exception as e:
            print(f"❌ Error importing NarrativeState: {e}")
            
        # Crear tablas
        print("🔨 Creando tablas...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

async def get_db():
    """Obtener sesión de base de datos"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
            
