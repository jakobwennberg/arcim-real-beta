from fivetran_connector_sdk import Connector
from fivetran_connector_sdk import Operations as op
from fivetran_connector_sdk import Logging as log
import requests
from datetime import datetime, timedelta


def schema(configuration: dict):
    """
    Define tables for Tink banking data.
    Schema matches Tink API response structure.
    """
    return [
        {
            "table": "accounts",
            "primary_key": ["id"],
            "columns": {
                "id": "STRING",
                "tenant_id": "STRING",
                "financial_institution_id": "STRING",
                "name": "STRING",
                "type": "STRING",
                "balance_amount": {"type": "DECIMAL", "precision": 18, "scale": 2},
                "balance_currency": "STRING",
                "iban": "STRING",
                "last_refreshed": "STRING",
            },
        },
        {
            "table": "transactions",
            "primary_key": ["id"],
            "columns": {
                "id": "STRING",
                "tenant_id": "STRING",
                "account_id": "STRING",
                "amount": {"type": "DECIMAL", "precision": 18, "scale": 2},
                "currency": "STRING",
                "booked_date": "NAIVE_DATE",
                "value_date": "NAIVE_DATE",
                "description": "STRING",
                "merchant_name": "STRING",
                "status": "STRING",
                "type": "STRING",
            },
        },
    ]


def update(configuration: dict, state: dict):
    """
    Fetch transactions from Tink API.

    Configuration keys:
    - tink_client_id: Tink client ID
    - tink_client_secret: Tink client secret
    - tenant_id: Arcim tenant ID
    - tink_user_id: Tink user ID (use "MOCK" for testing)
    """

    tenant_id = configuration["tenant_id"]
    tink_user_id = configuration.get("tink_user_id")

    log.info(f"Starting sync for tenant {tenant_id}")

    # === MOCK MODE for testing ===
    if tink_user_id == "MOCK":
        log.info("Running in MOCK mode")

        # Mock account
        op.upsert(
            table="accounts",
            data={
                "id": "mock_account_1",
                "tenant_id": tenant_id,
                "financial_institution_id": "swedbank",
                "name": "Business Checking",
                "type": "CHECKING",
                "balance_amount": "150000.50",
                "balance_currency": "SEK",
                "iban": "SE1234567890123456",
                "last_refreshed": datetime.utcnow().isoformat(),
            },
        )

        # Mock transactions
        base_date = datetime.utcnow()
        for i in range(10):
            op.upsert(
                table="transactions",
                data={
                    "id": f"mock_txn_{i}",
                    "tenant_id": tenant_id,
                    "account_id": "mock_account_1",
                    "amount": str(-1500.00 - (i * 100)),
                    "currency": "SEK",
                    "booked_date": (base_date - timedelta(days=i)).strftime("%Y-%m-%d"),
                    "value_date": (base_date - timedelta(days=i)).strftime("%Y-%m-%d"),
                    "description": f"Payment to supplier {i}",
                    "merchant_name": f"Supplier AB {i}",
                    "status": "BOOKED",
                    "type": "DEFAULT",
                },
            )

        op.checkpoint(state={"last_sync_date": datetime.utcnow().strftime("%Y-%m-%d")})
        log.info("Mock sync complete: 1 account, 10 transactions")
        return
    # === END MOCK MODE ===

    # Get Tink access token
    access_token = get_user_access_token(
        configuration["tink_client_id"],
        configuration["tink_client_secret"],
        tink_user_id,
    )

    if not access_token:
        log.severe("Failed to get Tink access token")
        return

    # Fetch accounts
    log.info("Fetching accounts")
    accounts = fetch_accounts(access_token)

    for account in accounts:
        op.upsert(
            table="accounts",
            data={
                "id": account["id"],
                "tenant_id": tenant_id,
                "financial_institution_id": account.get("financialInstitutionId"),
                "name": account.get("name"),
                "type": account.get("type"),
                "balance_amount": account.get("balances", {})
                .get("booked", {})
                .get("amount", {})
                .get("value", {})
                .get("unscaledValue"),
                "balance_currency": account.get("balances", {})
                .get("booked", {})
                .get("amount", {})
                .get("currencyCode"),
                "iban": account.get("identifiers", {}).get("iban", {}).get("iban"),
                "last_refreshed": account.get("dates", {}).get("lastRefreshed"),
            },
        )

    log.info(f"Upserted {len(accounts)} accounts")

    # Fetch transactions for each account
    last_sync = state.get("last_sync_date")

    if not last_sync:
        # First sync - get last 90 days
        last_sync = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")
        log.info(f"Initial sync from {last_sync}")

    total_transactions = 0

    for account in accounts:
        account_id = account["id"]
        log.info(f"Fetching transactions for account {account_id}")

        transactions = fetch_transactions(
            access_token=access_token, account_id=account_id, booked_date_gte=last_sync
        )

        for txn in transactions:
            op.upsert(
                table="transactions",
                data={
                    "id": txn["id"],
                    "tenant_id": tenant_id,
                    "account_id": account_id,
                    "amount": txn.get("amount", {})
                    .get("value", {})
                    .get("unscaledValue"),
                    "currency": txn.get("amount", {}).get("currencyCode"),
                    "booked_date": txn.get("dates", {}).get("booked"),
                    "value_date": txn.get("dates", {}).get("value"),
                    "description": txn.get("descriptions", {}).get("display"),
                    "merchant_name": txn.get("merchantInformation", {}).get(
                        "merchantName"
                    ),
                    "status": txn.get("status"),
                    "type": txn.get("types", {}).get("type"),
                },
            )

        total_transactions += len(transactions)
        log.info(f"Upserted {len(transactions)} transactions for account {account_id}")

    # Update state
    new_state = {"last_sync_date": datetime.utcnow().strftime("%Y-%m-%d")}

    op.checkpoint(state=new_state)

    log.info(
        f"Sync complete: {len(accounts)} accounts, {total_transactions} transactions"
    )


def get_user_access_token(client_id: str, client_secret: str, user_id: str) -> str:
    """
    Get user access token from Tink.
    Implements authorization flow from Tink docs.
    """
    # Step 1: Get client access token
    response = requests.post(
        "https://api.tink.com/api/v1/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": "authorization:grant",
        },
    )

    if response.status_code != 200:
        log.severe(f"Failed to get client token: {response.text}")
        return None

    client_token = response.json()["access_token"]

    # Step 2: Generate authorization code for user
    response = requests.post(
        "https://api.tink.com/api/v1/oauth/authorization-grant",
        headers={"Authorization": f"Bearer {client_token}"},
        data={
            "user_id": user_id,
            "scope": "accounts:read,balances:read,transactions:read",
        },
    )

    if response.status_code != 200:
        log.severe(f"Failed to get auth code: {response.text}")
        return None

    auth_code = response.json()["code"]

    # Step 3: Exchange code for user access token
    response = requests.post(
        "https://api.tink.com/api/v1/oauth/token",
        data={
            "code": auth_code,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
        },
    )

    if response.status_code != 200:
        log.severe(f"Failed to get user token: {response.text}")
        return None

    return response.json()["access_token"]


def fetch_accounts(access_token: str) -> list:
    """Fetch accounts from Tink API."""
    response = requests.get(
        "https://api.tink.com/data/v2/accounts",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if response.status_code != 200:
        log.severe(f"Failed to fetch accounts: {response.text}")
        return []

    return response.json().get("accounts", [])


def fetch_transactions(
    access_token: str, account_id: str, booked_date_gte: str
) -> list:
    """Fetch transactions from Tink API with pagination."""
    all_transactions = []
    page_token = None

    while True:
        params = {
            "accountIdIn": account_id,
            "bookedDateGte": booked_date_gte,
            "pageSize": 100,
        }

        if page_token:
            params["pageToken"] = page_token

        response = requests.get(
            "https://api.tink.com/data/v2/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )

        if response.status_code != 200:
            log.warning(f"Failed to fetch transactions: {response.text}")
            break

        data = response.json()
        transactions = data.get("transactions", [])
        all_transactions.extend(transactions)

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return all_transactions


# Initialize connector
connector = Connector(update=update, schema=schema)

if __name__ == "__main__":
    connector.debug()
