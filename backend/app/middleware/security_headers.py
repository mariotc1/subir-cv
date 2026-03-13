"""
Middleware para añadir headers de seguridad a todas las respuestas.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Añade headers de seguridad a todas las respuestas HTTP.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Content Security Policy - Previene XSS
        # Permite blob: para visualización previa de PDFs
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "frame-src 'self' blob:; "
            "object-src 'self' blob:; "
            "frame-ancestors 'none'; "
            "form-action 'self'"
        )

        # Permite frames solo del mismo origen para el visor de PDF
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # Previene MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Habilita HSTS (solo HTTPS)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # Controla información de referrer
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Previene XSS en navegadores antiguos
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Política de permisos
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response
