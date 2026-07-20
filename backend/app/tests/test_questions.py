def _login(client, email, password):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]


def test_anonymous_question_hides_identity(client, register_student, register_mentor):
    register_student(email="anon.student@example.com", password="Student123!")
    student_token = _login(client, "anon.student@example.com", "Student123!")

    resp = client.post(
        "/api/v1/questions",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"title": "Sensitive question", "body": "Please help", "visibility": "ANONYMOUS"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["author_name"] == "Anonymous Student"
    assert "student_id" not in body
    assert "anon.student" not in str(body)


def test_public_question_shows_author_name(client, register_student):
    register_student(email="public.student@example.com", password="Student123!")
    token = _login(client, "public.student@example.com", "Student123!")

    resp = client.post(
        "/api/v1/questions",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Public question", "body": "Help please", "visibility": "PUBLIC"},
    )
    assert resp.status_code == 201
    assert resp.json()["author_name"] == "Test Student"


def test_helpful_vote_duplicate_prevented(client, register_student, register_mentor):
    register_student(email="voter@example.com", password="Student123!")
    student_token = _login(client, "voter@example.com", "Student123!")

    register_mentor(email="answerer@example.com", password="Mentor123!")
    mentor_token = _login(client, "answerer@example.com", "Mentor123!")

    q_resp = client.post(
        "/api/v1/questions",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"title": "Q", "body": "Need help", "visibility": "PUBLIC"},
    )
    question_id = q_resp.json()["id"]

    a_resp = client.post(
        f"/api/v1/questions/{question_id}/answers",
        headers={"Authorization": f"Bearer {mentor_token}"},
        json={"body": "Here is the answer"},
    )
    answer_id = a_resp.json()["id"]

    vote1 = client.post(
        f"/api/v1/questions/answers/{answer_id}/helpful", headers={"Authorization": f"Bearer {student_token}"}
    )
    assert vote1.status_code == 200
    assert vote1.json()["helpful_count"] == 1

    vote2 = client.post(
        f"/api/v1/questions/answers/{answer_id}/helpful", headers={"Authorization": f"Bearer {student_token}"}
    )
    assert vote2.status_code == 409
