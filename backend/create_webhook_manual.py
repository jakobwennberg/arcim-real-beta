import httpx
import asyncio


async def create_webhook():
    group_id = "thefe_hallucinations"
    webhook_url = (
        "https://81bd57342d65.ngrok-free.app/api/webhooks/fivetran/sync-status"
    )

    response = await httpx.AsyncClient().post(
        f"https://api.fivetran.com/v1/webhooks/group/{group_id}",
        headers={
            "Authorization": "Basic eWlpdUpoeGxKNGs2MFZyNTpFM0J2V1Y4RktwN0hXTU9HQ2VsenZsUEQ3ZXlsM2N4UA==",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={"url": webhook_url, "events": ["sync_start", "sync_end"], "active": True},
    )

    print(response.status_code)
    print(response.json())


asyncio.run(create_webhook())
