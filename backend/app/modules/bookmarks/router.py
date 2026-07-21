from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import BookmarkTargetType
from app.core.permissions import require_any_authenticated
from app.database.session import get_db
from app.modules.bookmarks.schemas import BookmarkCreate, BookmarkOut
from app.modules.bookmarks.service import BookmarkService
from app.modules.users.models import User

router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])


@router.post("", response_model=BookmarkOut, status_code=201)
def add_bookmark(payload: BookmarkCreate, current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    return BookmarkService(db).add_bookmark(current_user.id, payload)


@router.delete("/{target_type}/{target_id}", status_code=204)
def remove_bookmark(target_type: BookmarkTargetType, target_id: str, current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    BookmarkService(db).remove_bookmark(current_user.id, target_type, target_id)


@router.get("", response_model=list[BookmarkOut])
def list_bookmarks(target_type: BookmarkTargetType | None = Query(None), current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    return BookmarkService(db).list_bookmarks(current_user.id, target_type)
