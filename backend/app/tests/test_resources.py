import io


def _login(client, email, password):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]


def test_resource_pending_by_default_and_hidden_from_public_list(client, register_student):
    register_student(email="uploader@example.com", password="Student123!")
    token = _login(client, "uploader@example.com", "Student123!")

    resp = client.post(
        "/api/v1/resources",
        headers={"Authorization": f"Bearer {token}"},
        data={"title": "Physics Notes", "resource_type": "STUDY_NOTE", "is_premium": "false"},
        files={"file": ("notes.pdf", io.BytesIO(b"%PDF-1.4 notes"), "application/pdf")},
    )
    assert resp.status_code == 201
    assert resp.json()["approval_status"] == "PENDING"

    public_list = client.get("/api/v1/resources")
    assert all(r["id"] != resp.json()["id"] for r in public_list.json()["items"])


def test_only_owner_can_edit_resource(client, register_student):
    register_student(email="owner@example.com", password="Student123!")
    owner_token = _login(client, "owner@example.com", "Student123!")

    register_student(email="intruder@example.com", password="Student123!")
    intruder_token = _login(client, "intruder@example.com", "Student123!")

    resp = client.post(
        "/api/v1/resources",
        headers={"Authorization": f"Bearer {owner_token}"},
        data={"title": "My Notes", "resource_type": "STUDY_NOTE", "is_premium": "false"},
        files={"file": ("notes.pdf", io.BytesIO(b"%PDF-1.4 notes"), "application/pdf")},
    )
    resource_id = resp.json()["id"]

    edit_resp = client.put(
        f"/api/v1/resources/{resource_id}",
        headers={"Authorization": f"Bearer {intruder_token}"},
        json={"title": "Hacked title"},
    )
    assert edit_resp.status_code == 403


def test_premium_resource_requires_purchase_to_download(client, register_student):
    register_student(email="premium.uploader@example.com", password="Student123!")
    uploader_token = _login(client, "premium.uploader@example.com", "Student123!")

    resp = client.post(
        "/api/v1/resources",
        headers={"Authorization": f"Bearer {uploader_token}"},
        data={"title": "Premium Notes", "resource_type": "STUDY_NOTE", "is_premium": "true"},
        files={"file": ("premium.pdf", io.BytesIO(b"%PDF-1.4 premium"), "application/pdf")},
    )
    resource_id = resp.json()["id"]

    from app.core.constants import ResourceApprovalStatus

    download_resp = client.post(
        f"/api/v1/resources/{resource_id}/download", headers={"Authorization": f"Bearer {uploader_token}"}
    )
    
    assert download_resp.status_code == 404
