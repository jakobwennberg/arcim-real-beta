from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import json
import hmac
import hashlib
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/webhooks/fivetran", tags=["fivetran_webhooks"])
tenant_service = TenantService()


@router.post("/sync-status")
async def fivetran_sync_webhook(request: Request):
    """
    Receives Fivetran sync status webhooks.
    Marks tenant data_ready when historical sync completes.
    """
    body = await request.body()

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = payload.get("event")
    data = payload.get("data", {})

    connector_id = data.get("id")
    sync_state = data.get("status", {}).get("sync_state")
    is_historical_sync = data.get("status", {}).get("is_historical_sync")
    succeeded_at = data.get("succeeded_at")

    print(
        f"Fivetran webhook: {event_type}, connector: {connector_id}, sync_state: {sync_state}"
    )

    # Find tenant by connector_id
    # Need to add method to tenant_service
    tenant = tenant_service.get_tenant_by_connector_id(connector_id)

    if not tenant:
        print(f"No tenant found for connector {connector_id}")
        return {"message": "Connector not associated with tenant"}

    # Mark data ready when historical sync completes successfully
    if (
        event_type == "sync_end"
        and sync_state == "scheduled"
        and is_historical_sync == False
        and succeeded_at
    ):
        print(f"Historical sync complete for tenant {tenant['tenant_id']}")
        tenant_service.mark_data_ready(tenant["tenant_id"])

        return {"message": "Tenant data marked ready", "tenant_id": tenant["tenant_id"]}

    return {
        "message": "Webhook received",
        "event": event_type,
        "connector_id": connector_id,
    }
