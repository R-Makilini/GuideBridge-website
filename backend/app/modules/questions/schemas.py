from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.constants import QuestionVisibility


class QuestionCreate(BaseModel):
    title: str
    body: str
    subject_id: Optional[str] = None
    visibility: QuestionVisibility = QuestionVisibility.PUBLIC


class QuestionUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    subject_id: Optional[str] = None


class QuestionOut(BaseModel):
    id: str
    title: str
    body: str
    subject_id: Optional[str] = None
    visibility: QuestionVisibility
    view_count: int
    author_name: str
    created_at: datetime


class AnswerCreate(BaseModel):
    body: str


class AnswerUpdate(BaseModel):
    body: str


class AnswerOut(BaseModel):
    id: str
    question_id: str
    mentor_id: str
    body: str
    helpful_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
