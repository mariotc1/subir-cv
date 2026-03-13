"""
Middleware de Rate Limiting para protección contra brute force.
"""
import time
from collections import defaultdict
from threading import Lock
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.config import get_settings
from app.utils.logging import security_logger

settings = get_settings()


class RateLimiter:
    """
    Implementación thread-safe de rate limiting basado en IP.
    """

    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.blocked_ips: dict[str, float] = {}
        self.login_attempts: dict[str, list[float]] = defaultdict(list)
        self.lock = Lock()

    def _clean_old_requests(self, ip: str, window: int):
        """Elimina requests antiguos fuera de la ventana de tiempo."""
        current_time = time.time()
        self.requests[ip] = [
            req_time for req_time in self.requests[ip]
            if current_time - req_time < window
        ]

    def _clean_old_login_attempts(self, ip: str, window: int):
        """Elimina intentos de login antiguos."""
        current_time = time.time()
        self.login_attempts[ip] = [
            attempt_time for attempt_time in self.login_attempts[ip]
            if current_time - attempt_time < window
        ]

    def is_blocked(self, ip: str) -> bool:
        """Verifica si una IP está bloqueada."""
        with self.lock:
            if ip in self.blocked_ips:
                if time.time() < self.blocked_ips[ip]:
                    return True
                else:
                    del self.blocked_ips[ip]
            return False

    def block_ip(self, ip: str, duration: int):
        """Bloquea una IP por un período de tiempo."""
        with self.lock:
            self.blocked_ips[ip] = time.time() + duration
            security_logger.warning(
                f"IP bloqueada por rate limiting: {ip} "
                f"(duración: {duration}s)"
            )

    def check_rate_limit(self, ip: str) -> bool:
        """
        Verifica si la IP ha excedido el límite de requests.
        Retorna True si está dentro del límite, False si excede.
        """
        with self.lock:
            self._clean_old_requests(ip, settings.RATE_LIMIT_WINDOW)
            current_time = time.time()

            if len(self.requests[ip]) >= settings.RATE_LIMIT_REQUESTS:
                return False

            self.requests[ip].append(current_time)
            return True

    def record_login_attempt(self, ip: str, success: bool):
        """
        Registra un intento de login.
        Bloquea la IP si excede el límite de intentos fallidos.
        """
        with self.lock:
            if success:
                # Limpiar intentos fallidos en login exitoso
                self.login_attempts[ip] = []
                return

            self._clean_old_login_attempts(ip, settings.LOGIN_BLOCK_DURATION)
            current_time = time.time()
            self.login_attempts[ip].append(current_time)

            if len(self.login_attempts[ip]) >= settings.LOGIN_MAX_ATTEMPTS:
                self.block_ip(ip, settings.LOGIN_BLOCK_DURATION)


# Instancia global del rate limiter
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware que implementa rate limiting por IP.
    """

    async def dispatch(self, request: Request, call_next):
        # Obtener IP del cliente
        client_ip = self._get_client_ip(request)

        # Verificar si la IP está bloqueada
        if rate_limiter.is_blocked(client_ip):
            security_logger.warning(
                f"Acceso denegado - IP bloqueada: {client_ip}"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Demasiadas solicitudes. Por favor, espere."
                }
            )

        # Verificar rate limit general
        if not rate_limiter.check_rate_limit(client_ip):
            security_logger.warning(
                f"Rate limit excedido: {client_ip}"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Demasiadas solicitudes. Por favor, espere."
                }
            )

        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Obtiene la IP real del cliente.
        Considera headers de proxy si están presentes.
        """
        # X-Forwarded-For puede contener múltiples IPs
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Tomar la primera IP (cliente original)
            return forwarded_for.split(",")[0].strip()

        # X-Real-IP como alternativa
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # IP directa del cliente
        if request.client:
            return request.client.host

        return "unknown"
