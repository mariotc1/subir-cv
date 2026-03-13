"""
Gestión de tokens JWT.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID
from jose import jwt, JWTError
from app.config import get_settings

settings = get_settings()


def create_access_token(user_id: UUID) -> str:
    """
    Crea un token JWT con el ID del usuario.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRATION_MINUTES
    )
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> UUID | None:
    """
    Decodifica y valida un token JWT.
    Retorna el user_id si es válido, None si no lo es.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None

        # Verificar que el token no ha expirado
        exp = payload.get("exp")
        if exp is None:
            return None

        if datetime.now(timezone.utc) > datetime.fromtimestamp(exp, tz=timezone.utc):
            return None

        return UUID(user_id_str)
    except (JWTError, ValueError):
        return None
