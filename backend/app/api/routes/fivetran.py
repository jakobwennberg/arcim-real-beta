from fastapi import APIRouter, HTTPException
from app.services.fivetran_service import FivetranService
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/fivetran", tags=["fivetran"])
fivetran_service = FivetranService()
tenant_service = TenantService()


@router.post("/setup/{tenant_id}")
async def setup_fivetran_for_tenant(tenant_id: str):
    """
    Creates Fivetran group and Fortnox connector for tenant.
    Returns Connect Card URI for user to complete OAuth.
    """
    # Get tenant
    tenant = tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if not tenant["company_name"]:
        raise HTTPException(
            status_code=400, detail="Company name required before connecting data"
        )

    try:
        # Create Fivetran group (one per tenant)
        group = await fivetran_service.create_group(
            tenant_id=tenant_id, company_name=tenant["company_name"]
        )
        group_id = group["id"]

        # Create Fortnox connector with Connect Card
        connector = await fivetran_service.create_fortnox_connector(
            group_id=group_id, tenant_id=tenant_id
        )

        connector_id = connector["id"]
        connect_card_uri = connector["connect_card"]["uri"]

        # Store Fivetran IDs in tenant record
        tenant_service.update_fivetran_ids(tenant_id, group_id, connector_id)

        # Update onboarding state
        tenant_service.update_onboarding_state(tenant_id, "connecting")

        return {
            "group_id": group_id,
            "connector_id": connector_id,
            "connect_card_uri": connect_card_uri,
            "service": "fortnox",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fivetran setup failed: {str(e)}")


@router.get("/status/{tenant_id}")
async def get_tenant_connector_status(tenant_id: str):
    """
    Get sync status for tenant's Fortnox connector.
    """
    tenant = tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    connector_id = tenant.get("fivetran_connector_id")
    if not connector_id:
        raise HTTPException(status_code=404, detail="No connector found for tenant")

    try:
        status = await fivetran_service.get_connector_status(connector_id)
        return {
            "connector_id": connector_id,
            "setup_state": status["status"]["setup_state"],
            "sync_state": status["status"]["sync_state"],
            "is_historical_sync": status["status"]["is_historical_sync"],
            "succeeded_at": status.get("succeeded_at"),
            "failed_at": status.get("failed_at"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
