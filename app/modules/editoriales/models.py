"""Modelo de tabla del módulo editoriales."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import Libro


class Editorial(SQLModel, table=True):
    __tablename__ = "editoriales"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True, max_length=120)
    pais: str = Field(max_length=60)

    # Relación 1 a x con Libro (agregación en Libro)
    libros: list["Libro"] = Relationship(back_populates="editorial")

