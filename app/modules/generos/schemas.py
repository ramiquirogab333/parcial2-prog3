"""DTOs de generos (contratos de entrada/salida, separados del modelo de tabla)."""

from pydantic import Field
from sqlmodel import SQLModel


class GeneroCreate(SQLModel):
    """Cuerpo del POST /generos/: no lleva id (lo genera la base)."""

    nombre: str = Field(min_length=1, max_length=80)


class GeneroUpdate(SQLModel):
    """Cuerpo para una futura edición parcial de un género."""

    nombre: str | None = Field(default=None, min_length=1, max_length=80)


class GeneroRead(SQLModel):
    """Respuesta de salida: incluye el id generado por la base."""

    id: int
    nombre: str
