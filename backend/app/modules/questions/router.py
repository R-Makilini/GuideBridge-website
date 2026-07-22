from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.file_validation import safe_file_key, validate_upload
from app.core.pagination import PaginatedResponse
from app.core.permissions import require_any_authenticated, require_mentor, require_student
from app.database.session import get_db
from app.integrations.storage import get_storage_backend
from app.modules.questions.models import QuestionAttachment
from app.modules.questions.schemas import AnswerCreate, AnswerOut, AnswerUpdate, QuestionCreate, QuestionOut, QuestionUpdate
from app.modules.questions.service import QuestionService
from app.modules.users.models import User

router = APIRouter(prefix="/questions", tags=["Questions & Answers"])


@router.post("", response_model=QuestionOut, status_code=201)
def create_question(payload: QuestionCreate, current_user: User = Depends(require_student), db: Session = Depends(get_db)):
    return QuestionService(db).create_question(current_user.id, payload)


@router.put("/{question_id}", response_model=QuestionOut)
def update_question(question_id: str, payload: QuestionUpdate, current_user: User = Depends(require_student), db: Session = Depends(get_db)):
    return QuestionService(db).update_question(current_user.id, question_id, payload)


@router.delete("/{question_id}", status_code=204)
def delete_question(question_id: str, current_user: User = Depends(require_student), db: Session = Depends(get_db)):
    QuestionService(db).delete_question(current_user.id, question_id)


@router.get("/feed", response_model=PaginatedResponse[QuestionOut])
def question_feed(
    subject_id: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, meta = QuestionService(db).feed(page, page_size, subject_id, search)
    return PaginatedResponse(items=items, meta=meta)


@router.get("/trending", response_model=list[QuestionOut])
def trending_questions(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    return QuestionService(db).trending(limit)


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(question_id: str, db: Session = Depends(get_db)):
    return QuestionService(db).get_question_detail(question_id)


@router.post("/{question_id}/attachments", status_code=201)
def upload_attachment(
    question_id: str, file: UploadFile = File(...), current_user: User = Depends(require_student), db: Session = Depends(get_db)
):
    validate_upload(file)
    key, safe_name = safe_file_key(file.filename, folder=f"questions/{question_id}")
    url = get_storage_backend().upload(file.file, key, file.content_type)
    attachment = QuestionAttachment(question_id=question_id, file_url=url, file_name=safe_name, mime_type=file.content_type)
    db.add(attachment)
    db.commit()
    return {"file_url": url, "file_name": safe_name}


@router.post("/{question_id}/answers", response_model=AnswerOut, status_code=201)
def create_answer(question_id: str, payload: AnswerCreate, current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    return QuestionService(db).create_answer(current_user.id, question_id, payload)


@router.put("/answers/{answer_id}", response_model=AnswerOut)
def update_answer(answer_id: str, payload: AnswerUpdate, current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    return QuestionService(db).update_answer(current_user.id, answer_id, payload)


@router.delete("/answers/{answer_id}", status_code=204)
def delete_answer(answer_id: str, current_user: User = Depends(require_mentor), db: Session = Depends(get_db)):
    QuestionService(db).delete_answer(current_user.id, answer_id)


@router.post("/answers/{answer_id}/helpful", response_model=AnswerOut)
def vote_helpful(answer_id: str, current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    return QuestionService(db).vote_helpful(current_user.id, answer_id)
