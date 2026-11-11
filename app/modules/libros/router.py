"""Router HTTP del módulo libros."""

from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.modules.libros import service
from app.modules.libros.schemas import (
    LibroCreate,
    LibroReadDetail,
    LibroReadList,
    LibroUpdate,
)

router = APIRouter(prefix="/libros", tags=["Libros"])

R404 = {status.HTTP_404_NOT_FOUND: {"description": "No existe un libro con ese id"}}
R409 = {status.HTTP_409_CONFLICT: {"description": "Conflicto de integridad (ISBN repetido o clave foránea inexistente)"}}


@router.post(
    "/",
    response_model=LibroReadDetail,
    status_code=status.HTTP_201_CREATED,
    responses=R409,
)
async def crear_libro(
    data: LibroCreate,
    session: AsyncSession = Depends(get_session),
) -> LibroReadDetail:
    """Da de alta un libro con sus autores asociados.

    Cumple la regla del Ejercicio 4: no realiza consultas previas; si la base
    rechaza una clave foránea o ISBN repetido, devuelve 409.
    """
    return await service.crear_libro(session, data)


@router.get(
    "/",
    response_model=list[LibroReadList],
)
async def listar_libros(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=100, description="Cantidad de resultados (1 a 100)"),
    offset: int = Query(default=0, ge=0, description="Resultados a saltear (desde 0)"),
    titulo: str | None = Query(default=None, description="Filtro insensible a mayúsculas por parte del título"),
    genero_id: int | None = Query(default=None, description="Filtro opcional por género"),
) -> list[LibroReadList]:
    """Lista libros con paginación por limit/offset y filtros por título y género (RN-10, RN-11)."""
    libros = await service.listar_libros(
        session, limit=limit, offset=offset, titulo=titulo, genero_id=genero_id
    )
    # FastAPI/Pydantic serializa automáticamente cada Libro a LibroReadList
    return libros  # type: ignore[return-value]


@router.get(
    "/{libro_id}",
    response_model=LibroReadDetail,
    responses=R404,
)
async def obtener_libro(
    libro_id: int,
    session: AsyncSession = Depends(get_session),
) -> LibroReadDetail:
    """Devuelve el detalle completo del libro con editorial, género y autores (sin N+1)."""
    libro = await service.obtener_libro(session, libro_id)
    return service.a_detalle_libro(libro)


@router.patch(
    "/{libro_id}",
    response_model=LibroReadDetail,
    responses={**R404, **R409},
)
async def actualizar_libro(
    libro_id: int,
    data: LibroUpdate,
    session: AsyncSession = Depends(get_session),
) -> LibroReadDetail:
    """Actualiza parcialmente un libro aplicando solo los campos enviados (exclude_unset)."""
    return await service.actualizar_libro(session, libro_id, data)
