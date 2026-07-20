from app.core.security import hash_password


def _make_admin(db_session):
    from app.core.constants import AuthProvider, UserRole, UserStatus
    from app.modules.users.models import User

    admin = User(
        email="admin@guidebridge.lk",
        full_name="Admin",
        hashed_password=hash_password("AdminPass123!"),
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        auth_provider=AuthProvider.LOCAL,
        is_email_verified=True,
    )
    db_session.add(admin)
    db_session.commit()
    return admin


def _login(client, email, password):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]


def test_admin_can_access_dashboard(client, db_session):
    _make_admin(db_session)
    token = _login(client, "admin@guidebridge.lk", "AdminPass123!")

    resp = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert "total_students" in body
    assert "platform_revenue" in body


def test_non_admin_cannot_access_admin_endpoints(client, register_student):
    register_student()
    token = _login(client, "student1@example.com", "Student123!")
    resp = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_admin_can_suspend_user(client, db_session, register_student):
    _make_admin(db_session)
    admin_token = _login(client, "admin@guidebridge.lk", "AdminPass123!")
    register_student()

    from app.modules.users.models import User

    student = db_session.query(User).filter(User.email == "student1@example.com").first()

    resp = client.post(
        f"/api/v1/admin/users/{student.id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "SUSPENDED", "reason": "Policy violation"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "SUSPENDED"

    # Suspended user should now be blocked from logging in.
    login_resp = client.post("/api/v1/auth/login", json={"email": "student1@example.com", "password": "Student123!"})
    assert login_resp.status_code == 401
