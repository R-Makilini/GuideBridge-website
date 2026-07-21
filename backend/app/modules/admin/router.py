from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.permissions import require_super_admin
from app.database.session import get_db
from app.modules.admin.schemas import (
    AdminDashboardOut,
    AdminUserOut,
    AuditLogOut,
    SystemSettingOut,
    SystemSettingUpdate,
    UserStatusUpdateRequest,
)
from app.modules.admin.service import AdminService
from app.modules.users.models import User

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=AdminDashboardOut)
def dashboard(current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return AdminService(db).dashboard()


@router.get("/students", response_model=list[AdminUserOut])
def list_students(current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return AdminService(db).list_students()


@router.get("/mentors", response_model=list[AdminUserOut])
def list_mentors(current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return AdminService(db).list_mentors()


@router.post("/users/{user_id}/status", response_model=AdminUserOut)
def update_user_status(
    user_id: str, payload: UserStatusUpdateRequest, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)
):
    return AdminService(db).update_user_status(current_user.id, user_id, payload.status, payload.reason)


@router.get("/settings", response_model=list[SystemSettingOut])
def list_settings(current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return AdminService(db).list_settings()


@router.put("/settings", response_model=SystemSettingOut)
def upsert_setting(payload: SystemSettingUpdate, current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return AdminService(db).upsert_setting(payload)


@router.get("/audit-logs", response_model=list[AuditLogOut])
def audit_logs(limit: int = Query(100, ge=1, le=500), current_user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    return AdminService(db).list_audit_logs(limit)
