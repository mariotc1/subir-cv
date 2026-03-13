"""
Configuración de tests con pytest.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configurar variables de entorno antes de importar la app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_testing_only_32chars!"
os.environ["UPLOAD_DIR"] = "/tmp/test_cvs"

from app.database import Base, get_db
from app.main import app


# Crear engine de test con SQLite en memoria
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override de la dependencia de base de datos para tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_db():
    """Fixture que crea y destruye la base de datos para cada test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Fixture que proporciona un cliente de test."""
    app.dependency_overrides[get_db] = override_get_db

    # Crear directorio de uploads para tests
    os.makedirs("/tmp/test_cvs", exist_ok=True)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Datos de usuario de prueba válidos."""
    return {
        "email": "test@example.com",
        "password": "TestPass123!@#"
    }


@pytest.fixture
def registered_user(client, test_user_data):
    """Fixture que registra un usuario y retorna sus datos."""
    client.post("/api/auth/register", json=test_user_data)
    return test_user_data


@pytest.fixture
def auth_headers(client, registered_user):
    """Fixture que retorna headers de autenticación."""
    response = client.post("/api/auth/login", json=registered_user)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def valid_pdf_content():
    """Contenido mínimo válido de un PDF."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"


@pytest.fixture
def invalid_pdf_content():
    """Contenido que no es un PDF."""
    return b"This is not a PDF file"
