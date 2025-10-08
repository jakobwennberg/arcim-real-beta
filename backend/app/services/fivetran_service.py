import httpx
from typing import Optional, Dict
from app.core.config import settings


class FivetranService:
    def __init__(self):
        self.base_url = "https://api.fivetran.com/v1"
        self.auth_token = settings.fivetran_auth_token

    def _get_headers(self):
        return {
            "Authorization": f"Basic {self.auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json;version=2",
        }

    async def create_group(self, tenant_id: str, company_name: str) -> dict:
        """
        Creates Fivetran group for tenant.
        One group per tenant allows isolated management.
        """
        async with httpx.AsyncClient() as client:
            payload = {"name": f"{company_name}_{tenant_id[:8]}"}

            print(f"Creating group with payload: {payload}")

            response = await client.post(
                f"{self.base_url}/groups", headers=self._get_headers(), json=payload
            )

            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")

            response.raise_for_status()
            return response.json()["data"]

    async def create_snowflake_destination(self, group_id: str, tenant_id: str) -> dict:
        """
        Creates Snowflake destination for group.
        Uses key-pair authentication with tenant-specific role.
        """

        # Read private key file
        with open(settings.snowflake_private_key_path, "r") as key_file:
            private_key_content = key_file.read()

        tenant_role = f"TENANT_{tenant_id.replace('-', '_').upper()}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/destinations",
                headers=self._get_headers(),
                json={
                    "group_id": group_id,
                    "service": "snowflake",
                    "time_zone_offset": "+1",
                    "run_setup_tests": False,
                    "config": {
                        "host": f"{settings.snowflake_account}.snowflakecomputing.com",
                        "port": 443,
                        "database": settings.snowflake_database,
                        "auth": "KEY_PAIR",
                        "user": settings.snowflake_user,
                        "private_key": private_key_content,
                        "role": tenant_role,
                    },
                },
            )

            print(f"Destination response status: {response.status_code}")
            print(f"Destination response body: {response.text}")

            response.raise_for_status()
            return response.json()["data"]

    async def create_fortnox_connector(
        self, group_id: str, tenant_id: str, redirect_uri: str = None
    ) -> dict:
        """
        Creates Fortnox connector with Connect Card.
        User completes OAuth flow in Connect Card with pre-configured app credentials.

        Schema name format: fortnox_<tenant_short_id>
        This ensures unique schema per tenant in shared Snowflake destination.
        """
        if not redirect_uri:
            redirect_uri = f"{settings.frontend_url}/onboarding/connection-complete"

        # Schema name must be unique and permanent
        schema_name = f"fortnox_{tenant_id.replace('-', '_')[:8]}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/connectors",
                headers=self._get_headers(),
                json={
                    "group_id": group_id,
                    "service": "fortnox",
                    "trust_certificates": True,
                    "trust_fingerprints": True,
                    "run_setup_tests": False,
                    "paused": False,
                    "sync_frequency": 1440,
                    "schedule_type": "auto",
                    "connect_card_config": {
                        "redirect_uri": redirect_uri,
                        "hide_setup_guide": False,
                    },
                    "config": {
                        "schema": schema_name,
                        "client_id": settings.fortnox_client_id,
                        "client_secret": settings.fortnox_client_secret,
                        "scopes": settings.fortnox_scopes,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()["data"]
            return data

    async def get_connector_status(self, connector_id: str) -> dict:
        """Get connector sync status."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/connectors/{connector_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()["data"]

    async def list_group_connectors(self, group_id: str) -> list:
        """List all connectors in a group."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/groups/{group_id}/connectors",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()["data"]["items"]

    async def create_group_webhook(
        self, group_id: str, webhook_url: str, secret: str
    ) -> dict:
        """
        Creates webhook for Fivetran group to receive sync notifications.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/webhooks/group/{group_id}",
                headers=self._get_headers(),
                json={
                    "url": webhook_url,
                    "events": ["sync_start", "sync_end"],
                    "active": True,
                    "secret": secret,
                },
            )

            print(f"Webhook response status: {response.status_code}")
            print(f"Webhook response body: {response.text}")

            response.raise_for_status()
            return response.json()["data"]
