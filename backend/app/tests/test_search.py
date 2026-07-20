def _login(client, email, password):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]


def _approve_mentor(db_session, mentor_email):
    from app.core.constants import VerificationStatus
    from app.modules.mentors.models import MentorProfile
    from app.modules.users.models import User

    user = db_session.query(User).filter(User.email == mentor_email).first()
    profile = db_session.query(MentorProfile).filter(MentorProfile.user_id == user.id).first()
    profile.verification_status = VerificationStatus.APPROVED
    profile.is_publicly_visible = True
    db_session.add(profile)
    db_session.commit()
    return profile


def test_search_returns_only_approved_mentors(client, db_session, register_mentor, register_student):
    register_mentor(email="approved@example.com", password="Mentor123!")
    register_mentor(email="pending@example.com", password="Mentor123!")

    _approve_mentor(db_session, "approved@example.com")

    resp = client.get("/api/v1/search/mentors")
    assert resp.status_code == 200
    body = resp.json()
    names = [m["full_name"] for m in body["items"]]
    assert "Test Mentor" in names  
    assert body["meta"]["total_items"] == 1


def test_search_pagination_and_sorting_params_accepted(client, db_session, register_mentor):
    register_mentor(email="sortme@example.com", password="Mentor123!")
    _approve_mentor(db_session, "sortme@example.com")

    resp = client.get("/api/v1/search/mentors", params={"sort_by": "experienced", "page": 1, "page_size": 5})
    assert resp.status_code == 200
    assert resp.json()["meta"]["page"] == 1
    assert resp.json()["meta"]["page_size"] == 5
