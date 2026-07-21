import json
import uuid
from datetime import datetime, timezone
from app.core.datetime_utils import utcnow

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import BookingStatus, NotificationType, PaymentStatus, RefundStatus
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.integrations.payhere.client import build_checkout_payload, checkout_endpoint
from app.integrations.payhere.schemas import PayHereCallback
from app.integrations.payhere.signatures import verify_callback_signature
from app.modules.admin.models import SystemSetting
from app.modules.bookings.repository import BookingRepository
from app.modules.notifications.service import NotificationService
from app.modules.payments.models import Payment, PaymentEvent, RefundRequest
from app.modules.payments.repository import PaymentRepository
from app.modules.payments.schemas import InvoiceOut, RefundRequestCreate, RefundReviewRequest


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PaymentRepository(db)
        self.booking_repo = BookingRepository(db)
        self.notifications = NotificationService(db)

    def _commission_percent(self) -> float:
        setting = self.db.query(SystemSetting).filter(SystemSetting.key == "platform_commission_percent").first()
        if setting:
            try:
                return float(setting.value)
            except ValueError:
                pass
        return float(settings.DEFAULT_PLATFORM_COMMISSION_PERCENT)

    def initiate_payhere_payment(self, student_id: str, booking_id: str) -> dict:
        booking = self.booking_repo.get(booking_id)
        if not booking:
            raise NotFoundError("Booking not found.")
        if booking.student_id != student_id:
            raise ForbiddenError("This booking does not belong to you.")
        if booking.status != BookingStatus.PENDING:
            raise ConflictError("Payment can only be initiated for pending bookings.")

        existing = self.repo.get_by_booking(booking_id)
        if existing and existing.status == PaymentStatus.PAID:
            raise ConflictError("This booking has already been paid for.")

        order_id = existing.gateway_order_id if existing else f"GB-{uuid.uuid4().hex[:12].upper()}"

        commission_pct = self._commission_percent()
        commission = round(float(booking.fee) * commission_pct / 100, 2)
        mentor_earnings = round(float(booking.fee) - commission, 2)

        if existing:
            payment = existing
            payment.amount = booking.fee
            payment.platform_commission = commission
            payment.mentor_earnings = mentor_earnings
            payment.status = PaymentStatus.PENDING
        else:
            payment = Payment(
                booking_id=booking.id,
                student_id=student_id,
                gateway_order_id=order_id,
                amount=booking.fee,
                currency="LKR",
                platform_commission=commission,
                mentor_earnings=mentor_earnings,
                status=PaymentStatus.PENDING,
            )
            self.repo.create(payment)

        booking.status = BookingStatus.PAYMENT_PENDING
        self.db.add(booking)
        self.repo.commit()

        student = booking.student
        checkout_payload = build_checkout_payload(
            order_id=order_id,
            amount=float(booking.fee),
            items_description=f"GuideBridge mentoring session ({booking.topic or 'session'})",
            first_name=student.full_name.split(" ")[0],
            last_name=" ".join(student.full_name.split(" ")[1:]) or ".",
            email=student.email,
            phone=student.phone or "0000000000",
        )
        return {"checkout_url": checkout_endpoint(), "payload": checkout_payload.model_dump()}

    def handle_payhere_callback(self, callback: PayHereCallback) -> Payment:
        valid = verify_callback_signature(
            merchant_id=callback.merchant_id,
            order_id=callback.order_id,
            amount=callback.payhere_amount,
            currency=callback.payhere_currency,
            status_code=callback.status_code,
            md5sig=callback.md5sig,
        )

        payment = self.repo.get_by_order_id(callback.order_id)
        if not payment:
            raise NotFoundError("Payment not found for this order.")

        event = PaymentEvent(
            payment_id=payment.id,
            event_type="payhere_callback",
            raw_payload=json.dumps(callback.model_dump()),
            signature_valid=valid,
        )
        self.repo.add_event(event)

        if not valid:
            payment.status = PaymentStatus.FAILED
            self.db.add(payment)
            self.repo.commit()
            raise BadRequestError("Invalid PayHere callback signature.")

        booking = self.booking_repo.get(payment.booking_id)

        # PayHere status codes: 2 = success, 0 = pending, -1 = cancelled, -2 = failed, -3 = charged back
        if callback.status_code == "2":
            payment.status = PaymentStatus.PAID
            payment.gateway_payment_id = callback.payment_id
            payment.paid_at = utcnow()
            if booking:
                booking.status = BookingStatus.CONFIRMED
                booking.confirmed_at = utcnow()
                self.db.add(booking)
            self.notifications.notify(
                payment.student_id, NotificationType.PAYMENT_SUCCESS, "Payment Successful",
                "Your payment was processed successfully.", auto_commit=False,
            )
        elif callback.status_code == "0":
            payment.status = PaymentStatus.PROCESSING
        elif callback.status_code == "-1":
            payment.status = PaymentStatus.CANCELLED
            self.notifications.notify(
                payment.student_id, NotificationType.PAYMENT_FAILURE, "Payment Cancelled",
                "Your payment was cancelled.", auto_commit=False,
            )
        else:
            payment.status = PaymentStatus.FAILED
            self.notifications.notify(
                payment.student_id, NotificationType.PAYMENT_FAILURE, "Payment Failed",
                "Your payment could not be processed.", auto_commit=False,
            )

        self.db.add(payment)
        self.repo.commit()
        return payment

    def request_refund(self, user_id: str, payload: RefundRequestCreate) -> RefundRequest:
        payment = self.repo.get(payload.payment_id)
        if not payment:
            raise NotFoundError("Payment not found.")
        if payment.student_id != user_id:
            raise ForbiddenError("This payment does not belong to you.")
        if payment.status != PaymentStatus.PAID:
            raise ConflictError("Only successfully paid transactions can be refunded.")

        refund = RefundRequest(payment_id=payment.id, requested_by_id=user_id, reason=payload.reason)
        self.repo.create_refund_request(refund)
        self.repo.commit()
        return refund

    def review_refund(self, admin_id: str, refund_id: str, payload: RefundReviewRequest) -> RefundRequest:
        refund = self.repo.get_refund(refund_id)
        if not refund:
            raise NotFoundError("Refund request not found.")

        refund.status = payload.status
        refund.admin_notes = payload.admin_notes
        if payload.status == RefundStatus.PROCESSED:
            refund.processed_at = utcnow()
            payment = self.repo.get(refund.payment_id)
            payment.status = PaymentStatus.REFUNDED
            self.db.add(payment)

        self.db.add(refund)
        self.repo.commit()
        return refund

    def get_history_for_student(self, student_id: str):
        return self.repo.list_for_student(student_id)

    def get_all_for_admin(self):
        return self.repo.list_all_payments()

    def get_all_refund_requests(self):
        return self.repo.list_all_refund_requests()

    def get_invoice(self, payment_id: str, user_id: str, is_admin: bool) -> InvoiceOut:
        payment = self.repo.get(payment_id)
        if not payment:
            raise NotFoundError("Payment not found.")
        if not is_admin and payment.student_id != user_id:
            raise ForbiddenError("This payment does not belong to you.")

        booking = self.booking_repo.get(payment.booking_id)
        mentor_name = booking.mentor.user.full_name if booking and booking.mentor else "Unknown Mentor"

        return InvoiceOut(
            invoice_number=f"INV-{payment.id[:8].upper()}",
            payment_id=payment.id,
            booking_id=payment.booking_id,
            student_name=payment.student.full_name,
            mentor_name=mentor_name,
            amount=float(payment.amount),
            currency=payment.currency,
            platform_commission=float(payment.platform_commission),
            mentor_earnings=float(payment.mentor_earnings),
            status=payment.status,
            issued_at=payment.created_at,
            paid_at=payment.paid_at,
        )
