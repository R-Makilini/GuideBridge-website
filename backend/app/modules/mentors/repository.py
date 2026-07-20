from sqlalchemy.orm import Session, joinedload

from app.core.constants import VerificationStatus
from app.modules.mentors.models import MentorExpertiseTag, MentorLanguage, MentorProfile, MentorSubject


class MentorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: str) -> MentorProfile | None:
        return self.db.query(MentorProfile).filter(MentorProfile.user_id == user_id).first()

    def get_by_id(self, mentor_id: str) -> MentorProfile | None:
        return self.db.query(MentorProfile).filter(MentorProfile.id == mentor_id).first()

    def get_public_profile(self, mentor_id: str) -> MentorProfile | None:
        return (
            self.db.query(MentorProfile)
            .options(joinedload(MentorProfile.user))
            .filter(
                MentorProfile.id == mentor_id,
                MentorProfile.verification_status == VerificationStatus.APPROVED,
                MentorProfile.is_publicly_visible.is_(True),
            )
            .first()
        )

    def replace_subjects(self, mentor_id: str, subject_ids: list[str]) -> None:
        self.db.query(MentorSubject).filter(MentorSubject.mentor_id == mentor_id).delete()
        for sid in set(subject_ids):
            self.db.add(MentorSubject(mentor_id=mentor_id, subject_id=sid))

    def replace_expertise_tags(self, mentor_id: str, tag_ids: list[str]) -> None:
        self.db.query(MentorExpertiseTag).filter(MentorExpertiseTag.mentor_id == mentor_id).delete()
        for tid in set(tag_ids):
            self.db.add(MentorExpertiseTag(mentor_id=mentor_id, tag_id=tid))

    def replace_languages(self, mentor_id: str, languages: list[str]) -> None:
        self.db.query(MentorLanguage).filter(MentorLanguage.mentor_id == mentor_id).delete()
        for lang in set(languages):
            self.db.add(MentorLanguage(mentor_id=mentor_id, language=lang))

    def commit(self):
        self.db.commit()


class MentorRegistrationProgressRepository:
    def __init__(self, db):
        self.db = db

    def get_or_create(self, mentor_id: str):
        from app.modules.mentors.models import MentorRegistrationProgress

        progress = (
            self.db.query(MentorRegistrationProgress)
            .filter(MentorRegistrationProgress.mentor_id == mentor_id)
            .first()
        )
        if not progress:
            progress = MentorRegistrationProgress(mentor_id=mentor_id)
            self.db.add(progress)
            self.db.flush()
        return progress

    def commit(self):
        self.db.commit()
