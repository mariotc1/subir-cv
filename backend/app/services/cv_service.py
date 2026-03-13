"""
Servicio de gestión de CVs.
Maneja subida, descarga y eliminación de CVs.
"""
import os
import uuid
from pathlib import Path
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from app.models.cv import CV
from app.models.user import User
from app.config import get_settings
from app.utils.file_validation import (
    validate_pdf_file,
    validate_storage_path,
    sanitize_filename
)
from app.utils.logging import log_file_upload, log_file_download, security_logger

settings = get_settings()


class CVService:
    """Servicio para operaciones con CVs."""

    @staticmethod
    async def upload_cv(
        db: Session,
        user: User,
        file: UploadFile,
        client_ip: str
    ) -> CV:
        """
        Sube un CV para un usuario.
        Si ya tiene uno, lo reemplaza.
        """
        # Validar archivo
        file_content = await validate_pdf_file(file)

        # Generar nombre único para el archivo
        file_uuid = uuid.uuid4()
        storage_filename = f"{file_uuid}.pdf"
        storage_path = os.path.join(settings.UPLOAD_DIR, storage_filename)

        # Validar que el path está dentro del directorio permitido
        if not validate_storage_path(settings.UPLOAD_DIR, storage_path):
            security_logger.warning(
                f"Intento de path traversal en upload. User: {user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al procesar el archivo"
            )

        # Si el usuario ya tiene un CV, eliminarlo
        existing_cv = db.query(CV).filter(CV.user_id == user.id).first()
        if existing_cv:
            # Eliminar archivo anterior
            old_path = existing_cv.storage_path
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception as e:
                    security_logger.error(
                        f"Error eliminando CV anterior: {e}"
                    )

            # Eliminar registro de BD
            db.delete(existing_cv)
            db.commit()

        # Guardar archivo nuevo
        try:
            # Asegurar que el directorio existe
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

            with open(storage_path, "wb") as f:
                f.write(file_content)
        except Exception as e:
            security_logger.error(f"Error guardando archivo: {e}")
            log_file_upload(str(user.id), file.filename or "", False, client_ip)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al guardar el archivo"
            )

        # Crear registro en BD
        original_filename = sanitize_filename(file.filename or "cv.pdf")
        cv = CV(
            user_id=user.id,
            filename=storage_filename,
            original_filename=original_filename,
            storage_path=storage_path
        )

        try:
            db.add(cv)
            db.commit()
            db.refresh(cv)
            log_file_upload(str(user.id), original_filename, True, client_ip)
            return cv
        except Exception as e:
            # Rollback y eliminar archivo si falla BD
            db.rollback()
            if os.path.exists(storage_path):
                os.remove(storage_path)
            security_logger.error(f"Error guardando CV en BD: {e}")
            log_file_upload(str(user.id), file.filename or "", False, client_ip)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al guardar el archivo"
            )

    @staticmethod
    def get_user_cv(db: Session, user: User) -> CV | None:
        """
        Obtiene el CV de un usuario.
        """
        return db.query(CV).filter(CV.user_id == user.id).first()

    @staticmethod
    def get_cv_file_path(
        db: Session,
        user: User,
        client_ip: str
    ) -> tuple[str, str]:
        """
        Obtiene el path del archivo CV de un usuario.
        Verifica ownership antes de retornar.
        Retorna (storage_path, original_filename).
        """
        cv = db.query(CV).filter(CV.user_id == user.id).first()

        if not cv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tiene ningún CV subido"
            )

        # Verificar que el archivo existe
        if not os.path.exists(cv.storage_path):
            security_logger.error(
                f"CV no encontrado en disco. User: {user.id}, Path: {cv.storage_path}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Archivo no encontrado"
            )

        # Verificar path traversal
        if not validate_storage_path(settings.UPLOAD_DIR, cv.storage_path):
            security_logger.warning(
                f"Intento de path traversal en download. User: {user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado"
            )

        log_file_download(str(user.id), str(cv.id), client_ip)
        return cv.storage_path, cv.original_filename

    @staticmethod
    def delete_cv(db: Session, user: User, client_ip: str) -> bool:
        """
        Elimina el CV de un usuario.
        """
        cv = db.query(CV).filter(CV.user_id == user.id).first()

        if not cv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tiene ningún CV para eliminar"
            )

        # Eliminar archivo
        if os.path.exists(cv.storage_path):
            try:
                os.remove(cv.storage_path)
            except Exception as e:
                security_logger.error(
                    f"Error eliminando archivo: {e}"
                )

        # Eliminar registro
        db.delete(cv)
        db.commit()

        security_logger.info(
            f"CV eliminado. User: {user.id}, IP: {client_ip}"
        )
        return True
