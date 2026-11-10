"""Modelo de tabla del módulo editoriales."""

from sqlmodel import Field, SQLModel


class Editorial(SQLModel, table=True):
    __tablename__ = "editoriales"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True, max_length=120)
    pais: str = Field(max_length=60)

    # TODO(Turno 4 - Libros): agregar la relación con Libro (1 a x) y el
    # endpoint GET /editoriales/{id}/libros. Lo implementa el turno de Libros.
