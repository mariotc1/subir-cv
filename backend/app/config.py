"""
Configuración de la aplicación.
Todas las variables sensibles se cargan desde variables de entorno.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import field_validator
import secrets


class Settings(BaseSettings):
    # Base de datos
    DATABASE_URL: str = "postgresql://cvapp:cvapp_secure_password@db:5432/cvapp"

    # JWT
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30

    # Seguridad
    BCRYPT_ROUNDS: int = 12

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # segundos
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_BLOCK_DURATION: int = 300  # 5 minutos en segundos

    # Archivos
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5 MB
    UPLOAD_DIR: str = "/app/storage/cvs"
    ALLOWED_EXTENSIONS: set = {".pdf"}

    # Aplicación
    APP_NAME: str = "CV Upload System"
    DEBUG: bool = False

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY debe tener al menos 32 caracteres")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
