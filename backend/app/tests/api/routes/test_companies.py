from fastapi.testclient import TestClient
from sqlmodel import Session
import uuid

from app.core.config import settings
from app.models import Company, User, UserRole
from app.tests.utils.factories import create_random_company, create_random_user

def test_create_company(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Acme Corp", "details": "Leading manufacturer"}
    response = client.post(
        f"{settings.API_V1_STR}/companies/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert "id" in content

def test_create_company_by_normal_user_fails(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    data = {"name": "Unauthorized Corp"}
    response = client.post(
        f"{settings.API_V1_STR}/companies/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403

def test_read_companies_as_admin(
    client: TestClient, db: Session, admin_user_token_headers: dict[str, str]
) -> None:
    create_random_company(db)
    create_random_company(db)
    response = client.get(f"{settings.API_V1_STR}/companies/", headers=admin_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["count"] >= 2

def test_read_companies_as_normal_user(
    client: TestClient, db: Session, normal_user: User
) -> None:
    # Create another company that this user should not see
    create_random_company(db)
    from app.tests.conftest import get_auth_headers
    headers = get_auth_headers(normal_user)

    response = client.get(f"{settings.API_V1_STR}/companies/", headers=headers)
    assert response.status_code == 200
    content = response.json()
    # The normal user should only see their own company
    assert content["count"] == 1
    assert content["data"][0]["id"] == str(normal_user.company_id)

def test_read_company_by_id(
    client: TestClient, db: Session, admin_user_token_headers: dict[str, str]
) -> None:
    company = create_random_company(db)
    response = client.get(
        f"{settings.API_V1_STR}/companies/{company.id}",
        headers=admin_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(company.id)
    assert content["name"] == company.name

def test_read_other_company_by_normal_user_fails(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    other_company = create_random_company(db)
    response = client.get(
        f"{settings.API_V1_STR}/companies/{other_company.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403

def test_update_company(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    company = create_random_company(db)
    update_data = {"name": "Innovate Inc.", "is_demo": True}
    response = client.patch(
        f"{settings.API_V1_STR}/companies/{company.id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == update_data["name"]
    assert content["is_demo"] is True

def test_delete_company(
    client: TestClient, db: Session, admin_user_token_headers: dict[str, str]
) -> None:
    company = create_random_company(db)
    response = client.delete(
        f"{settings.API_V1_STR}/companies/{company.id}",
        headers=admin_user_token_headers,
    )
    assert response.status_code == 200
    db_company = db.get(Company, company.id)
    assert db_company is None
