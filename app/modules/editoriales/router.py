from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.editoriales import service
from app.modules.editoriales.models import Editorial
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate
from app.modules.libros.schemas import LibroReadList

router = APIRouter(prefix="/editoriales", tags=["Editoriales"])


@router.post(
    "/",
    response_model=EditorialRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"description": "Ya existe una editorial con ese nombre"},
    },
)
async def crear_editorial(
    data: EditorialCreate,
    session: AsyncSession = Depends(get_session),
) -> EditorialRead:
    """Da de alta una editorial. La unicidad del nombre la garantiza la base (409 si se repite)."""
    return await service.crear_editorial(session, data)


@router.get(
    "/",
    response_model=list[EditorialRead],
)
async def listar_editoriales(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=100, description="Cantidad de resultados (1 a 100)"),
    offset: int = Query(default=0, ge=0, description="Resultados a saltear (desde 0)"),
) -> list[EditorialRead]:
    """Lista editoriales con paginación por limit/offset."""
    return await service.listar_editoriales(session, limit=limit, offset=offset)


@router.get(
    "/{editorial_id}",
    response_model=EditorialRead,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No existe una editorial con ese id"},
    },
)
async def obtener_editorial(
    editorial_id: int,
    session: AsyncSession = Depends(get_session),
) -> EditorialRead:
    """Devuelve una editorial por id. El path validado como int devuelve 422 si no lo es."""
    return await service.obtener_editorial(session, editorial_id)


@router.patch(
    "/{editorial_id}",
    response_model=EditorialRead,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No existe una editorial con ese id"},
        status.HTTP_409_CONFLICT: {"description": "Ya existe una editorial con ese nombre"},
    },
)
async def actualizar_editorial(
    editorial_id: int,
    data: EditorialUpdate,
    session: AsyncSession = Depends(get_session),
) -> EditorialRead:
    """Actualiza parcialmente una editorial: solo se aplican los campos enviados (exclude_unset)."""
    return await service.actualizar_editorial(session, editorial_id, data)


@router.get(
    "/{editorial_id}/libros",
    response_model=list[LibroReadList],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No existe una editorial con ese id"},
    },
)
async def listar_libros_editorial(
    editorial_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[LibroReadList]:
    """Lista los libros pertenecientes a una editorial (con precarga de editorial y género)."""
    libros = await service.listar_libros_por_editorial(session, editorial_id)
    return libros  # type: ignore[return-value]

