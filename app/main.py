import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import close_db, init_db
from app.modules.health.router import router as health_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: conecta a PostgreSQL y crea las tablas registradas.
    logger.info("Inicializando base de datos...")
    await init_db()
    logger.info("Base de datos lista.")
    yield
    # Shutdown: libera el pool de conexiones.
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)

# Los turnos siguientes registran acá sus routers, por ejemplo:
# from app.modules.editoriales.router import router as editoriales_router
# app.include_router(editoriales_router)
