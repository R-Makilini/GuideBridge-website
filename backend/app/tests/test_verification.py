import io


def _register_and_login(client, register_fn, email, password):
    register_fn(email=email, password=password)
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login_resp.json()["access_token"]


def test_mentor_documents_upload_and_admin_review(client, register_mentor, register_student):
    mentor_token = _register_and_login(client, register_mentor, "mentor.v@example.com", "Mentor123!")

    file_content = b"%PDF-1.4 fake pdf content for testing"
    resp = client.post(
        "/api/v1/verification/documents",
        headers={"Authorization": f"Bearer {mentor_token}"},
        data={"document_type": "CV"},
        files={"file": ("cv.pdf", io.BytesIO(file_content), "application/pdf")},
    )
    assert resp.status_code == 201
    assert resp.json()["document_type"] == "CV"

    
    resp = client.get("/api/v1/mentors/me", headers={"Authorization": f"Bearer {mentor_token}"})
    assert resp.status_code == 200
    assert resp.json()["verification_status"] == "PENDING"
    assert resp.json()["is_publicly_visible"] is False


def test_unverified_mentor_not_in_search(client, register_mentor):
    mentor_token = _register_and_login(client, register_mentor, "mentor.search@example.com", "Mentor123!")
    resp = client.get("/api/v1/search/mentors")
    assert resp.status_code == 200
    ids = [m["id"] for m in resp.json()["items"]]
    
    my_profile = client.get("/api/v1/mentors/me", headers={"Authorization": f"Bearer {mentor_token}"}).json()
    assert my_profile["id"] not in ids
