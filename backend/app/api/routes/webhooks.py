from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import json
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
tenant_service = TenantService()


@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    svix_id: Optional[str] = Header(None),
    svix_timestamp: Optional[str] = Header(None),
    svix_signature: Optional[str] = Header(None),
):
    """
    Receives Clerk webhook events.
    Creates tenant on user.created event.
    """
    # Get raw body
    body = await request.body()

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Extract event type
    event_type = payload.get("type")

    # Handle user.created event
    if event_type == "user.created":
        data = payload.get("data", {})

        clerk_user_id = data.get("id")
        email_addresses = data.get("email_addresses", [])

        # Get primary email
        primary_email = None
        for email_obj in email_addresses:
            if email_obj.get("id") == data.get("primary_email_address_id"):
                primary_email = email_obj.get("email_address")
                break

        if not clerk_user_id or not primary_email:
            raise HTTPException(status_code=400, detail="Missing user ID or email")

        # Check if tenant already exists
        existing = tenant_service.get_tenant_by_clerk_id(clerk_user_id)
        if existing:
            return {
                "message": "Tenant already exists",
                "tenant_id": existing["tenant_id"],
            }

        # Create tenant
        tenant = tenant_service.create_tenant(
            company_name=None, clerk_user_id=clerk_user_id, email=primary_email
        )

        return {
            "message": "Tenant created",
            "tenant_id": tenant["tenant_id"],
            "event_type": event_type,
        }

    # Ignore other event types
    return {"message": "Event received", "event_type": event_type}
