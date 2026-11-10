"""DTOs de editoriales (contratos de entrada/salida, separados del modelo de tabla)."""

from pydantic import Field
from sqlmodel import SQLModel


class EditorialCreate(SQLModel):
    """Cuerpo del POST /editoriales/: no lleva id (lo genera la base)."""

    nombre: str = Field(min_length=1, max_length=120)
    pais: str = Field(min_length=1, max_length=60)


class EditorialUpdate(SQLModel):
    """Cuerpo del PATCH /editoriales/{id}: solo los campos enviados se aplican."""

    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    pais: str | None = Field(default=None, min_length=1, max_length=60)


class EditorialRead(SQLModel):
    """Respuesta de salida: incluye el id generado por la base."""

    id: int
    nombre: str
    pais: str
