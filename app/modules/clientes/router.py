from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.clientes import service
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteRead,
    ClienteUpdate,
    PerfilClienteCreate,
)

router = APIRouter(prefix="/clientes", tags=["Clientes"])

R404 = {status.HTTP_404_NOT_FOUND: {"description": "No existe un cliente con ese id"}}
R409_EMAIL = {status.HTTP_409_CONFLICT: {"description": "Ya existe un cliente con ese email"}}
R409_PERFIL = {status.HTTP_409_CONFLICT: {"description": "El cliente ya tiene un perfil"}}


@router.post(
    "/", response_model=ClienteRead, status_code=status.HTTP_201_CREATED, responses=R409_EMAIL
)
async def crear_cliente(
    data: ClienteCreate,
    session: AsyncSession = Depends(get_session),
) -> ClienteRead:
    """Da de alta un cliente (con perfil opcional). Email repetido => 409 (RN-02)."""
    return await service.crear_cliente(session, data)


@router.get("/", response_model=list[ClienteRead])
async def listar_clientes(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=100, description="Cantidad de resultados (1 a 100)"),
    offset: int = Query(default=0, ge=0, description="Resultados a saltear (desde 0)"),
) -> list[ClienteRead]:
    """Lista clientes con su perfil, paginados por limit/offset."""
    return await service.listar_clientes(session, limit=limit, offset=offset)


@router.get("/{cliente_id}", response_model=ClienteRead, responses=R404)
async def obtener_cliente(
    cliente_id: int,
    session: AsyncSession = Depends(get_session),
) -> ClienteRead:
    """Devuelve el cliente con su perfil."""
    return await service.obtener_cliente(session, cliente_id)


@router.patch("/{cliente_id}", response_model=ClienteRead, responses={**R404, **R409_EMAIL})
async def actualizar_cliente(
    cliente_id: int,
    data: ClienteUpdate,
    session: AsyncSession = Depends(get_session),
) -> ClienteRead:
    """Actualiza parcialmente un cliente."""
    return await service.actualizar_cliente(session, cliente_id, data)


@router.post(
    "/{cliente_id}/perfil",
    response_model=ClienteRead,
    status_code=status.HTTP_201_CREATED,
    responses={**R404, **R409_PERFIL},
)
async def crear_perfil(
    cliente_id: int,
    data: PerfilClienteCreate,
    session: AsyncSession = Depends(get_session),
) -> ClienteRead:
    """Crea el perfil de un cliente. Si ya tiene uno => 409 (RN-09, UNIQUE en base)."""
    return await service.crear_perfil(session, cliente_id, data)
