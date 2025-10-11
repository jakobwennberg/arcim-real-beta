import asyncio
import httpx
from app.core.config import settings


async def get_user():
    tenant_id = "0973369a-5994-4878-8d0d-04d87bc630ff"

    # Get client token with authorization:grant scope
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.tink.com/api/v1/oauth/token",
            data={
                "client_id": settings.tink_client_id,
                "client_secret": settings.tink_client_secret,
                "grant_type": "client_credentials",
                "scope": "authorization:grant",
            },
        )
        token = response.json()["access_token"]
        print(f"Got token")

        # Try to generate auth code using external_user_id parameter instead
        response = await client.post(
            "https://api.tink.com/api/v1/oauth/authorization-grant/delegate",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "response_type": "code",
                "actor_client_id": "df05e4b379934cd09963197cc855bfe9",
                "external_user_id": tenant_id,  # Use external_user_id instead of user_id
                "id_hint": "test@example.com",
                "scope": "authorization:read,authorization:grant",
            },
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")


asyncio.run(get_user())
