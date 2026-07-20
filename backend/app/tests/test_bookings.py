from datetime import date, timedelta


def _login(client, email, password):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]


def _setup_mentor_with_slot(client, register_mentor):
    register_mentor(email="mentor.b@example.com", password="Mentor123!")
    token = _login(client, "mentor.b@example.com", "Mentor123!")

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post(
        "/api/v1/availability",
        headers={"Authorization": f"Bearer {token}"},
        json={"slot_date": tomorrow, "start_time": "10:00:00", "end_time": "11:00:00", "session_fee": 1500},
    )
    assert resp.status_code == 201
    slot = resp.json()
    return token, slot


def test_create_booking_success(client, register_mentor, register_student):
    mentor_token, slot = _setup_mentor_with_slot(client, register_mentor)

    register_student(email="student.b@example.com", password="Student123!")
    student_token = _login(client, "student.b@example.com", "Student123!")

    resp = client.post(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"slot_id": slot["id"], "topic": "Combined Maths help"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "PENDING"


def test_double_booking_prevented(client, register_mentor, register_student):
    mentor_token, slot = _setup_mentor_with_slot(client, register_mentor)

    register_student(email="student.c1@example.com", password="Student123!")
    token1 = _login(client, "student.c1@example.com", "Student123!")
    register_student(email="student.c2@example.com", password="Student123!")
    token2 = _login(client, "student.c2@example.com", "Student123!")

    resp1 = client.post(
        "/api/v1/bookings", headers={"Authorization": f"Bearer {token1}"}, json={"slot_id": slot["id"]}
    )
    assert resp1.status_code == 201

    resp2 = client.post(
        "/api/v1/bookings", headers={"Authorization": f"Bearer {token2}"}, json={"slot_id": slot["id"]}
    )
    assert resp2.status_code == 409


def test_mentor_cannot_book_own_slot(client, register_mentor):
    mentor_token, slot = _setup_mentor_with_slot(client, register_mentor)
    resp = client.post(
        "/api/v1/bookings", headers={"Authorization": f"Bearer {mentor_token}"}, json={"slot_id": slot["id"]}
    )
    # Mentor role is blocked from the student-only booking endpoint entirely.
    assert resp.status_code == 403


def test_past_date_slot_rejected(client, register_mentor):
    register_mentor(email="mentor.past@example.com", password="Mentor123!")
    token = _login(client, "mentor.past@example.com", "Mentor123!")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    resp = client.post(
        "/api/v1/availability",
        headers={"Authorization": f"Bearer {token}"},
        json={"slot_date": yesterday, "start_time": "10:00:00", "end_time": "11:00:00", "session_fee": 1000},
    )
    assert resp.status_code == 400


def test_overlapping_availability_rejected(client, register_mentor):
    mentor_token, slot = _setup_mentor_with_slot(client, register_mentor)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post(
        "/api/v1/availability",
        headers={"Authorization": f"Bearer {mentor_token}"},
        json={"slot_date": tomorrow, "start_time": "10:30:00", "end_time": "11:30:00", "session_fee": 1000},
    )
    assert resp.status_code == 409
