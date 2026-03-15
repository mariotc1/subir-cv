"""
Web Application Firewall (WAF) básico.
Bloquea patrones de ataque comunes.
"""
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.utils.logging import security_logger


class WAFMiddleware(BaseHTTPMiddleware):
    """
    Middleware WAF que detecta y bloquea patrones de ataque comunes.
    """

    # Patrones de ataque a detectar
    ATTACK_PATTERNS = [
        # Path Traversal
        (r"\.\./", "Path Traversal"),
        (r"\.\.\\", "Path Traversal"),
        (r"%2e%2e%2f", "Path Traversal (encoded)"),
        (r"%2e%2e/", "Path Traversal (partial encoded)"),
        (r"\.\.%2f", "Path Traversal (partial encoded)"),
        (r"%252e%252e%252f", "Path Traversal (double encoded)"),

        # SQL Injection
        (r"(?i)union\s+(all\s+)?select", "SQL Injection"),
        (r"(?i)'\s*or\s+'?1'?\s*=\s*'?1", "SQL Injection"),
        (r"(?i)'\s*or\s+''='", "SQL Injection"),
        (r"(?i);\s*drop\s+table", "SQL Injection"),
        (r"(?i);\s*delete\s+from", "SQL Injection"),
        (r"(?i);\s*update\s+\w+\s+set", "SQL Injection"),
        (r"(?i);\s*insert\s+into", "SQL Injection"),
        (r"(?i)'\s*;\s*--", "SQL Injection"),
        (r"(?i)'\s*or\s+1\s*=\s*1", "SQL Injection"),
        (r"(?i)admin'\s*--", "SQL Injection"),
        (r"(?i)'\s*waitfor\s+delay", "SQL Injection"),
        (r"(?i)benchmark\s*\(", "SQL Injection"),
        (r"(?i)sleep\s*\(", "SQL Injection"),
        (r"(?i)pg_sleep\s*\(", "SQL Injection"),
        (r"(?i)\/\*.*\*\/", "SQL Injection (Comments)"),
        (r"(?i)@@version", "SQL Injection (Version)"),

        # XSS
        (r"(?i)<script[^>]*>", "XSS"),
        (r"(?i)</script>", "XSS"),
        (r"(?i)javascript\s*:", "XSS"),
        (r"(?i)vbscript\s*:", "XSS"),
        (r"(?i)on\w+\s*=", "XSS (Event Handler)"),
        (r"(?i)<iframe", "XSS"),
        (r"(?i)<object", "XSS"),
        (r"(?i)<embed", "XSS"),
        (r"(?i)<svg[^>]*", "XSS"),
        (r"(?i)expression\s*\(", "XSS"),
        (r"(?i)alert\s*\(", "XSS"),
        (r"(?i)document\.cookie", "XSS"),
        (r"(?i)eval\s*\(", "XSS"),
        (r"(?i)window\.location", "XSS"),

        # Command Injection
        (r"(?i);\s*(cat|ls|pwd|whoami|netcat|nc|wget|curl|ping)", "Command Injection"),
        (r"(?i)\|\s*(cat|ls|pwd|whoami|netcat|nc|wget|curl|ping)", "Command Injection"),
        (r"(?i)&&\s*(cat|ls|pwd|whoami|netcat|nc|wget|curl|ping)", "Command Injection"),
        (r"`[^`]+`", "Command Injection"),
        (r"\$\([^)]+\)", "Command Injection"),
        (r"\${[^}]+}", "Command Injection"),

        # LDAP Injection
        (r"(?i)\)\s*\(\|", "LDAP Injection"),
        (r"(?i)\)\s*\(&", "LDAP Injection"),

        # Null byte injection
        (r"%00", "Null Byte Injection"),
        (r"\x00", "Null Byte Injection"),
    ]

    # Compilar patrones para mejor rendimiento
    COMPILED_PATTERNS = [
        (re.compile(pattern), name) for pattern, name in ATTACK_PATTERNS
    ]

    async def dispatch(self, request: Request, call_next):
        # Verificar URL
        url_path = request.url.path
        query_string = str(request.url.query) if request.url.query else ""

        # Verificar path y query string
        combined = f"{url_path}?{query_string}"

        attack_detected = self._check_patterns(combined)
        if attack_detected:
            client_ip = self._get_client_ip(request)
            security_logger.warning(
                f"WAF - Ataque detectado: {attack_detected} | "
                f"IP: {client_ip} | "
                f"Path: {url_path} | "
                f"Query: {query_string}"
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Solicitud bloqueada por razones de seguridad"}
            )

        # Verificar body para POST/PUT/PATCH
        if request.method in ("POST", "PUT", "PATCH"):
            # Solo verificar si es JSON o form data
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.body()
                    body_str = body.decode("utf-8", errors="ignore")
                    attack_detected = self._check_patterns(body_str)
                    if attack_detected:
                        client_ip = self._get_client_ip(request)
                        security_logger.warning(
                            f"WAF - Ataque en body: {attack_detected} | "
                            f"IP: {client_ip} | "
                            f"Path: {url_path}"
                        )
                        return JSONResponse(
                            status_code=403,
                            content={
                                "detail": "Solicitud bloqueada por razones de seguridad"
                            }
                        )
                except Exception:
                    pass

        response = await call_next(request)
        return response

    def _check_patterns(self, text: str) -> str | None:
        """
        Verifica si el texto contiene patrones de ataque.
        Retorna el nombre del ataque si lo encuentra, None si no.
        """
        for pattern, attack_name in self.COMPILED_PATTERNS:
            if pattern.search(text):
                return attack_name
        return None

    def _get_client_ip(self, request: Request) -> str:
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
