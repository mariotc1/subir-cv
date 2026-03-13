"""
Schemas Pydantic para Usuario.
Validación estricta de entrada de datos.
"""
import re
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Valida que la contraseña cumpla con los requisitos de seguridad:
        - Mínimo 12 caracteres
        - Al menos una mayúscula
        - Al menos una minúscula
        - Al menos un número
        - Al menos un símbolo
        """
        if len(v) < 12:
            raise ValueError("La contraseña debe tener al menos 12 caracteres")

        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una mayúscula")

        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe contener al menos una minúscula")

        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", v):
            raise ValueError("La contraseña debe contener al menos un símbolo")

        return v

    @field_validator("email")
    @classmethod
    def validate_email_length(cls, v: str) -> str:
        if len(v) > 255:
            raise ValueError("El email no puede exceder 255 caracteres")
        return v.lower().strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class UserResponse(UserBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: UUID | None = None


class MessageResponse(BaseModel):
    message: str
