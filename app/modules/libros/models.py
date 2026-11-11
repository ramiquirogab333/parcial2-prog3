"""Modelos de tabla del módulo libros: Libro y LibroAutor (objeto de asociación)."""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.autores.models import Autor
    from app.modules.editoriales.models import Editorial
    from app.modules.generos.models import Genero


class LibroAutor(SQLModel, table=True):
    """Objeto de asociación entre Libro y Autor (muchos a muchos con atributos).

    Tiene clave primaria compuesta (libro_id, autor_id) y almacena los atributos
    propios de la autoría: rol y orden en la tapa.
    """

    __tablename__ = "libro_autor"
    __table_args__ = (
        CheckConstraint("orden >= 1", name="check_libro_autor_orden_minimo"),
        CheckConstraint(
            "rol IN ('autor', 'coautor', 'traductor', 'ilustrador')",
            name="check_libro_autor_rol_valido",
        ),
    )

    libro_id: int = Field(foreign_key="libros.id", primary_key=True, index=True)
    autor_id: int = Field(foreign_key="autores.id", primary_key=True, index=True)
    rol: str = Field(max_length=20)
    orden: int = Field()

    libro: Optional["Libro"] = Relationship(back_populates="autorias")
    autor: Optional["Autor"] = Relationship(back_populates="autorias")


class Libro(SQLModel, table=True):
    """Modelo de tabla de libros (catálogo central de la librería)."""

    __tablename__ = "libros"
    __table_args__ = (
        CheckConstraint("precio > 0", name="check_libro_precio_positivo"),
        CheckConstraint("stock >= 0", name="check_libro_stock_no_negativo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    # RN-01: ISBN único garantizado en la base de datos (409 en colisión).
    isbn: str = Field(unique=True, index=True, max_length=30)
    titulo: str = Field(index=True, max_length=255)
    # Dinero representado estrictamente con Decimal / NUMERIC(10, 2)
    precio: Decimal = Field(
        sa_column=Column(Numeric(precision=10, scale=2), nullable=False)
    )
    stock: int = Field(default=0)

    # Agregación: Libro incorpora una editorial que ya existe
    editorial_id: int = Field(foreign_key="editoriales.id", index=True)
    # Agregación opcional: el género es optativo (nulo permitido)
    genero_id: int | None = Field(
        default=None, foreign_key="generos.id", index=True, nullable=True
    )

    # Navegación en los dos extremos
    editorial: Optional["Editorial"] = Relationship(back_populates="libros")
    genero: Optional["Genero"] = Relationship(back_populates="libros")
    autorias: list[LibroAutor] = Relationship(
        back_populates="libro",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
