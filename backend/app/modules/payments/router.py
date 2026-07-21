from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.core.permissions import require_student, require_student_or_admin, require_super_admin
from app.database.session import get_db
from app.integrations.payhere.schemas import PayHereCallback
from app.modules.payments.schemas import (
    InvoiceOut,
    PaymentOut,
    RefundRequestCreate,
    RefundRequestOut,
    RefundReviewRequest,
)
from app.modules.payments.service import PaymentService
from app.modules.users.models import User

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/payhere/initiate/{booking_id}")
def initiate_payhere(booking_id: str, current_user: User = Depends(require_student), db: Session = Depends(get_db)):
    return PaymentService(db).initiate_payhere_payment(current_user.id, booking_id)


@router.post("/payhere/callback")
def payhere_callback(
    merchant_id: str = Form(...),
    order_id: str = Form(...),
    payment_id: str = Form(...),
    payhere_amount: str = Form(...),
    payhere_currency: str = Form(...),
    status_code: str = Form(...),
    md5sig: str = Form(...),
    method: str = Form(None),
    status_message: str = Form(None),
    db: Session = Depends(get_db),
):
    callback = PayHereCallback(
        merchant_id=merchant_id,
        order_id=order_id,
        payment_id=payment_id,
        payhere_amount=payhere_amount,
        payhere_currency=payhere_currency,
        status_code=status_code,
        md5sig=md5sig,
        method=method,
        status_message=status_message,
    )
    PaymentService(db).handle_payhere_callback(callback)
    return {"received": True}


@router.get("/history/me", response_model=list[PaymentOut])
def my_payment_history(current_user: User = Depends(require_student), db: Session = Depends(get_db)):
    return PaymentService(db).get_history_for_student(current_user.id)


@router.get("/{payment_id}/invoice", response_model=InvoiceOut)
def get_invoice(payment_id: str, current_user: User = Depends(require_student_or_admin), db: Session = Depends(get_db)):
    from app.core.constants import UserRole

    return PaymentService(db).get_invoice(payment_id, current_user.id, current_user.role == UserRole.SUPER_ADMIN)


@router.post("/refunds", response_model=RefundRequestOut, status_code=201)
def request_refund(payload: RefundRequestCreate, current_user: User = Depends(require_student), db: Session = Depends(get_db)):
    return PaymentService(db).request_refund(current_user.id, payload)


@router.get("/admin/refunds", response_model=list[RefundRequestOut])
def list_refund_requests(current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return PaymentService(db).get_all_refund_requests()


@router.post("/admin/refunds/{refund_id}/review", response_model=RefundRequestOut)
def review_refund(
    refund_id: str, payload: RefundReviewRequest, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)
):
    return PaymentService(db).review_refund(current_user.id, refund_id, payload)


@router.get("/admin/all", response_model=list[PaymentOut])
def list_all_payments(current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return PaymentService(db).get_all_for_admin()
