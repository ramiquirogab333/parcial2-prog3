"""Configuración de la aplicación.

Los secretos (usuario, contraseña, host de la base) entran SOLO por variables
de entorno o por un archivo `.env` local que nunca se sube al repositorio.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Librería de Barrio API"

    # Datos de conexión a PostgreSQL 16
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "libreria"

    # Si se define, tiene prioridad sobre los campos sueltos de arriba.
    # Formato: postgresql+asyncpg://usuario:clave@host:puerto/base
    DATABASE_URL: str | None = None

    # Muestra el SQL generado por SQLAlchemy en consola (útil para revisar N+1).
    DB_ECHO: bool = False

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
