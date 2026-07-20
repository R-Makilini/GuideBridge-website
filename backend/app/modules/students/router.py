from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.file_validation import safe_file_key, validate_upload
from app.core.permissions import require_student
from app.database.session import get_db
from app.integrations.storage import get_storage_backend
from app.modules.students.schemas import StudentDashboardOut, StudentProfileOut, StudentProfileUpdate
from app.modules.students.service import StudentService
from app.modules.users.models import User

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/me", response_model=StudentProfileOut)
def get_my_profile(current_user: User = Depends(require_student), db: Session = Depends(get_db)):
    return StudentService(db).get_profile(current_user.id)


@router.put("/me", response_model=StudentProfileOut)
def update_my_profile(
    payload: StudentProfileUpdate,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    return StudentService(db).update_profile(current_user.id, payload)


@router.post("/me/profile-picture", response_model=StudentProfileOut)
def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    validate_upload(file)
    key, _ = safe_file_key(file.filename, folder="profile-pictures")
    url = get_storage_backend().upload(file.file, key, file.content_type)

    current_user.profile_picture_url = url
    db.add(current_user)
    db.commit()

    return StudentService(db).get_profile(current_user.id)


@router.get("/me/dashboard", response_model=StudentDashboardOut)
def dashboard(current_user: User = Depends(require_student), db: Session = Depends(get_db)):
    return StudentService(db).dashboard_summary(current_user.id)
