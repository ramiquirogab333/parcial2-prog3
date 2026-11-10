"""DTOs de autores (contratos de entrada/salida, separados del modelo de tabla)."""

from pydantic import Field
from sqlmodel import SQLModel


class AutorCreate(SQLModel):
    """Cuerpo del POST /autores/: no lleva id (lo genera la base)."""

    nombre: str = Field(min_length=1, max_length=80)
    apellido: str = Field(min_length=1, max_length=80)
    nacionalidad: str | None = Field(default=None, min_length=1, max_length=60)


class AutorUpdate(SQLModel):
    """Cuerpo del PATCH /autores/{id}: solo los campos enviados se aplican."""

    nombre: str | None = Field(default=None, min_length=1, max_length=80)
    apellido: str | None = Field(default=None, min_length=1, max_length=80)
    nacionalidad: str | None = Field(default=None, min_length=1, max_length=60)


class AutorRead(SQLModel):
    """Respuesta de salida: incluye el id generado por la base."""

    id: int
    nombre: str
    apellido: str
    nacionalidad: str | None = None
