"""Modelo de tabla del módulo autores."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import LibroAutor


class Autor(SQLModel, table=True):
    __tablename__ = "autores"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=80)
    apellido: str = Field(max_length=80)
    nacionalidad: str | None = Field(default=None, max_length=60)

    # Relación muchos a muchos con Libro vía tabla intermedia con datos (LibroAutor)
    autorias: list["LibroAutor"] = Relationship(back_populates="autor")

