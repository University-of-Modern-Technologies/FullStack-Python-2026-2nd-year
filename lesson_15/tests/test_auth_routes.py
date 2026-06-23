from unittest.mock import Mock

import pytest

from src.services.auth import create_verification_token


NEW_USER = {
    "username": "agent007",
    "email": "agent007@gmail.com",
    "password": "12345678",
}


def test_register_user(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_verification_email", mock_send_email)

    response = client.post("/api/auth/register", json=NEW_USER)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == NEW_USER["username"]
    assert data["email"] == NEW_USER["email"]
    assert data["role"] == "user"
    assert data["avatar_url"] is None
    assert "password" not in data
    mock_send_email.assert_called_once()


def test_register_duplicate_user_returns_409(client, monkeypatch):
    monkeypatch.setattr("src.routes.auth.send_verification_email", Mock())
    duplicate = {
        "username": "user_demo",
        "email": "user@example.com",
        "password": "12345678",
    }

    response = client.post("/api/auth/register", json=duplicate)

    assert response.status_code == 409, response.text
    assert response.json()["detail"] == "Username or email already exists"


def test_login_verified_user_returns_token_pair(client):
    response = client.post(
        "/api/auth/login",
        data={"username": "user_demo", "password": "12345678"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]


def test_login_unverified_user_returns_403(client):
    response = client.post(
        "/api/auth/login",
        data={"username": "mail_demo", "password": "12345678"},
    )

    assert response.status_code == 403, response.text
    assert "Email" in response.json()["detail"]


def test_verify_email_marks_user_as_verified(client, seeded_users):
    token = create_verification_token(seeded_users["unverified"].id)

    response = client.get("/api/auth/verify-email", params={"token": token})

    assert response.status_code == 200, response.text
    assert "Email" in response.text


def test_resend_verification_mocks_email_sender(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_verification_email", mock_send_email)

    response = client.post(
        "/api/auth/resend-verification",
        json={"email": "mail@example.com"},
    )

    assert response.status_code == 204, response.text
    mock_send_email.assert_called_once()


def test_refresh_token_returns_new_access_token(client):
    login_response = client.post(
        "/api/auth/login",
        data={"username": "user_demo", "password": "12345678"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200, response.text
    assert response.json()["access_token"]
    assert response.json()["token_type"] == "bearer"


@pytest.mark.skip(reason="Temporary skip while logout revocation behavior is being revised.")
def test_logout_revokes_refresh_token(client, auth_headers):
    login_response = client.post(
        "/api/auth/login",
        data={"username": "user_demo", "password": "12345678"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh_token},
        headers=auth_headers("user"),
    )

    assert response.status_code == 204, response.text
    refresh_response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 401
