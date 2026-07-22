from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.modules.subscriptions.models import SubscriptionPlanCode, SubscriptionStatus


class SubscriptionPlanOut(BaseModel):
    id: str
    code: SubscriptionPlanCode
    name: str
    price_monthly: float
    free_chat_limit: int
    can_access_premium_resources: bool

    model_config = {"from_attributes": True}


class UpgradePlanRequest(BaseModel):
    plan_code: SubscriptionPlanCode


class UserSubscriptionOut(BaseModel):
    id: str
    plan: SubscriptionPlanOut
    status: SubscriptionStatus
    started_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
