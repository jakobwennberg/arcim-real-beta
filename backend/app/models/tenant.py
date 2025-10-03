from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TenantCreate(BaseModel):
    company_name: Optional[str] = None
    clerk_user_id: str
    email: str


class TenantResponse(BaseModel):
    tenant_id: str
    company_name: Optional[str] = None
    clerk_user_id: str
    email: str
    snowflake_role: str
    onboarding_state: str
    created_at: datetime
    data_ready: bool


class OnboardingState(BaseModel):
    tenant_id: str
    state: str  # "pending", "connecting", "syncing", "ready"
    updated_at: datetime
