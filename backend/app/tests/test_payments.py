import hashlib
from datetime import date, timedelta


def _login(client, email, password):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]


def _create_pending_booking(client, register_mentor, register_student):
    register_mentor(email="mentor.pay@example.com", password="Mentor123!")
    mentor_token = _login(client, "mentor.pay@example.com", "Mentor123!")

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    slot_resp = client.post(
        "/api/v1/availability",
        headers={"Authorization": f"Bearer {mentor_token}"},
        json={"slot_date": tomorrow, "start_time": "09:00:00", "end_time": "10:00:00", "session_fee": 2000},
    )
    slot = slot_resp.json()

    register_student(email="student.pay@example.com", password="Student123!")
    student_token = _login(client, "student.pay@example.com", "Student123!")

    booking_resp = client.post(
        "/api/v1/bookings", headers={"Authorization": f"Bearer {student_token}"}, json={"slot_id": slot["id"]}
    )
    return student_token, booking_resp.json()


def test_initiate_payhere_payment_builds_signed_payload(client, register_mentor, register_student):
    student_token, booking = _create_pending_booking(client, register_mentor, register_student)

    resp = client.post(
        f"/api/v1/payments/payhere/initiate/{booking['id']}", headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "payload" in body
    assert body["payload"]["order_id"]
    assert len(body["payload"]["hash"]) == 32  


def test_payhere_callback_rejects_invalid_signature(client, register_mentor, register_student):
    student_token, booking = _create_pending_booking(client, register_mentor, register_student)
    init_resp = client.post(
        f"/api/v1/payments/payhere/initiate/{booking['id']}", headers={"Authorization": f"Bearer {student_token}"}
    )
    order_id = init_resp.json()["payload"]["order_id"]

    resp = client.post(
        "/api/v1/payments/payhere/callback",
        data={
            "merchant_id": "wrong_merchant",
            "order_id": order_id,
            "payment_id": "PH12345",
            "payhere_amount": "2000.00",
            "payhere_currency": "LKR",
            "status_code": "2",
            "md5sig": "0" * 32,
        },
    )
    assert resp.status_code == 400


def test_payhere_callback_confirms_booking_on_valid_signature(client, register_mentor, register_student):
    from app.core.config import settings

    student_token, booking = _create_pending_booking(client, register_mentor, register_student)
    init_resp = client.post(
        f"/api/v1/payments/payhere/initiate/{booking['id']}", headers={"Authorization": f"Bearer {student_token}"}
    )
    order_id = init_resp.json()["payload"]["order_id"]

    merchant_id = settings.PAYHERE_MERCHANT_ID or "test_merchant"
    secret_hash = hashlib.md5(settings.PAYHERE_MERCHANT_SECRET.encode()).hexdigest().upper()
    amount = "2000.00"
    currency = "LKR"
    status_code = "2"
    raw = f"{merchant_id}{order_id}{amount}{currency}{status_code}{secret_hash}"
    md5sig = hashlib.md5(raw.encode()).hexdigest().upper()

    resp = client.post(
        "/api/v1/payments/payhere/callback",
        data={
            "merchant_id": merchant_id,
            "order_id": order_id,
            "payment_id": "PH12345",
            "payhere_amount": amount,
            "payhere_currency": currency,
            "status_code": status_code,
            "md5sig": md5sig,
        },
    )
    assert resp.status_code == 200

    booking_check = client.get(
        f"/api/v1/bookings/{booking['id']}", headers={"Authorization": f"Bearer {student_token}"}
    )
    assert booking_check.json()["status"] == "CONFIRMED"


def test_duplicate_payment_for_same_booking_prevented(client, register_mentor, register_student):
    student_token, booking = _create_pending_booking(client, register_mentor, register_student)

    r1 = client.post(
        f"/api/v1/payments/payhere/initiate/{booking['id']}", headers={"Authorization": f"Bearer {student_token}"}
    )
    assert r1.status_code == 200

    
    r2 = client.post(
        f"/api/v1/payments/payhere/initiate/{booking['id']}", headers={"Authorization": f"Bearer {student_token}"}
    )
    assert r2.status_code == 409
