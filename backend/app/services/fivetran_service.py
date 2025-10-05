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
            response = await client.post(
                f"{self.base_url}/groups",
                headers=self._get_headers(),
                json={"name": f"{company_name}_{tenant_id[:8]}"},
            )
            response.raise_for_status()
            return response.json()["data"]

    async def create_fortnox_connector(
        self, group_id: str, tenant_id: str, redirect_uri: str = None
    ) -> dict:
        """
        Creates Fortnox connector with Connect Card.
        User completes OAuth flow in Connect Card.

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
                    "config": {"schema": schema_name},
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
