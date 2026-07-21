from sqlalchemy.orm import Session

from app.modules.payments.models import Payment, PaymentEvent, RefundRequest


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_booking(self, booking_id: str) -> Payment | None:
        return self.db.query(Payment).filter(Payment.booking_id == booking_id).first()

    def get_by_order_id(self, order_id: str) -> Payment | None:
        return self.db.query(Payment).filter(Payment.gateway_order_id == order_id).first()

    def get(self, payment_id: str) -> Payment | None:
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def create(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.flush()
        return payment

    def add_event(self, event: PaymentEvent) -> None:
        self.db.add(event)

    def list_for_student(self, student_id: str):
        return self.db.query(Payment).filter(Payment.student_id == student_id).order_by(Payment.created_at.desc()).all()

    def create_refund_request(self, refund: RefundRequest) -> RefundRequest:
        self.db.add(refund)
        self.db.flush()
        return refund

    def get_refund(self, refund_id: str) -> RefundRequest | None:
        return self.db.query(RefundRequest).filter(RefundRequest.id == refund_id).first()

    def list_all_refund_requests(self):
        return self.db.query(RefundRequest).order_by(RefundRequest.created_at.desc()).all()

    def list_all_payments(self):
        return self.db.query(Payment).order_by(Payment.created_at.desc()).all()

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()
