from fastapi import APIRouter, HTTPException
import httpx
from app.services.tink_service import TinkService
from app.services.tenant_service import TenantService
from app.core.config import settings

router = APIRouter(prefix="/tink", tags=["tink"])
tink_service = TinkService()
tenant_service = TenantService()


@router.post("/setup/{tenant_id}")
async def setup_tink_for_tenant(tenant_id: str):
    """
    Step 1: Create Tink user and generate Link URL.
    Returns URL for user to connect their bank.
    """
    tenant = tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    try:
        # Check if Tink user already exists
        tink_user_id = tenant.get("tink_user_id")

        # Create Tink user if doesn't exist
        if not tink_user_id:
            print(f"Creating Tink user for tenant {tenant_id}")
            tink_user = await tink_service.create_tink_user(
                external_user_id=tenant_id, market="SE"
            )

            if not tink_user:
                print("User creation failed, might already exist")
                # User already exists in Tink, continue anyway
            else:
                tink_user_id = tink_user["user_id"]
                print(f"Tink user created: {tink_user_id}")

                # Save tink_user_id to tenant (optional - we use tenant_id as external_user_id)
                conn = tenant_service._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE tenants SET tink_user_id = %s WHERE tenant_id = %s",
                    (tink_user_id, tenant_id),
                )
                conn.commit()
                cursor.close()
                conn.close()
        else:
            print(f"Using existing Tink user: {tink_user_id}")

        # Generate authorization code using tenant_id as external_user_id
        print("Generating authorization code")
        auth_code = await tink_service.generate_authorization_code(
            external_user_id=tenant_id, id_hint=tenant["email"]
        )

        if not auth_code:
            raise HTTPException(status_code=500, detail="Failed to generate auth code")

        print(f"Authorization code generated successfully")

        # Build Tink Link URL
        redirect_uri = f"{settings.frontend_url}/onboarding/tink-complete"
        tink_link_url = tink_service.build_tink_link_url(
            authorization_code=auth_code, redirect_uri=redirect_uri, market="SE"
        )

        return {
            "tink_link_url": tink_link_url,
            "message": "Redirect user to tink_link_url to connect bank",
        }

    except Exception as e:
        print(f"Error setting up Tink: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def tink_callback(credentials_id: str, state: str = None):
    """
    Step 2: Handle callback after user connects bank via Tink Link.
    Tink redirects here with credentials_id.
    """
    print(f"Tink callback received: credentials_id={credentials_id}, state={state}")

    # credentials_id confirms successful bank connection
    # State can be used to identify the tenant if needed

    return {
        "status": "success",
        "credentials_id": credentials_id,
        "message": "Bank connection successful. Data will sync within 24 hours.",
    }


@router.post("/activate/{tenant_id}")
async def activate_tink_connector(tenant_id: str):
    """
    Step 3: Switch Tink connector from MOCK to real mode.
    Called after user completes bank connection.
    """
    tenant = tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    connector_id = tenant.get("tink_connector_id")
    if not connector_id:
        raise HTTPException(status_code=404, detail="No Tink connector found")

    try:
        print(f"Activating Tink connector {connector_id} for tenant {tenant_id}")

        # Update connector configuration using PATCH /connectors/{id}
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"https://api.fivetran.com/v1/connectors/{connector_id}",
                headers={
                    "Authorization": f"Basic {settings.fivetran_auth_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json;version=2",
                },
                json={
                    "config": {
                        "tink_user_id": tenant_id  # Update config to use real tenant_id
                    }
                },
            )

            print(f"Update config response: {response.status_code}")
            print(f"Update config body: {response.text}")

            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update connector: {response.text}",
                )

            # Trigger immediate sync
            print(f"Triggering sync for connector {connector_id}")
            sync_response = await client.post(
                f"https://api.fivetran.com/v1/connectors/{connector_id}/sync",
                headers={
                    "Authorization": f"Basic {settings.fivetran_auth_token}",
                    "Content-Type": "application/json",
                },
            )

            print(f"Sync trigger response: {sync_response.status_code}")

            return {
                "status": "activated",
                "connector_id": connector_id,
                "message": "Tink connector updated. Real banking data will sync shortly.",
            }

    except Exception as e:
        print(f"Error activating connector: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{tenant_id}")
async def get_tink_status(tenant_id: str):
    """
    Get Tink connector sync status for tenant.
    """
    tenant = tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    connector_id = tenant.get("tink_connector_id")
    if not connector_id:
        raise HTTPException(status_code=404, detail="No Tink connector found")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.fivetran.com/v1/connectors/{connector_id}",
                headers={
                    "Authorization": f"Basic {settings.fivetran_auth_token}",
                    "Accept": "application/json;version=2",
                },
            )

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to get status")

            data = response.json()["data"]

            return {
                "connector_id": connector_id,
                "setup_state": data["status"]["setup_state"],
                "sync_state": data["status"]["sync_state"],
                "succeeded_at": data.get("succeeded_at"),
                "failed_at": data.get("failed_at"),
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
