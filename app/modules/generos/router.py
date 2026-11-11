from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.generos import service
from app.modules.generos.schemas import GeneroCreate, GeneroRead
from app.modules.libros.schemas import LibroReadList

router = APIRouter(prefix="/generos", tags=["Generos"])


@router.post(
    "/",
    response_model=GeneroRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"description": "Ya existe un género con ese nombre"},
    },
)
async def crear_genero(
    data: GeneroCreate,
    session: AsyncSession = Depends(get_session),
) -> GeneroRead:
    """Da de alta un género. La unicidad del nombre la garantiza la base (409 si se repite)."""
    return await service.crear_genero(session, data)


@router.get(
    "/",
    response_model=list[GeneroRead],
)
async def listar_generos(
    session: AsyncSession = Depends(get_session),
) -> list[GeneroRead]:
    """Lista todos los géneros."""
    return await service.listar_generos(session)


@router.get(
    "/{genero_id}/libros",
    response_model=list[LibroReadList],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No existe un género con ese id"},
    },
)
async def listar_libros_genero(
    genero_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[LibroReadList]:
    """Lista los libros asociados a un género (con precarga de editorial y género)."""
    libros = await service.listar_libros_por_genero(session, genero_id)
    return libros  # type: ignore[return-value]
