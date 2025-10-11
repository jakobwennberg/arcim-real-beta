# backend/get_tink_user.py
import asyncio
import httpx
from app.core.config import settings


async def get_user():
    # Get client token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.tink.com/api/v1/oauth/token",
            data={
                "client_id": settings.tink_client_id,
                "client_secret": settings.tink_client_secret,
                "grant_type": "client_credentials",
                "scope": "user:read",
            },
        )
        print(f"Token response: {response.status_code}")
        token = response.json()["access_token"]
        print(f"Got token: {token[:20]}...")

        # List users - note: this endpoint might not exist
        # Try getting user by external_user_id instead
        tenant_id = "0973369a-5994-4878-8d0d-04d87bc630ff"

        # According to Tink docs, we need to use the external_user_id to construct user_id
        # For Tink, when you create a user with external_user_id, that becomes their user_id
        print(f"\nTink user_id is typically the external_user_id you provided")
        print(f"Try using: {tenant_id}")


asyncio.run(get_user())
