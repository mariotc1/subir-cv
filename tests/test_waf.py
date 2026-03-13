"""
Tests del WAF (Web Application Firewall).
"""
import pytest


class TestWAFProtection:
    """Tests de protección del WAF."""

    def test_block_sql_injection_in_path(self, client):
        """Test de bloqueo de SQL injection en path."""
        malicious_paths = [
            "/api/auth/login?id=1' OR '1'='1",
            "/api/auth/login?id=1; DROP TABLE users--",
            "/api/auth/login?id=1 UNION SELECT * FROM users",
        ]

        for path in malicious_paths:
            response = client.get(path)
            assert response.status_code == 403

    def test_block_xss_in_query(self, client):
        """Test de bloqueo de XSS en query string."""
        malicious_queries = [
            "/api/auth/me?name=<script>alert('xss')</script>",
            "/api/auth/me?callback=javascript:alert(1)",
            "/api/auth/me?data=<img onerror=alert(1)>",
        ]

        for path in malicious_queries:
            response = client.get(path)
            assert response.status_code == 403

    def test_block_path_traversal(self, client):
        """Test de bloqueo de path traversal."""
        malicious_paths = [
            "/api/../../../etc/passwd",
            "/api/..%2f..%2f..%2fetc/passwd",
            "/api/cv/download?file=../../../etc/passwd",
        ]

        for path in malicious_paths:
            response = client.get(path)
            assert response.status_code in [403, 404]

    def test_block_sql_injection_in_body(self, client):
        """Test de bloqueo de SQL injection en body."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "admin' OR '1'='1",
                "password": "password"
            }
        )
        # Puede ser 403 (WAF) o 422 (validación de email)
        assert response.status_code in [403, 422]

    def test_allow_legitimate_requests(self, client, test_user_data):
        """Test de que requests legítimos no son bloqueados."""
        # Registro legítimo
        response = client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 201

        # Login legítimo
        response = client.post("/api/auth/login", json=test_user_data)
        assert response.status_code == 200


class TestRateLimiting:
    """Tests de rate limiting."""

    def test_rate_limit_after_failed_logins(self, client, registered_user):
        """Test de bloqueo después de múltiples intentos fallidos."""
        # Realizar múltiples intentos fallidos
        for i in range(6):
            response = client.post("/api/auth/login", json={
                "email": registered_user["email"],
                "password": "WrongPassword123!@#"
            })

        # El último intento debe ser bloqueado
        assert response.status_code == 429
