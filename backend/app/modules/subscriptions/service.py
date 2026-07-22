from datetime import datetime, timedelta, timezone
from app.core.datetime_utils import utcnow

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.subscriptions.models import SubscriptionPlanCode, SubscriptionStatus, UserSubscription
from app.modules.subscriptions.repository import SubscriptionRepository


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SubscriptionRepository(db)

    def list_plans(self):
        return self.repo.list_plans()

    def get_current_plan(self, user_id: str) -> UserSubscription:
        current = self.repo.get_current(user_id)
        if not current:
            free_plan = self.repo.get_plan_by_code(SubscriptionPlanCode.FREE)
            if not free_plan:
                raise NotFoundError("No subscription plans configured. Run the seed script.")
            current = UserSubscription(
                user_id=user_id,
                plan_id=free_plan.id,
                status=SubscriptionStatus.ACTIVE,
                started_at=utcnow(),
            )
            self.repo.create(current)
            self.repo.commit()
        return current

    def upgrade_plan(self, user_id: str, plan_code: SubscriptionPlanCode) -> UserSubscription:
        plan = self.repo.get_plan_by_code(plan_code)
        if not plan:
            raise BadRequestError(f"Unknown plan: {plan_code}")

        existing = self.repo.get_current(user_id)
        if existing:
            existing.status = SubscriptionStatus.CANCELLED
            existing.cancelled_at = utcnow()
            self.db.add(existing)

        new_sub = UserSubscription(
            user_id=user_id,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE,
            started_at=utcnow(),
            expires_at=utcnow() + timedelta(days=30) if plan_code != SubscriptionPlanCode.FREE else None,
        )
        self.repo.create(new_sub)
        self.repo.commit()
        return new_sub

    def cancel_subscription(self, user_id: str) -> UserSubscription:
        current = self.repo.get_current(user_id)
        if not current:
            raise NotFoundError("No active subscription found.")
        current.status = SubscriptionStatus.CANCELLED
        current.cancelled_at = utcnow()
        self.db.add(current)
        self.repo.commit()
        return current

    def history(self, user_id: str):
        return self.repo.list_history(user_id)
