import httpx
import asyncio
from app.core.config import settings


async def test_webhook():
    # Get webhook_id from Fivetran group
    # You need to list webhooks first or get it from creation response

    auth_token = settings.fivetran_auth_token

    # First, list webhooks to get webhook_id
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.fivetran.com/v1/webhooks",
            headers={
                "Authorization": f"Basic {auth_token}",
                "Accept": "application/json",
            },
        )
        print("Webhooks:")
        print(response.json())

        # Copy webhook_id from output, then test it:
        webhook_id = "your_webhook_id_here"

        test_response = await client.post(
            f"https://api.fivetran.com/v1/webhooks/{webhook_id}/test",
            headers={
                "Authorization": f"Basic {auth_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={"event": "sync_end"},
        )
        print("\nTest webhook response:")
        print(test_response.json())


asyncio.run(test_webhook())
