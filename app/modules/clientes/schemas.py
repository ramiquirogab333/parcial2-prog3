"""DTOs de clientes (contratos de entrada/salida, separados de los modelos de tabla)."""

from pydantic import Field
from sqlmodel import SQLModel

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class PerfilClienteCreate(SQLModel):
    telefono: str | None = Field(default=None, min_length=1, max_length=30)
    direccion: str | None = Field(default=None, min_length=1, max_length=200)


class PerfilClienteRead(SQLModel):
    id: int
    telefono: str | None = None
    direccion: str | None = None


class ClienteCreate(SQLModel):
    """Cuerpo del POST /clientes/. El perfil es opcional y se crea junto al cliente."""

    nombre: str = Field(min_length=1, max_length=120)
    email: str = Field(max_length=254, pattern=EMAIL_PATTERN)
    perfil: PerfilClienteCreate | None = None


class ClienteUpdate(SQLModel):
    """Cuerpo del PATCH /clientes/{id}: solo los campos enviados se aplican."""

    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=254, pattern=EMAIL_PATTERN)


class ClienteRead(SQLModel):
    id: int
    nombre: str
    email: str
    perfil: PerfilClienteRead | None = None
