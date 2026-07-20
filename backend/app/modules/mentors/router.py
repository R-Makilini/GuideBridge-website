from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.file_validation import safe_file_key, validate_upload
from app.core.permissions import require_mentor
from app.database.session import get_db
from app.integrations.storage import get_storage_backend
from app.modules.mentors.repository import MentorRegistrationProgressRepository
from app.modules.mentors.schemas import (
    MentorDashboardOut,
    MentorEarningsSummaryOut,
    MentorProfileOut,
    MentorProfileUpdate,
    PublicMentorProfileOut,
    RegistrationProgressOut,
    RegistrationProgressUpdate,
)
from app.modules.mentors.service import MentorService
from app.modules.users.models import User

router = APIRouter(prefix="/mentors", tags=["Mentors"])


@router.get("/me/registration-progress", response_model=RegistrationProgressOut)
def get_registration_progress(current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    mentor = MentorService(db).get_own_profile(current_user.id)
    progress = MentorRegistrationProgressRepository(db).get_or_create(mentor.id)
    db.commit()
    return RegistrationProgressOut(
        mentor_id=mentor.id,
        personal_info_completed=progress.personal_info_completed,
        university_info_completed=progress.university_info_completed,
        documents_uploaded=progress.documents_uploaded,
        completion_percentage=progress.completion_percentage,
    )


@router.put("/me/registration-progress", response_model=RegistrationProgressOut)
def update_registration_progress(
    payload: RegistrationProgressUpdate, current_user: User = Depends(require_mentor), db: Session = Depends(get_db)
):
    mentor = MentorService(db).get_own_profile(current_user.id)
    repo = MentorRegistrationProgressRepository(db)
    progress = repo.get_or_create(mentor.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(progress, field, value)
    db.add(progress)
    repo.commit()
    return RegistrationProgressOut(
        mentor_id=mentor.id,
        personal_info_completed=progress.personal_info_completed,
        university_info_completed=progress.university_info_completed,
        documents_uploaded=progress.documents_uploaded,
        completion_percentage=progress.completion_percentage,
    )


@router.get("/me", response_model=MentorProfileOut)
def get_my_profile(current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    profile = MentorService(db).get_own_profile(current_user.id)
    return _to_out(profile)


@router.put("/me", response_model=MentorProfileOut)
def update_my_profile(
    payload: MentorProfileUpdate,
    current_user: User = Depends(require_mentor),
    db: Session = Depends(get_db),
):
    profile = MentorService(db).update_own_profile(current_user.id, payload)
    return _to_out(profile)


@router.post("/me/profile-picture", response_model=MentorProfileOut)
def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(require_mentor),
    db: Session = Depends(get_db),
):
    validate_upload(file)
    key, _ = safe_file_key(file.filename, folder="profile-pictures")
    url = get_storage_backend().upload(file.file, key, file.content_type)

    current_user.profile_picture_url = url
    db.add(current_user)
    db.commit()

    profile = MentorService(db).get_own_profile(current_user.id)
    return _to_out(profile)


@router.get("/{mentor_id}", response_model=PublicMentorProfileOut)
def get_public_profile(mentor_id: str, db: Session = Depends(get_db)):
    profile = MentorService(db).get_public_profile(mentor_id)
    return PublicMentorProfileOut(
        id=profile.id,
        full_name=profile.user.full_name,
        profile_picture_url=profile.user.profile_picture_url,
        university_id=profile.university_id,
        faculty_id=profile.faculty_id,
        degree_id=profile.degree_id,
        academic_year=profile.academic_year,
        biography=profile.biography,
        skills=profile.skills,
        achievements=profile.achievements,
        helpful_score=profile.helpful_score,
        completed_session_count=profile.completed_session_count,
        average_rating=profile.average_rating,
        is_verified=True,
    )


def _to_out(profile) -> MentorProfileOut:
    return MentorProfileOut(
        id=profile.id,
        user_id=profile.user_id,
        university_id=profile.university_id,
        faculty_id=profile.faculty_id,
        department_id=profile.department_id,
        degree_id=profile.degree_id,
        academic_year=profile.academic_year,
        biography=profile.biography,
        skills=profile.skills,
        achievements=profile.achievements,
        verification_status=profile.verification_status.value,
        is_publicly_visible=profile.is_publicly_visible,
        helpful_score=profile.helpful_score,
        completed_session_count=profile.completed_session_count,
        average_rating=profile.average_rating,
        profile_completion_percentage=profile.profile_completion_percentage,
    )


@router.get("/me/dashboard", response_model=MentorDashboardOut)
def mentor_dashboard(current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    return MentorService(db).dashboard_summary(current_user.id)


@router.get("/me/earnings", response_model=MentorEarningsSummaryOut)
def mentor_earnings(current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    return MentorService(db).earnings_summary(current_user.id)
