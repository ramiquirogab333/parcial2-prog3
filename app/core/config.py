"""Configuración de la aplicación.

La dirección de la base entra SOLO por la variable de entorno DATABASE_URL
(o por un archivo `.env` local que nunca se sube al repositorio).

No hay valores por defecto para la base: si DATABASE_URL falta, la aplicación
no arranca (es el comportamiento que pide el caso D-05 de la consigna).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Librería de Barrio API"

    # Obligatoria. Formato:
    # postgresql+asyncpg://usuario:clave@host:puerto/base
    DATABASE_URL: str

    # Diagnóstico: muestra en consola el SQL que emite SQLAlchemy.
    # En producción va en false para no escribir cada consulta en el registro.
    SQL_ECHO: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
