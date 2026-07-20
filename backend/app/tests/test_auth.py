import pytest
from pydantic import ValidationError

from app.modules.auth.schemas import ChangePasswordRequest, ResetPasswordRequest


def test_student_registration(client, register_student):
    resp = register_student()
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "student1@example.com"
    assert body["role"] == "STUDENT"


def test_duplicate_registration_conflicts(client, register_student):
    register_student()
    resp = register_student()
    assert resp.status_code == 409


def test_mentor_registration(client, register_mentor):
    resp = register_mentor()
    assert resp.status_code == 201
    assert resp.json()["role"] == "MENTOR"


def test_registration_rejects_mismatched_password_confirmation(client):
    resp = client.post(
        "/api/v1/auth/register/student",
        json={
            "full_name": "Test Student",
            "email": "mismatch@example.com",
            "password": "Student123!",
            "confirm_password": "Different123!",
        },
    )

    assert resp.status_code == 422
    assert "Passwords do not match" in resp.text


@pytest.mark.parametrize(
    ("request_type", "payload"),
    [
        (
            ResetPasswordRequest,
            {"token": "reset-token", "new_password": "Student123!", "confirm_password": "Different123!"},
        ),
        (
            ChangePasswordRequest,
            {
                "current_password": "OldPassword123!",
                "new_password": "Student123!",
                "confirm_password": "Different123!",
            },
        ),
    ],
)
def test_new_password_flows_reject_mismatched_confirmation(request_type, payload):
    with pytest.raises(ValidationError, match="Passwords do not match"):
        request_type(**payload)


def test_login_success(client, register_student):
    register_student()
    resp = client.post("/api/v1/auth/login", json={"email": "student1@example.com", "password": "Student123!"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_login_wrong_password_rejected(client, register_student):
    register_student()
    resp = client.post("/api/v1/auth/login", json={"email": "student1@example.com", "password": "WrongPass123!"})
    assert resp.status_code == 401


def test_refresh_token_flow(client, register_student):
    register_student()
    login_resp = client.post("/api/v1/auth/login", json={"email": "student1@example.com", "password": "Student123!"})
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()

    # Old refresh token should now be rejected (rotation).
    reuse_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse_resp.status_code == 401


def test_authorization_requires_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_authorization_role_gate(client, register_student):
    register_student()
    login_resp = client.post("/api/v1/auth/login", json={"email": "student1@example.com", "password": "Student123!"})
    token = login_resp.json()["access_token"]

    # A student should not be able to access mentor-only endpoints.
    resp = client.get("/api/v1/mentors/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_admin_endpoints_require_admin_role(client, register_student):
    register_student()
    login_resp = client.post("/api/v1/auth/login", json={"email": "student1@example.com", "password": "Student123!"})
    token = login_resp.json()["access_token"]

    resp = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
