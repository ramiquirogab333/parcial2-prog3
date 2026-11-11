"""DTOs de libros y autorías (contratos de entrada/salida, separados del modelo de tabla)."""

from decimal import Decimal
from typing import Literal

from pydantic import Field
from sqlmodel import SQLModel

from app.modules.editoriales.schemas import EditorialRead
from app.modules.generos.schemas import GeneroRead

RolAutor = Literal["autor", "coautor", "traductor", "ilustrador"]


# --- Entrada (Create / Update) ---


class LibroAutorCreate(SQLModel):
    """Datos de una autoría enviados dentro del alta de un libro (DTO anidado)."""

    autor_id: int = Field(gt=0, description="Id de un autor existente")
    rol: RolAutor = Field(description="Rol dentro de la obra (autor, coautor, traductor, ilustrador)")
    orden: int = Field(ge=1, description="Orden de aparición en la portada (>= 1)")


class LibroCreate(SQLModel):
    """Cuerpo del POST /libros/: no lleva id (lo genera la base)."""

    isbn: str = Field(min_length=1, max_length=30, description="ISBN único")
    titulo: str = Field(min_length=1, max_length=255, description="Título del libro")
    # RN-03: precio mayor que cero
    precio: Decimal = Field(gt=0, decimal_places=2, description="Precio mayor a cero")
    # RN-03: stock nunca negativo
    stock: int = Field(default=0, ge=0, description="Stock mayor o igual a cero")
    editorial_id: int = Field(gt=0, description="Id de la editorial existente")
    genero_id: int | None = Field(default=None, gt=0, description="Id del género existente (opcional)")
    autores: list[LibroAutorCreate] = Field(
        default_factory=list, description="Lista de autores con sus datos de autoría"
    )


class LibroUpdate(SQLModel):
    """Cuerpo del PATCH /libros/{id}: solo los campos enviados se aplican (exclude_unset)."""

    isbn: str | None = Field(default=None, min_length=1, max_length=30)
    titulo: str | None = Field(default=None, min_length=1, max_length=255)
    precio: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    editorial_id: int | None = Field(default=None, gt=0)
    genero_id: int | None = Field(default=None, gt=0)


# --- Salida (Read) ---


class AutorEnLibroRead(SQLModel):
    """Datos del autor y de la relación incluidos en el detalle del libro."""

    id: int
    autor_id: int
    nombre: str
    apellido: str
    nacionalidad: str | None = None
    rol: str
    orden: int


class LibroRead(SQLModel):
    """Representación base de un libro."""

    id: int
    isbn: str
    titulo: str
    precio: Decimal
    stock: int
    editorial_id: int
    genero_id: int | None = None


class LibroReadList(LibroRead):
    """Representación de un libro para listados con precarga de editorial y género."""

    editorial: EditorialRead
    genero: GeneroRead | None = None


class LibroReadDetail(LibroReadList):
    """Detalle completo de un libro: incluye editorial, género y lista de autores."""

    autores: list[AutorEnLibroRead] = Field(default_factory=list)


class LibroEnAutorRead(SQLModel):
    """Representación de un libro en la vista de un autor (GET /autores/{id}/libros)."""

    id: int
    libro_id: int
    isbn: str
    titulo: str
    precio: Decimal
    stock: int
    editorial_id: int
    genero_id: int | None = None
    rol: str
    orden: int
