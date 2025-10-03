from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from app.models.tenant import TenantCreate, TenantResponse
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])
tenant_service = TenantService()


@router.post("/", response_model=TenantResponse)
async def create_tenant(tenant_data: TenantCreate):
    """
    Creates new tenant record.
    Called from Next.js after Clerk sign-up webhook.
    """
    try:
        # Check if tenant already exists
        existing = tenant_service.get_tenant_by_clerk_id(tenant_data.clerk_user_id)
        if existing:
            raise HTTPException(status_code=400, detail="Tenant already exists")

        # Create tenant
        tenant = tenant_service.create_tenant(
            company_name=tenant_data.company_name,
            clerk_user_id=tenant_data.clerk_user_id,
            email=tenant_data.email,
        )

        return tenant

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{clerk_user_id}", response_model=TenantResponse)
async def get_tenant(clerk_user_id: str):
    """
    Retrieves tenant by Clerk user ID.
    Used by frontend to check onboarding state.
    """
    tenant = tenant_service.get_tenant_by_clerk_id(clerk_user_id)

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return tenant


@router.patch("/{tenant_id}/state")
async def update_tenant_state(tenant_id: str, state: str):
    """
    Updates tenant onboarding state.
    States: pending -> connecting -> syncing -> ready
    """
    valid_states = ["pending", "connecting", "syncing", "ready"]
    if state not in valid_states:
        raise HTTPException(
            status_code=400, detail=f"Invalid state. Must be one of {valid_states}"
        )

    tenant = tenant_service.update_onboarding_state(tenant_id, state)

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return tenant
