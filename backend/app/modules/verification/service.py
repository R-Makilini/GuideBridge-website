from datetime import datetime, timezone
from app.core.datetime_utils import utcnow

from sqlalchemy.orm import Session

from app.core.constants import DocumentType, NotificationType, VerificationStatus
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.file_validation import safe_file_key, validate_upload
from app.integrations.storage import get_storage_backend
from app.modules.mentors.repository import MentorRepository
from app.modules.notifications.service import NotificationService
from app.modules.verification.models import VerificationDocument, VerificationReview
from app.modules.verification.repository import VerificationRepository
from app.modules.verification.schemas import VerificationReviewRequest


class VerificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = VerificationRepository(db)
        self.mentor_repo = MentorRepository(db)
        self.notifications = NotificationService(db)

    def upload_document(self, mentor_user_id: str, document_type: DocumentType, file) -> VerificationDocument:
        mentor = self.mentor_repo.get_by_user_id(mentor_user_id)
        if not mentor:
            raise NotFoundError("Mentor profile not found.")

        validate_upload(file)
        key, safe_name = safe_file_key(file.filename, folder=f"verification/{mentor.id}")
        url = get_storage_backend().upload(file.file, key, file.content_type)

        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        document = VerificationDocument(
            mentor_id=mentor.id,
            document_type=document_type,
            file_url=url,
            file_name=safe_name,
            mime_type=file.content_type,
            file_size_bytes=size,
        )
        self.repo.add_document(document)

        if mentor.verification_status in (VerificationStatus.REJECTED,):
            mentor.verification_status = VerificationStatus.PENDING
            self.db.add(mentor)

        self.repo.commit()
        return document

    def get_pending_mentors(self):
        return self.repo.get_pending_mentors()

    def review_mentor(self, admin_id: str, mentor_id: str, payload: VerificationReviewRequest):
        mentor = self.mentor_repo.get_by_id(mentor_id)
        if not mentor:
            raise NotFoundError("Mentor not found.")

        if payload.status not in VerificationStatus:
            raise BadRequestError("Invalid verification status.")

        mentor.verification_status = payload.status
        mentor.is_publicly_visible = payload.status == VerificationStatus.APPROVED
        self.db.add(mentor)

        review = VerificationReview(
            mentor_id=mentor.id,
            reviewed_by_id=admin_id,
            status=payload.status,
            admin_notes=payload.admin_notes,
            reviewed_at=utcnow(),
        )
        self.repo.add_review(review)

        status_messages = {
            VerificationStatus.APPROVED: "Congratulations! Your mentor account has been verified.",
            VerificationStatus.REJECTED: "Your mentor verification was rejected. Please review the notes and resubmit.",
            VerificationStatus.REUPLOAD_REQUESTED: "Please re-upload your verification documents.",
        }
        message = status_messages.get(payload.status, "Your verification status has been updated.")
        self.notifications.notify(
            user_id=mentor.user_id,
            type_=NotificationType.MENTOR_VERIFICATION,
            title="Mentor Verification Update",
            body=message,
            auto_commit=False,
        )

        self.repo.commit()
        return review
