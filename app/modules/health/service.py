import logging

from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)


async def database_is_up(session: AsyncSession) -> bool:
    """Ejecuta un `SELECT 1` contra PostgreSQL. Nunca propaga el error crudo."""
    try:
        await session.exec(text("SELECT 1"))
        return True
    except Exception:  # cualquier falla de conexión/consulta = base caída
        # Se loguea del lado del servidor; al cliente no le llega el detalle interno.
        logger.exception("Health ready: la base de datos no responde")
        return False
