"""
Router de autenticación.
Endpoints: registro, login, perfil.
"""
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user_schema import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    MessageResponse
)
from app.services.auth_service import AuthService
from app.security.auth import get_current_user
from app.models.user import User
from app.middleware.rate_limiter import rate_limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario.

    Requisitos de contraseña:
    - Mínimo 12 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    - Al menos un símbolo
    """
    AuthService.create_user(db, user_data)
    return MessageResponse(message="Usuario registrado exitosamente")


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Inicia sesión y retorna un token JWT.
    """
    client_ip = _get_client_ip(request)

    # Verificar si la IP está bloqueada
    if rate_limiter.is_blocked(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Por favor, espere."
        )

    try:
        access_token = AuthService.authenticate_user(
            db, login_data, client_ip
        )
        # Login exitoso - limpiar intentos fallidos
        rate_limiter.record_login_attempt(client_ip, success=True)
        return TokenResponse(access_token=access_token)
    except HTTPException as e:
        # Login fallido - registrar intento
        rate_limiter.record_login_attempt(client_ip, success=False)
        raise e


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene información del usuario actual.
    Requiere autenticación.
    """
    return current_user


def _get_client_ip(request: Request) -> str:
    """Obtiene la IP del cliente."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    if request.client:
        return request.client.host

    return "unknown"
