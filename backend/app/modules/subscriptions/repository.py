from sqlalchemy.orm import Session

from app.modules.subscriptions.models import SubscriptionPlan, SubscriptionPlanCode, UserSubscription


class SubscriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_plan_by_code(self, code: SubscriptionPlanCode) -> SubscriptionPlan | None:
        return self.db.query(SubscriptionPlan).filter(SubscriptionPlan.code == code).first()

    def list_plans(self):
        return self.db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active.is_(True)).all()

    def get_current(self, user_id: str) -> UserSubscription | None:
        from app.modules.subscriptions.models import SubscriptionStatus

        return (
            self.db.query(UserSubscription)
            .filter(UserSubscription.user_id == user_id, UserSubscription.status == SubscriptionStatus.ACTIVE)
            .order_by(UserSubscription.created_at.desc())
            .first()
        )

    def list_history(self, user_id: str):
        return (
            self.db.query(UserSubscription)
            .filter(UserSubscription.user_id == user_id)
            .order_by(UserSubscription.created_at.desc())
            .all()
        )

    def create(self, sub: UserSubscription) -> UserSubscription:
        self.db.add(sub)
        self.db.flush()
        return sub

    def commit(self):
        self.db.commit()
