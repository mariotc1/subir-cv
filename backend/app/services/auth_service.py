"""
Servicio de autenticación.
Maneja registro, login y gestión de usuarios.
"""
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserLogin
from app.security.password import hash_password, verify_password
from app.security.jwt_handler import create_access_token
from app.utils.logging import log_login_attempt


class AuthService:
    """Servicio para operaciones de autenticación."""

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """
        Crea un nuevo usuario.
        """
        # Verificar si el email ya existe
        existing_user = db.query(User).filter(
            User.email == user_data.email.lower()
        ).first()

        if existing_user:
            # No revelar si el email existe (protección contra enumeración)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo crear la cuenta. Por favor, intente con otros datos."
            )

        # Crear usuario
        hashed_password = hash_password(user_data.password)
        user = User(
            email=user_data.email.lower(),
            password_hash=hashed_password
        )

        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo crear la cuenta. Por favor, intente con otros datos."
            )

    @staticmethod
    def authenticate_user(
        db: Session,
        login_data: UserLogin,
        client_ip: str
    ) -> str:
        """
        Autentica un usuario y retorna un token JWT.
        """
        # Buscar usuario por email
        user = db.query(User).filter(
            User.email == login_data.email.lower()
        ).first()

        # Verificar credenciales
        # Siempre verificar password aunque el usuario no exista
        # para evitar timing attacks
        if user is None:
            # Simular verificación de password para tiempo constante
            verify_password("dummy_password", "$2b$12$dummy_hash_for_timing")
            log_login_attempt(login_data.email, False, client_ip)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )

        if not verify_password(login_data.password, user.password_hash):
            log_login_attempt(login_data.email, False, client_ip)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )

        # Login exitoso
        log_login_attempt(login_data.email, True, client_ip)
        access_token = create_access_token(user.id)
        return access_token

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> User | None:
        """
        Obtiene un usuario por su ID.
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        """
        Obtiene un usuario por su email.
        """
        return db.query(User).filter(
            User.email == email.lower()
        ).first()
