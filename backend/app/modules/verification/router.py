from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.constants import DocumentType, VerificationStatus
from app.core.permissions import require_mentor, require_super_admin
from app.database.session import get_db
from app.modules.verification.repository import VerificationRepository
from app.modules.verification.schemas import (
    PendingMentorOut,
    VerificationDocumentOut,
    VerificationReviewOut,
    VerificationReviewRequest,
)
from app.modules.verification.service import VerificationService
from app.modules.users.models import User

router = APIRouter(prefix="/verification", tags=["Mentor Verification"])


@router.post("/documents", response_model=VerificationDocumentOut, status_code=201)
def upload_document(
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_mentor),
    db: Session = Depends(get_db),
):
    return VerificationService(db).upload_document(current_user.id, document_type, file)


@router.get("/documents/me", response_model=list[VerificationDocumentOut])
def my_documents(current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    from app.modules.mentors.repository import MentorRepository

    mentor = MentorRepository(db).get_by_user_id(current_user.id)
    return VerificationRepository(db).get_documents_for_mentor(mentor.id) if mentor else []


def _to_pending_out(mentors):
    return [
        PendingMentorOut(
            mentor_id=m.id,
            full_name=m.user.full_name,
            email=m.user.email,
            verification_status=m.verification_status,
            documents=m.verification_documents,
        )
        for m in mentors
    ]


@router.get("/pending", response_model=list[PendingMentorOut])
def pending_mentors(current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return _to_pending_out(VerificationService(db).get_pending_mentors())


@router.get("/queue/approved", response_model=list[PendingMentorOut])
def approved_queue(current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return _to_pending_out(VerificationRepository(db).get_mentors_by_status([VerificationStatus.APPROVED]))


@router.get("/queue/rejected", response_model=list[PendingMentorOut])
def rejected_queue(current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return _to_pending_out(VerificationRepository(db).get_mentors_by_status([VerificationStatus.REJECTED]))


@router.get("/queue/reupload-requested", response_model=list[PendingMentorOut])
def reupload_queue(current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return _to_pending_out(VerificationRepository(db).get_mentors_by_status([VerificationStatus.REUPLOAD_REQUESTED]))


@router.get("/status/me", response_model=VerificationReviewOut)
def my_verification_status(current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    from app.core.exceptions import NotFoundError
    from app.modules.mentors.repository import MentorRepository

    mentor = MentorRepository(db).get_by_user_id(current_user.id)
    if not mentor:
        raise NotFoundError("Mentor profile not found.")
    review = VerificationRepository(db).get_latest_review(mentor.id)
    if not review:
        raise NotFoundError("No verification review has been recorded yet.")
    return review


@router.post("/{mentor_id}/review", response_model=VerificationReviewOut)
def review_mentor(
    mentor_id: str,
    payload: VerificationReviewRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    return VerificationService(db).review_mentor(current_user.id, mentor_id, payload)
