import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.core.security import verify_password
from app.models import Company, CompanyCreate, User, UserCreate, UserRole, UserAreaAssignmentLink, Area, AreaCreate
from app.tests.utils.utils import random_email, random_lower_string


@pytest.fixture(name="test_company")
def test_company_fixture(db: Session) -> Company:
    company_in = CompanyCreate(name=random_lower_string(), details="Test Company Details")
    # Create a superuser to create the company
    superuser_in = UserCreate(email=random_email(), password=random_lower_string(), is_superuser=True)
    superuser = crud.user.create(session=db, user_create=superuser_in)
    company = crud.company.create(session=db, company_in=company_in)
    db.commit()
    return company


@pytest.fixture(name="normal_user_with_company")
def normal_user_with_company_fixture(db: Session, test_company: Company) -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, company_id=test_company.id, role=UserRole.USER)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()
    user.password = password,
    return user


@pytest.fixture(name="auditor_user_with_company")
def auditor_user_with_company_fixture(db: Session, test_company: Company) -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, company_id=test_company.id, role=UserRole.AUDITOR)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()
    return user


@pytest.fixture(name="test_area")
def test_area_fixture(db: Session, test_company: Company) -> Area:
    area_in = AreaCreate(name=random_lower_string(), description="Test Area Description")
    assert test_company.id is not None
    area = crud.area.create(session=db, area_in=area_in, company_id=test_company.id)
    db.commit()
    return area


def test_get_users_superuser_me(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"]
    assert current_user["email"] == settings.FIRST_SUPERUSER


def test_get_users_normal_user_me(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is False
    assert current_user["email"] == settings.EMAIL_TEST_USER


def test_create_user_new_email(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session, test_company: Company
) -> None:
    with (
        patch("app.utils.send_email", return_value=None),
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.SMTP_USER", "admin@example.com"),
    ):
        username = random_email()
        password = random_lower_string()
        data = {"email": username, "password": password, "company_id": str(test_company.id), "role": UserRole.USER}
        r = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json=data,
        )
        assert 200 <= r.status_code < 300
        created_user = r.json()
        user = crud.user.get_by_email(session=db, email=username)
        assert user
        assert user.email == created_user["email"]
        assert user.company_id == test_company.id
        assert user.role == UserRole.USER


def test_get_existing_user(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session, test_company: Company
) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password, company_id=test_company.id, role=UserRole.USER)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()
    user_id = user.id
    r = client.get(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=superuser_token_headers,
    )
    assert 200 <= r.status_code < 300
    api_user = r.json()
    existing_user = crud.user.get_by_email(session=db, email=username)
    assert existing_user
    assert existing_user.email == api_user["email"]


def test_get_existing_user_current_user(client: TestClient, db: Session, normal_user_with_company: User) -> None:
    user_id = normal_user_with_company.id

    login_data = {
        "username": normal_user_with_company.email,
        "password": normal_user_with_company.password, # type: ignore
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    r = client.get(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=headers,
    )
    assert 200 <= r.status_code < 300
    api_user = r.json()
    assert normal_user_with_company.email == api_user["email"]


def test_get_existing_user_permissions_error(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session, test_company: Company
) -> None:
    # Create another user that the normal_user_token_headers user should not be able to see
    other_user_in = UserCreate(email=random_email(), password=random_lower_string(), company_id=test_company.id, role=UserRole.USER)
    other_user = crud.user.create(session=db, user_create=other_user_in)
    db.commit()

    r = client.get(
        f"{settings.API_V1_STR}/users/{other_user.id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "The user doesn't have enough privileges"


def test_create_user_existing_username(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session, test_company: Company
) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password, company_id=test_company.id, role=UserRole.USER)
    crud.user.create(session=db, user_create=user_in)
    db.commit()
    data = {"email": username, "password": password, "company_id": str(test_company.id), "role": UserRole.USER}
    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json=data,
    )
    created_user = r.json()
    assert r.status_code == 400
    assert "_id" not in created_user


def test_create_user_by_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str], test_company: Company
) -> None:
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password, "company_id": str(test_company.id), "role": UserRole.USER}
    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 403


def test_retrieve_users(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session, test_company: Company
) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password, company_id=test_company.id, role=UserRole.USER)
    crud.user.create(session=db, user_create=user_in)
    db.commit()

    username2 = random_email()
    password2 = random_lower_string()
    user_in2 = UserCreate(email=username2, password=password2, company_id=test_company.id, role=UserRole.USER)
    crud.user.create(session=db, user_create=user_in2)
    db.commit()

    r = client.get(f"{settings.API_V1_STR}/users/", headers=superuser_token_headers)
    all_users = r.json()

    assert len(all_users["data"]) > 1
    assert "count" in all_users
    for item in all_users["data"]:
        assert "email" in item


def test_update_user_me(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    full_name = "Updated Name"
    email = random_email()
    data = {"full_name": full_name, "email": email}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["email"] == email
    assert updated_user["full_name"] == full_name

    user_query = select(User).where(User.email == email)
    user_db = db.exec(user_query).first()
    assert user_db
    assert user_db.email == email
    assert user_db.full_name == full_name


def test_update_password_me(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    new_password = random_lower_string()
    data = {
        "current_password": settings.FIRST_SUPERUSER_PASSWORD,
        "new_password": new_password,
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["message"] == "Password updated successfully"

    user_query = select(User).where(User.email == settings.FIRST_SUPERUSER)
    user_db = db.exec(user_query).first()
    assert user_db
    assert user_db.email == settings.FIRST_SUPERUSER
    assert verify_password(new_password, user_db.hashed_password)

    # Revert to the old password to keep consistency in test
    old_data = {
        "current_password": new_password,
        "new_password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=old_data,
    )
    db.refresh(user_db)

    assert r.status_code == 200
    assert verify_password(settings.FIRST_SUPERUSER_PASSWORD, user_db.hashed_password)


def test_update_password_me_incorrect_password(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    new_password = random_lower_string()
    data = {"current_password": new_password, "new_password": new_password}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 400
    updated_user = r.json()
    assert updated_user["detail"] == "Incorrect password"


def test_update_user_me_email_exists(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session, test_company: Company
) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password, company_id=test_company.id, role=UserRole.USER)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()

    data = {"email": user.email}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "User with this email already exists"


def test_update_password_me_same_password_error(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "current_password": settings.FIRST_SUPERUSER_PASSWORD,
        "new_password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 400
    updated_user = r.json()
    assert (
        updated_user["detail"] == "New password cannot be the same as the current one"
    )


def test_register_user(client: TestClient, db: Session, test_company: Company) -> None:
    username = random_email()
    password = random_lower_string()
    full_name = random_lower_string()
    data = {"email": username, "password": password, "full_name": full_name, "company_id": str(test_company.id)}
    r = client.post(
        f"{settings.API_V1_STR}/users/signup",
        json=data,
    )
    assert r.status_code == 200
    created_user = r.json()
    assert created_user["email"] == username
    assert created_user["full_name"] == full_name
    assert created_user["company_id"] == str(test_company.id)

    user_query = select(User).where(User.email == username)
    user_db = db.exec(user_query).first()
    assert user_db
    assert user_db.email == username
    assert user_db.full_name == full_name
    assert verify_password(password, user_db.hashed_password)


def test_register_user_already_exists_error(client: TestClient) -> None:
    password = random_lower_string()
    full_name = random_lower_string()
    data = {
        "email": settings.FIRST_SUPERUSER,
        "password": password,
        "full_name": full_name,
    }
    r = client.post(
        f"{settings.API_V1_STR}/users/signup",
        json=data,
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "The user with this email already exists in the system"


def test_update_user(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session, test_company: Company
) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password, company_id=test_company.id, role=UserRole.USER)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()

    data = {"full_name": "Updated_full_name"}
    r = client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()

    assert updated_user["full_name"] == "Updated_full_name"

    user_query = select(User).where(User.email == username)
    user_db = db.exec(user_query).first()
    db.refresh(user_db)
    assert user_db
    assert user_db.full_name == "Updated_full_name"


def test_update_user_not_exists(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"full_name": "Updated_full_name"}
    r = client.patch(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "The user with this id does not exist in the system"


def test_update_user_email_exists(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session, test_company: Company
) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password, company_id=test_company.id, role=UserRole.USER)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()

    username2 = random_email()
    password2 = random_lower_string()
    user_in2 = UserCreate(email=username2, password=password2, company_id=test_company.id, role=UserRole.USER)
    user2 = crud.user.create(session=db, user_create=user_in2)
    db.commit()

    data = {"email": user2.email}
    r = client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "User with this email already exists"


def test_delete_user_me(client: TestClient, db: Session, normal_user_with_company: User) -> None:
    user_id = normal_user_with_company.id

    login_data = {
        "username": normal_user_with_company.email,
        "password": normal_user_with_company.password, # type: ignore
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    r = client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=headers,
    )
    assert r.status_code == 200
    deleted_user = r.json()
    assert deleted_user["message"] == "User deleted successfully"
    result = db.exec(select(User).where(User.id == user_id)).first()
    assert result is None

    user_query = select(User).where(User.id == user_id)
    user_db = db.execute(user_query).first()
    assert user_db is None


def test_delete_user_me_as_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=superuser_token_headers,
    )
    assert r.status_code == 403
    response = r.json()
    assert response["detail"] == "Super users are not allowed to delete themselves"


def test_delete_user_super_user(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session, test_company: Company
) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password, company_id=test_company.id, role=UserRole.USER)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()
    user_id = user.id
    r = client.delete(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    deleted_user = r.json()
    assert deleted_user["message"] == "User deleted successfully"
    result = db.exec(select(User).where(User.id == user_id)).first()
    assert result is None


def test_delete_user_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.delete(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


def test_delete_user_current_super_user_error(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    super_user = crud.user.get_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert super_user
    user_id = super_user.id

    r = client.delete(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Super users are not allowed to delete themselves"


def test_delete_user_without_privileges(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session, test_company: Company
) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password, company_id=test_company.id, role=UserRole.USER)
    user = crud.user.create(session=db, user_create=user_in)
    db.commit()

    r = client.delete(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "The user doesn't have enough privileges"


def test_assign_user_to_areas(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session, normal_user_with_company: User, test_area: Area
) -> None:
    user_id = normal_user_with_company.id
    area_id = test_area.id

    response = client.post(
        f"{settings.API_V1_STR}/users/{user_id}/assign-areas",
        headers=superuser_token_headers,
        json=[str(area_id)],
    )
    assert response.status_code == 200
    updated_user = response.json()
    assert len(updated_user["assigned_areas"]) == 1
    assert updated_user["assigned_areas"][0]["id"] == str(area_id)

    # Verify in DB
    user_db = db.get(User, user_id)
    assert user_db
    assert len(user_db.assigned_areas) == 1
    assert user_db.assigned_areas[0].id == area_id


def test_assign_user_to_areas_invalid_area(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session, normal_user_with_company: User
) -> None:
    user_id = normal_user_with_company.id
    invalid_area_id = uuid.uuid4()

    response = client.post(
        f"{settings.API_V1_STR}/users/{user_id}/assign-areas",
        headers=superuser_token_headers,
        json=[str(invalid_area_id)],
    )
    assert response.status_code == 400
    assert "not found or does not belong to user's company" in response.json()["detail"]


def test_remove_user_from_area(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session, normal_user_with_company: User, test_area: Area
) -> None:
    user_id = normal_user_with_company.id
    area_id = test_area.id

    # First assign the user to the area
    assign_response = client.post(
        f"{settings.API_V1_STR}/users/{user_id}/assign-areas",
        headers=superuser_token_headers,
        json=[str(area_id)],
    )
    assert assign_response.status_code == 200
    user_db_after_assign = db.get(User, user_id)
    assert user_db_after_assign
    db.refresh(user_db_after_assign, attribute_names=["area_links"])
    assert len(user_db_after_assign.assigned_areas) == 1

    # Then remove the user from the area
    remove_response = client.delete(
        f"{settings.API_V1_STR}/users/{user_id}/remove-area/{area_id}",
        headers=superuser_token_headers,
    )
    assert remove_response.status_code == 200
    assert remove_response.json()["message"] == "User successfully removed from area."

    # Verify in DB
    user_db_after_remove = db.get(User, user_id)
    assert user_db_after_remove
    db.refresh(user_db_after_remove, attribute_names=["area_links"])
    assert len(user_db_after_remove.assigned_areas) == 0


def test_remove_user_from_area_not_assigned(
    client: TestClient, superuser_token_headers: dict[str, str], normal_user_with_company: User, test_area: Area
) -> None:
    user_id = normal_user_with_company.id
    area_id = test_area.id

    response = client.delete(
        f"{settings.API_V1_STR}/users/{user_id}/remove-area/{area_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User is not assigned to this area."
