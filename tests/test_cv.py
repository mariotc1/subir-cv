"""
Tests de gestión de CVs y seguridad de archivos.
"""
import io
import pytest


class TestCVUpload:
    """Tests de subida de CVs."""

    def test_upload_without_auth(self, client, valid_pdf_content):
        """Test de subida sin autenticación."""
        files = {"file": ("test.pdf", io.BytesIO(valid_pdf_content), "application/pdf")}
        response = client.post("/api/cv/upload", files=files)
        assert response.status_code == 403

    def test_upload_valid_pdf(self, client, auth_headers, valid_pdf_content):
        """Test de subida de PDF válido."""
        files = {"file": ("test.pdf", io.BytesIO(valid_pdf_content), "application/pdf")}
        response = client.post("/api/cv/upload", files=files, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "CV subido exitosamente"

    def test_upload_non_pdf_extension(self, client, auth_headers, valid_pdf_content):
        """Test de subida de archivo con extensión no PDF."""
        files = {"file": ("test.txt", io.BytesIO(valid_pdf_content), "application/pdf")}
        response = client.post("/api/cv/upload", files=files, headers=auth_headers)
        assert response.status_code == 400

    def test_upload_wrong_mime_type(self, client, auth_headers, valid_pdf_content):
        """Test de subida con MIME type incorrecto."""
        files = {"file": ("test.pdf", io.BytesIO(valid_pdf_content), "text/plain")}
        response = client.post("/api/cv/upload", files=files, headers=auth_headers)
        assert response.status_code == 400

    def test_upload_invalid_magic_bytes(self, client, auth_headers, invalid_pdf_content):
        """Test de subida de archivo sin magic bytes de PDF."""
        files = {"file": ("test.pdf", io.BytesIO(invalid_pdf_content), "application/pdf")}
        response = client.post("/api/cv/upload", files=files, headers=auth_headers)
        assert response.status_code == 400

    def test_upload_file_too_large(self, client, auth_headers):
        """Test de subida de archivo demasiado grande."""
        # Crear contenido de 6 MB (límite es 5 MB)
        large_content = b"%PDF-1.4\n" + (b"x" * (6 * 1024 * 1024))
        files = {"file": ("test.pdf", io.BytesIO(large_content), "application/pdf")}
        response = client.post("/api/cv/upload", files=files, headers=auth_headers)
        assert response.status_code == 413

    def test_upload_empty_file(self, client, auth_headers):
        """Test de subida de archivo vacío."""
        files = {"file": ("test.pdf", io.BytesIO(b""), "application/pdf")}
        response = client.post("/api/cv/upload", files=files, headers=auth_headers)
        assert response.status_code == 400

    def test_upload_pdf_with_javascript(self, client, auth_headers):
        """Test de subida de PDF con JavaScript embebido."""
        malicious_pdf = b"%PDF-1.4\n/JavaScript /JS (alert('xss'))\nendobj"
        files = {"file": ("test.pdf", io.BytesIO(malicious_pdf), "application/pdf")}
        response = client.post("/api/cv/upload", files=files, headers=auth_headers)
        assert response.status_code == 400


class TestCVDownload:
    """Tests de descarga de CVs."""

    def test_download_without_auth(self, client):
        """Test de descarga sin autenticación."""
        response = client.get("/api/cv/download")
        assert response.status_code == 403

    def test_download_no_cv(self, client, auth_headers):
        """Test de descarga cuando no hay CV subido."""
        response = client.get("/api/cv/download", headers=auth_headers)
        assert response.status_code == 404

    def test_download_own_cv(self, client, auth_headers, valid_pdf_content):
        """Test de descarga del propio CV."""
        # Subir CV primero
        files = {"file": ("test.pdf", io.BytesIO(valid_pdf_content), "application/pdf")}
        client.post("/api/cv/upload", files=files, headers=auth_headers)

        # Descargar CV
        response = client.get("/api/cv/download", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert response.headers["x-content-type-options"] == "nosniff"


class TestCVAccessControl:
    """Tests de control de acceso a CVs."""

    def test_cannot_access_other_user_cv(self, client, valid_pdf_content):
        """Test de que un usuario no puede acceder al CV de otro."""
        # Crear usuario 1 y subir CV
        user1_data = {"email": "user1@example.com", "password": "TestPass123!@#"}
        client.post("/api/auth/register", json=user1_data)
        response = client.post("/api/auth/login", json=user1_data)
        user1_token = response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        files = {"file": ("cv1.pdf", io.BytesIO(valid_pdf_content), "application/pdf")}
        client.post("/api/cv/upload", files=files, headers=user1_headers)

        # Crear usuario 2
        user2_data = {"email": "user2@example.com", "password": "TestPass123!@#"}
        client.post("/api/auth/register", json=user2_data)
        response = client.post("/api/auth/login", json=user2_data)
        user2_token = response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # Usuario 2 intenta descargar (solo obtiene su propio CV o 404)
        response = client.get("/api/cv/download", headers=user2_headers)
        assert response.status_code == 404  # No tiene CV propio


class TestPathTraversal:
    """Tests de protección contra path traversal."""

    def test_path_traversal_in_filename(self, client, auth_headers, valid_pdf_content):
        """Test de path traversal en nombre de archivo."""
        malicious_filenames = [
            "../../../etc/passwd.pdf",
            "..\\..\\..\\windows\\system32\\config.pdf",
            "....//....//etc/passwd.pdf",
            "%2e%2e%2f%2e%2e%2fetc/passwd.pdf",
        ]

        for filename in malicious_filenames:
            files = {"file": (filename, io.BytesIO(valid_pdf_content), "application/pdf")}
            response = client.post("/api/cv/upload", files=files, headers=auth_headers)
            # Debe aceptar el archivo pero sanitizar el nombre
            if response.status_code == 200:
                # Verificar que el nombre fue sanitizado
                assert ".." not in response.json()["cv"]["original_filename"]


class TestSecurityHeaders:
    """Tests de headers de seguridad."""

    def test_security_headers_present(self, client):
        """Test de que los headers de seguridad están presentes."""
        response = client.get("/health")

        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"

        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"

        assert "content-security-policy" in response.headers
        assert "strict-transport-security" in response.headers
        assert "referrer-policy" in response.headers
