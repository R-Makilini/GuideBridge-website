from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import require_any_authenticated
from app.database.session import get_db
from app.modules.subscriptions.schemas import SubscriptionPlanOut, UpgradePlanRequest, UserSubscriptionOut
from app.modules.subscriptions.service import SubscriptionService
from app.modules.users.models import User

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/plans", response_model=list[SubscriptionPlanOut])
def list_plans(db: Session = Depends(get_db)):
    return SubscriptionService(db).list_plans()


@router.get("/me", response_model=UserSubscriptionOut)
def my_subscription(current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    return SubscriptionService(db).get_current_plan(current_user.id)


@router.post("/upgrade", response_model=UserSubscriptionOut)
def upgrade(payload: UpgradePlanRequest, current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    return SubscriptionService(db).upgrade_plan(current_user.id, payload.plan_code)


@router.post("/cancel", response_model=UserSubscriptionOut)
def cancel(current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    return SubscriptionService(db).cancel_subscription(current_user.id)


@router.get("/history", response_model=list[UserSubscriptionOut])
def history(current_user: User = Depends(require_any_authenticated), db: Session = Depends(get_db)):
    return SubscriptionService(db).history(current_user.id)
