"""
Sistema de logging seguro.
Nunca registra contraseñas ni tokens.
"""
import logging
import sys
from datetime import datetime, timezone

# Configurar formato de logs
LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """Configura el sistema de logging."""
    # Logger principal
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Reducir verbosidad de librerías externas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# Loggers específicos
app_logger = logging.getLogger("app")
security_logger = logging.getLogger("security")
access_logger = logging.getLogger("access")


def log_login_attempt(email: str, success: bool, ip: str):
    """
    Registra un intento de login.
    NUNCA registra la contraseña.
    """
    status = "SUCCESS" if success else "FAILED"
    # Sanitizar email para logs (ocultar parte del email)
    sanitized_email = _sanitize_email(email)
    security_logger.info(
        f"LOGIN {status} | Email: {sanitized_email} | IP: {ip}"
    )


def log_file_upload(user_id: str, filename: str, success: bool, ip: str):
    """Registra una subida de archivo."""
    status = "SUCCESS" if success else "FAILED"
    access_logger.info(
        f"FILE_UPLOAD {status} | User: {user_id} | "
        f"File: {filename} | IP: {ip}"
    )


def log_file_download(user_id: str, cv_id: str, ip: str):
    """Registra una descarga de archivo."""
    access_logger.info(
        f"FILE_DOWNLOAD | User: {user_id} | CV: {cv_id} | IP: {ip}"
    )


def log_security_event(event_type: str, details: str, ip: str):
    """Registra un evento de seguridad."""
    security_logger.warning(
        f"SECURITY_EVENT | Type: {event_type} | "
        f"Details: {details} | IP: {ip}"
    )


def _sanitize_email(email: str) -> str:
    """
    Sanitiza un email para logs.
    Muestra solo los primeros 2 caracteres antes del @.
    """
    try:
        local, domain = email.split("@")
        if len(local) > 2:
            sanitized_local = local[:2] + "***"
        else:
            sanitized_local = "***"
        return f"{sanitized_local}@{domain}"
    except Exception:
        return "***@***"


# Inicializar logging al importar el módulo
setup_logging()
