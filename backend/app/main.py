"""
Aplicación principal FastAPI.
CV Upload System - Aplicación segura para subida de CVs.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import auth_router, cv_router
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.waf import WAFMiddleware
from app.utils.logging import app_logger, security_logger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Contexto de vida de la aplicación.
    Inicializa la base de datos al arrancar.
    """
    app_logger.info("Iniciando aplicación...")

    # Crear directorio de uploads si no existe
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Inicializar base de datos
    init_db()
    app_logger.info("Base de datos inicializada")

    yield

    app_logger.info("Cerrando aplicación...")


# Crear aplicación FastAPI
app = FastAPI(
    title="CV Upload System",
    description="Sistema seguro de subida de CVs",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Middleware de seguridad (orden importante: se ejecutan de abajo a arriba)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(WAFMiddleware)

# CORS - Configuración restrictiva
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)


# Manejador global de excepciones
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Manejador global de excepciones.
    Nunca expone información sensible al cliente.
    """
    # Log del error real (solo internamente)
    security_logger.error(
        f"Error no manejado: {type(exc).__name__} - "
        f"Path: {request.url.path} - "
        f"IP: {request.client.host if request.client else 'unknown'}"
    )

    # Respuesta genérica al cliente
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ha ocurrido un error interno"}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejador de excepciones HTTP."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# Incluir routers
app.include_router(auth_router.router, prefix="/api")
app.include_router(cv_router.router, prefix="/api")


# Servir frontend estático
@app.get("/")
async def serve_frontend():
    """Sirve la página principal del frontend."""
    frontend_path = "/app/frontend/index.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Frontend no encontrado"}
    )


@app.get("/static/{filename:path}")
async def serve_static(filename: str):
    """Sirve archivos estáticos del frontend."""
    # Prevenir path traversal
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado"
        )

    static_path = f"/app/frontend/{filename}"
    if os.path.exists(static_path) and os.path.isfile(static_path):
        return FileResponse(static_path)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Archivo no encontrado"
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Endpoint de health check."""
    return {"status": "healthy"}
