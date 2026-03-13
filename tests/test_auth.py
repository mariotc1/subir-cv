"""
Tests de autenticación y seguridad.
"""
import pytest


class TestRegistration:
    """Tests de registro de usuarios."""

    def test_register_success(self, client, test_user_data):
        """Test de registro exitoso."""
        response = client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 201
        assert response.json()["message"] == "Usuario registrado exitosamente"

    def test_register_weak_password(self, client):
        """Test de registro con contraseña débil."""
        weak_passwords = [
            "short",  # Muy corta
            "nouppercase123!",  # Sin mayúsculas
            "NOLOWERCASE123!",  # Sin minúsculas
            "NoNumbers!@#$",  # Sin números
            "NoSymbols12345",  # Sin símbolos
        ]

        for password in weak_passwords:
            response = client.post("/api/auth/register", json={
                "email": "test@example.com",
                "password": password
            })
            assert response.status_code == 422, f"Password '{password}' should be rejected"

    def test_register_invalid_email(self, client):
        """Test de registro con email inválido."""
        response = client.post("/api/auth/register", json={
            "email": "not-an-email",
            "password": "ValidPass123!@#"
        })
        assert response.status_code == 422

    def test_register_duplicate_email(self, client, registered_user):
        """Test de registro con email duplicado (no debe revelar si existe)."""
        response = client.post("/api/auth/register", json=registered_user)
        assert response.status_code == 400
        # No debe revelar que el email ya existe
        assert "email" not in response.json()["detail"].lower()


class TestLogin:
    """Tests de login."""

    def test_login_success(self, client, registered_user):
        """Test de login exitoso."""
        response = client.post("/api/auth/login", json=registered_user)
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_login_wrong_password(self, client, registered_user):
        """Test de login con contraseña incorrecta."""
        response = client.post("/api/auth/login", json={
            "email": registered_user["email"],
            "password": "WrongPassword123!@#"
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Credenciales inválidas"

    def test_login_nonexistent_user(self, client):
        """Test de login con usuario inexistente (no debe revelar si existe)."""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123!@#"
        })
        assert response.status_code == 401
        # Mismo mensaje que para contraseña incorrecta
        assert response.json()["detail"] == "Credenciales inválidas"

    def test_login_timing_attack_protection(self, client, registered_user):
        """
        Test que verifica tiempos similares para usuarios existentes y no existentes.
        Esto ayuda a prevenir ataques de enumeración basados en tiempo.
        """
        import time

        # Login con usuario existente (contraseña incorrecta)
        start = time.time()
        client.post("/api/auth/login", json={
            "email": registered_user["email"],
            "password": "WrongPassword123!@#"
        })
        existing_user_time = time.time() - start

        # Login con usuario no existente
        start = time.time()
        client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!@#"
        })
        nonexistent_user_time = time.time() - start

        # Los tiempos deben ser similares (dentro de 500ms)
        assert abs(existing_user_time - nonexistent_user_time) < 0.5


class TestAuthentication:
    """Tests de autenticación con JWT."""

    def test_access_protected_route_without_token(self, client):
        """Test de acceso sin token."""
        response = client.get("/api/auth/me")
        assert response.status_code == 403

    def test_access_protected_route_with_invalid_token(self, client):
        """Test de acceso con token inválido."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_access_protected_route_with_valid_token(self, client, auth_headers):
        """Test de acceso con token válido."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert "email" in response.json()
