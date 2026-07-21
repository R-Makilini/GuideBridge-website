from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.constants import VerificationStatus
from app.core.pagination import PageMeta
from app.modules.mentors.models import MentorExpertiseTag, MentorLanguage, MentorProfile, MentorSubject
from app.modules.search.schemas import MentorSearchParams
from app.modules.users.models import User


class MentorSearchService:
    def __init__(self, db: Session):
        self.db = db

    def search(self, params: MentorSearchParams):
        query = (
            self.db.query(MentorProfile)
            .join(User, User.id == MentorProfile.user_id)
            .options(joinedload(MentorProfile.user))
            .filter(
                MentorProfile.verification_status == VerificationStatus.APPROVED,
                MentorProfile.is_publicly_visible.is_(True),
            )
        )

        if params.name:
            query = query.filter(User.full_name.ilike(f"%{params.name}%"))
        if params.university_id:
            query = query.filter(MentorProfile.university_id == params.university_id)
        if params.faculty_id:
            query = query.filter(MentorProfile.faculty_id == params.faculty_id)
        if params.degree_id:
            query = query.filter(MentorProfile.degree_id == params.degree_id)
        if params.subject_id:
            query = query.join(MentorSubject).filter(MentorSubject.subject_id == params.subject_id)
        if params.expertise_tag_id:
            query = query.join(MentorExpertiseTag).filter(
                MentorExpertiseTag.tag_id == params.expertise_tag_id
            )
        if params.language:
            query = query.join(MentorLanguage).filter(MentorLanguage.language.ilike(params.language))

        if params.sort_by == "experienced":
            query = query.order_by(MentorProfile.completed_session_count.desc())
        elif params.sort_by == "newest":
            query = query.order_by(MentorProfile.created_at.desc())
        else:
            query = query.order_by(MentorProfile.helpful_score.desc())

        total = query.order_by(None).with_entities(func.count(func.distinct(MentorProfile.id))).scalar() or 0
        items = (
            query.distinct()
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
            .all()
        )

        total_pages = (total + params.page_size - 1) // params.page_size if total else 0
        meta = PageMeta(page=params.page, page_size=params.page_size, total_items=total, total_pages=total_pages)
        return items, meta
