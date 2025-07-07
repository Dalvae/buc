from collections.abc import Generator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.main import app as main_app
from app.models import User, UserRole, Company
from app.core.security import create_access_token
from datetime import timedelta
from app.tests.utils.factories import create_random_user, create_random_company


# Usar una base de datos SQLite en memoria para tests aislados y rápidos
engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)

def override_get_db() -> Generator[Session, None, None]:
    """Sobrescribe la dependencia get_db para usar la BD de tests."""
    with Session(engine) as session:
        yield session

# Reemplaza la dependencia en la app globalmente
main_app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def create_test_db() -> Generator[None, None, None]:
    """Crea las tablas de la BD antes de que empiecen los tests y las elimina al final."""
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Provee una sesión de BD limpia para cada test."""
    with Session(engine) as session:
        yield session
        # Limpia todas las tablas después de cada test para asegurar el aislamiento
        for table in reversed(SQLModel.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()

@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Provee un cliente de test para hacer peticiones a la API."""
    with TestClient(main_app) as c:
        yield c

# --- Fixtures de Autenticación y Roles ---

def get_auth_headers(user: User) -> dict[str, str]:
    """Genera cabeceras de autorización para un usuario."""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.id, expires_delta=access_token_expires)
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def superuser(db: Session) -> User:
    return create_random_user(db, is_superuser=True)

@pytest.fixture
def superuser_token_headers(superuser: User) -> dict[str, str]:
    return get_auth_headers(superuser)

@pytest.fixture
def test_company(db: Session) -> Company:
    return create_random_company(db)

@pytest.fixture
def demo_company(db: Session) -> Company:
    return create_random_company(db, is_demo=True)

@pytest.fixture
def admin_user(db: Session, test_company: Company) -> User:
    return create_random_user(db, role=UserRole.ADMIN, company_id=test_company.id)

@pytest.fixture
def admin_user_token_headers(admin_user: User) -> dict[str, str]:
    return get_auth_headers(admin_user)

@pytest.fixture
def auditor_user(db: Session, test_company: Company) -> User:
    return create_random_user(db, role=UserRole.AUDITOR, company_id=test_company.id)

@pytest.fixture
def auditor_user_token_headers(auditor_user: User) -> dict[str, str]:
    return get_auth_headers(auditor_user)

@pytest.fixture
def normal_user(db: Session, test_company: Company) -> User:
    return create_random_user(db, role=UserRole.USER, company_id=test_company.id)

@pytest.fixture
def normal_user_token_headers(normal_user: User) -> dict[str, str]:
    return get_auth_headers(normal_user)
