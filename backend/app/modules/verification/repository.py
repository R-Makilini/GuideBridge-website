from sqlalchemy.orm import Session, joinedload

from app.core.constants import VerificationStatus
from app.modules.mentors.models import MentorProfile
from app.modules.verification.models import VerificationDocument, VerificationReview


class VerificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_document(self, document: VerificationDocument) -> VerificationDocument:
        self.db.add(document)
        self.db.flush()
        return document

    def get_documents_for_mentor(self, mentor_id: str) -> list[VerificationDocument]:
        return (
            self.db.query(VerificationDocument)
            .filter(VerificationDocument.mentor_id == mentor_id)
            .order_by(VerificationDocument.created_at.desc())
            .all()
        )

    def get_pending_mentors(self) -> list[MentorProfile]:
        return self.get_mentors_by_status([VerificationStatus.PENDING, VerificationStatus.REUPLOAD_REQUESTED])

    def get_mentors_by_status(self, statuses: list[VerificationStatus]) -> list[MentorProfile]:
        return (
            self.db.query(MentorProfile)
            .options(joinedload(MentorProfile.user), joinedload(MentorProfile.verification_documents))
            .filter(MentorProfile.verification_status.in_(statuses))
            .all()
        )

    def get_latest_review(self, mentor_id: str) -> VerificationReview | None:
        return (
            self.db.query(VerificationReview)
            .filter(VerificationReview.mentor_id == mentor_id)
            .order_by(VerificationReview.reviewed_at.desc())
            .first()
        )

    def add_review(self, review: VerificationReview) -> VerificationReview:
        self.db.add(review)
        self.db.flush()
        return review

    def commit(self):
        self.db.commit()
