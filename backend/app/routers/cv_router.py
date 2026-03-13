"""
Router de CV.
Endpoints: subir, descargar, ver info, eliminar.
"""
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.cv_schema import CVResponse, CVUploadResponse, CVDeleteResponse
from app.services.cv_service import CVService
from app.security.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/cv", tags=["CV Management"])


@router.post("/upload", response_model=CVUploadResponse)
async def upload_cv(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sube un CV en formato PDF.
    Si ya existe uno, lo reemplaza.

    Requisitos:
    - Solo archivos PDF
    - Tamaño máximo: 5 MB
    - Requiere autenticación
    """
    client_ip = _get_client_ip(request)
    cv = await CVService.upload_cv(db, current_user, file, client_ip)

    return CVUploadResponse(
        message="CV subido exitosamente",
        cv=CVResponse(
            id=cv.id,
            original_filename=cv.original_filename,
            uploaded_at=cv.uploaded_at
        )
    )


@router.get("/download")
async def download_cv(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Descarga el CV del usuario actual.
    Requiere autenticación.
    """
    client_ip = _get_client_ip(request)
    file_path, original_filename = CVService.get_cv_file_path(
        db, current_user, client_ip
    )

    return FileResponse(
        path=file_path,
        filename=original_filename,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{original_filename}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )


@router.get("/info", response_model=CVResponse)
async def get_cv_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene información del CV del usuario actual.
    Requiere autenticación.
    Retorna 404 si no tiene CV.
    """
    cv = CVService.get_user_cv(db, current_user)

    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tiene ningún CV subido"
        )

    return CVResponse(
        id=cv.id,
        original_filename=cv.original_filename,
        uploaded_at=cv.uploaded_at
    )


@router.delete("/delete", response_model=CVDeleteResponse)
async def delete_cv(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Elimina el CV del usuario actual.
    Requiere autenticación.
    """
    client_ip = _get_client_ip(request)
    CVService.delete_cv(db, current_user, client_ip)

    return CVDeleteResponse(message="CV eliminado exitosamente")


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
