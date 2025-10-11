import httpx
from typing import Optional
from app.core.config import settings


class TinkService:
    def __init__(self):
        self.base_url = "https://api.tink.com/api/v1"
        self.client_id = settings.tink_client_id
        self.client_secret = settings.tink_client_secret

    async def get_client_access_token(
        self, scope: str = "user:create"
    ) -> Optional[str]:
        """Get client access token for backend operations."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                    "scope": scope,
                },
            )

            if response.status_code != 200:
                print(f"Failed to get client token: {response.text}")
                return None

            return response.json()["access_token"]

    async def create_tink_user(
        self, external_user_id: str, market: str = "SE"
    ) -> Optional[dict]:
        """
        Create Tink user for tenant.
        external_user_id should be tenant_id.
        """
        print(f"Getting client token for user creation...")
        token = await self.get_client_access_token(scope="user:create")
        if not token:
            print("Failed to get client token")
            return None

        print(f"Client token obtained: {token[:20]}...")

        async with httpx.AsyncClient() as client:
            payload = {
                "external_user_id": external_user_id,
                "market": market,
                "locale": "en_US",
            }
            print(f"Creating Tink user with payload: {payload}")

            response = await client.post(
                f"{self.base_url}/user/create",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            print(f"Create user response status: {response.status_code}")
            print(f"Create user response body: {response.text}")

            if response.status_code != 200:
                print(f"Failed to create user: {response.text}")
                return None

            return response.json()

    async def generate_authorization_code(
        self,
        external_user_id: str,
        id_hint: str = None,
        scope: str = "authorization:read,authorization:grant,credentials:refresh,credentials:read,credentials:write,providers:read,user:read",
    ) -> Optional[str]:
        """Generate authorization code for user to access Tink Link."""
        token = await self.get_client_access_token(scope="authorization:grant")
        if not token:
            print("Failed to get client token for auth grant")
            return None

        # id_hint is typically the user's email or username
        if not id_hint:
            id_hint = external_user_id  # Fallback to user_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/authorization-grant/delegate",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "response_type": "code",
                    "actor_client_id": "df05e4b379934cd09963197cc855bfe9",
                    "external_user_id": external_user_id,
                    "id_hint": id_hint,
                    "scope": scope,
                },
            )

            print(f"Auth code response status: {response.status_code}")
            print(f"Auth code response body: {response.text}")

            if response.status_code != 200:
                print(f"Failed to get auth code: {response.text}")
                return None

            return response.json()["code"]

    def build_tink_link_url(
        self, authorization_code: str, redirect_uri: str, market: str = "SE"
    ) -> str:
        """Build Tink Link URL for user to connect bank."""
        return (
            f"https://link.tink.com/1.0/business-transactions/connect-accounts"
            f"?client_id={self.client_id}"
            f"&authorization_code={authorization_code}"
            f"&redirect_uri={redirect_uri}"
            f"&market={market}"
        )
