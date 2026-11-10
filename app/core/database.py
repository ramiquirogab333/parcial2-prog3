"""Motor asincrónico (asyncpg) y dependencia de sesión.

Uso en cualquier router de los turnos siguientes:

    from app.core.database import get_session
    from sqlmodel.ext.asyncio.session import AsyncSession

    @router.get("/")
    async def listar(session: AsyncSession = Depends(get_session)):
        ...
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,  # descarta conexiones muertas del pool
)

# expire_on_commit=False: después de un commit los objetos siguen siendo
# legibles sin disparar una nueva consulta (evita lazy loads implícitos en async).
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia de FastAPI: abre una sesión por request y la cierra al terminar."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Crea todas las tablas registradas en SQLModel.metadata.

    Importante: los modelos (`table=True`) tienen que estar importados ANTES de
    llamar a esta función, si no SQLModel no los conoce. Para eso existe
    `app/core/models_registry.py`: cada turno agrega ahí el import de su
    `models.py`.
    """
    import app.core.models_registry  # noqa: F401  (registra los modelos)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db() -> None:
    await engine.dispose()
