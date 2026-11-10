from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.autores import service
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate

router = APIRouter(prefix="/autores", tags=["Autores"])


@router.post("/", response_model=AutorRead, status_code=status.HTTP_201_CREATED)
async def crear_autor(
    data: AutorCreate,
    session: AsyncSession = Depends(get_session),
) -> AutorRead:
    """Da de alta un autor."""
    return await service.crear_autor(session, data)


@router.get("/", response_model=list[AutorRead])
async def listar_autores(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=100, description="Cantidad de resultados (1 a 100)"),
    offset: int = Query(default=0, ge=0, description="Resultados a saltear (desde 0)"),
) -> list[AutorRead]:
    """Lista autores con paginación por limit/offset."""
    return await service.listar_autores(session, limit=limit, offset=offset)


@router.get(
    "/{autor_id}",
    response_model=AutorRead,
    responses={status.HTTP_404_NOT_FOUND: {"description": "No existe un autor con ese id"}},
)
async def obtener_autor(
    autor_id: int,
    session: AsyncSession = Depends(get_session),
) -> AutorRead:
    """Devuelve el detalle de un autor."""
    return await service.obtener_autor(session, autor_id)


@router.patch(
    "/{autor_id}",
    response_model=AutorRead,
    responses={status.HTTP_404_NOT_FOUND: {"description": "No existe un autor con ese id"}},
)
async def actualizar_autor(
    autor_id: int,
    data: AutorUpdate,
    session: AsyncSession = Depends(get_session),
) -> AutorRead:
    """Actualiza parcialmente un autor: solo se aplican los campos enviados."""
    return await service.actualizar_autor(session, autor_id, data)
