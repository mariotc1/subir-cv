"""
Validación segura de archivos.
Verifica extensión, MIME type, magic bytes y contenido.
"""
import os
import re
import io
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from app.config import get_settings
from app.utils.logging import security_logger

settings = get_settings()

# Magic bytes para PDF
PDF_MAGIC_BYTES = b"%PDF"

# Patrones realmente peligrosos en PDFs
# Nota: /EmbeddedFile, /AcroForm, /OpenAction, /AA son comunes en PDFs legítimos
# Solo bloqueamos patrones que permiten ejecución de código
SUSPICIOUS_PATTERNS = [
    b"/JavaScript",  # Código JavaScript embebido
    b"/JS ",         # Abreviatura de JavaScript (con espacio para evitar falsos positivos)
    b"/Launch",      # Puede ejecutar aplicaciones externas
    b"/XFA",         # XML Forms que pueden contener scripts
    b"<script",      # HTML/XSS injection
    b"javascript:",  # URLs de JavaScript
]


class FileValidationError(Exception):
    """Error de validación de archivo."""
    pass


async def validate_pdf_file(file: UploadFile) -> bytes:
    """
    Valida que el archivo sea un PDF legítimo.
    Retorna el contenido del archivo si es válido.

    Validaciones:
    1. Extensión .pdf
    2. Content-Type application/pdf
    3. Magic bytes %PDF
    4. Tamaño máximo
    5. Estructura PDF válida (pypdf)
    6. No contiene patrones sospechosos
    """
    # 1. Validar extensión
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre de archivo no válido"
        )

    # Sanitizar nombre de archivo para evitar path traversal
    filename = sanitize_filename(file.filename)
    extension = Path(filename).suffix.lower()

    if extension != ".pdf":
        security_logger.warning(
            f"Extensión no válida: {extension} para archivo {filename}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos PDF"
        )

    # 2. Validar Content-Type
    content_type = file.content_type or ""
    if content_type != "application/pdf":
        security_logger.warning(
            f"Content-Type no válido: {content_type}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de archivo no válido"
        )

    # 3. Leer contenido del archivo
    content = await file.read()

    # 4. Validar tamaño
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo excede el tamaño máximo de {settings.MAX_FILE_SIZE // (1024*1024)} MB"
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío"
        )

    # 5. Validar magic bytes
    if not content.startswith(PDF_MAGIC_BYTES):
        security_logger.warning(
            f"Magic bytes no válidos. Esperado: {PDF_MAGIC_BYTES}, "
            f"Recibido: {content[:10]}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no es un PDF válido"
        )

    # 6. Validar estructura PDF con pypdf
    try:
        # Usar BytesIO para que pypdf pueda leer desde memoria
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)
        
        # Verificar que tenga al menos una página
        if len(reader.pages) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El PDF no contiene páginas válidas"
            )
            
        # Intentar acceder a la primera página para confirmar que es legible
        _ = reader.pages[0]
        
    except (PdfReadError, Exception) as e:
        security_logger.warning(f"Error al parsear estructura PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está corrupto o no es un PDF válido"
        )

    # 7. Buscar patrones sospechosos
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern.lower() in content.lower():
            security_logger.warning(
                f"Patrón sospechoso detectado en PDF: {pattern}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo contiene contenido no permitido (scripts detectados)"
            )

    # Resetear posición del archivo para futuras lecturas
    await file.seek(0)

    return content


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza el nombre de archivo para prevenir path traversal
    y otros ataques.
    """
    # Remover path traversal
    filename = filename.replace("..", "")
    filename = filename.replace("/", "")
    filename = filename.replace("\\", "")

    # Remover caracteres nulos
    filename = filename.replace("\x00", "")

    # Solo permitir caracteres alfanuméricos, guiones, guiones bajos y puntos
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

    # Limitar longitud
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext

    return filename


def validate_storage_path(base_path: str, file_path: str) -> bool:
    """
    Verifica que el path del archivo esté dentro del directorio permitido.
    Previene path traversal.
    """
    # Resolver paths absolutos
    base = Path(base_path).resolve()
    target = Path(file_path).resolve()

    # Verificar que el target está dentro del base
    try:
        target.relative_to(base)
        return True
    except ValueError:
        security_logger.warning(
            f"Intento de path traversal detectado. "
            f"Base: {base}, Target: {target}"
        )
        return False
