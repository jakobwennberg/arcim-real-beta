from fastapi import APIRouter, HTTPException
from app.services.snowflake_service import SnowflakeService
from app.services.tenant_service import TenantService
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import snowflake.connector
from datetime import datetime, timedelta

router = APIRouter(prefix="/metrics", tags=["metrics"])
tenant_service = TenantService()
snowflake_service = SnowflakeService()


def get_tenant_connection(tenant_id: str):
    """Get Snowflake connection as tenant role."""
    tenant = tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    with open(snowflake_service.private_key_path, "rb") as key_file:
        p_key = serialization.load_pem_private_key(
            key_file.read(), password=None, backend=default_backend()
        )

    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return snowflake.connector.connect(
        user=snowflake_service.user,
        account=snowflake_service.account,
        private_key=pkb,
        role=tenant["snowflake_role"],
        warehouse=snowflake_service.warehouse,
        database=snowflake_service.database,
    )


@router.get("/{tenant_id}/cash-position")
async def get_cash_position(tenant_id: str):
    """Get total cash across all bank accounts."""
    conn = get_tenant_connection(tenant_id)
    cursor = conn.cursor()

    try:
        tenant_short_id = tenant_id.replace("-", "_")[:8].upper()

        cursor.execute(f"""
            SELECT 
                SUM(balance_amount) as total_balance,
                balance_currency,
                COUNT(*) as account_count
            FROM ARCIMS_PROD.TINK_{tenant_short_id}.ACCOUNTS
            GROUP BY balance_currency
        """)

        results = cursor.fetchall()

        if not results:
            return {"total": 0, "currency": "SEK", "accounts": 0}

        return {
            "total": float(results[0][0]) if results[0][0] else 0,
            "currency": results[0][1],
            "accounts": results[0][2],
        }
    finally:
        cursor.close()
        conn.close()


@router.get("/{tenant_id}/burn-rate")
async def get_burn_rate(tenant_id: str):
    """Calculate average monthly burn rate (last 3 months)."""
    conn = get_tenant_connection(tenant_id)
    cursor = conn.cursor()

    try:
        tenant_short_id = tenant_id.replace("-", "_")[:8].upper()

        # Get last 3 months of spending
        cursor.execute(f"""
            SELECT 
                DATE_TRUNC('month', booked_date) as month,
                SUM(ABS(amount)) as monthly_spend
            FROM ARCIMS_PROD.TINK_{tenant_short_id}.TRANSACTIONS
            WHERE amount < 0
              AND booked_date >= DATEADD(month, -3, CURRENT_DATE())
            GROUP BY month
            ORDER BY month DESC
        """)

        results = cursor.fetchall()

        if not results:
            return {"monthly_average": 0, "currency": "SEK", "months_calculated": 0}

        total_spend = sum(row[1] for row in results)
        avg_monthly = total_spend / len(results)

        return {
            "monthly_average": float(avg_monthly),
            "currency": "SEK",
            "months_calculated": len(results),
        }
    finally:
        cursor.close()
        conn.close()


@router.get("/{tenant_id}/runway")
async def get_runway(tenant_id: str):
    """Calculate runway in months (cash / burn rate)."""
    # Get cash position
    cash = await get_cash_position(tenant_id)
    burn = await get_burn_rate(tenant_id)

    if burn["monthly_average"] == 0:
        return {"months": None, "message": "No spending data available"}

    runway_months = cash["total"] / burn["monthly_average"]

    return {
        "months": round(runway_months, 1),
        "cash_position": cash["total"],
        "monthly_burn": burn["monthly_average"],
        "currency": cash["currency"],
    }


@router.get("/{tenant_id}/recent-transactions")
async def get_recent_transactions(tenant_id: str, limit: int = 10):
    """Get most recent transactions."""
    conn = get_tenant_connection(tenant_id)
    cursor = conn.cursor()

    try:
        tenant_short_id = tenant_id.replace("-", "_")[:8].upper()

        cursor.execute(f"""
            SELECT 
                booked_date,
                description,
                amount,
                currency,
                merchant_name,
                status
            FROM ARCIMS_PROD.TINK_{tenant_short_id}.TRANSACTIONS
            ORDER BY booked_date DESC
            LIMIT {limit}
        """)

        results = cursor.fetchall()

        transactions = []
        for row in results:
            transactions.append(
                {
                    "date": row[0].isoformat() if row[0] else None,
                    "description": row[1],
                    "amount": float(row[2]) if row[2] else 0,
                    "currency": row[3],
                    "merchant": row[4],
                    "status": row[5],
                }
            )

        return {"transactions": transactions, "count": len(transactions)}
    finally:
        cursor.close()
        conn.close()


@router.get("/{tenant_id}/revenue-growth")
async def get_revenue_growth(tenant_id: str):
    """Calculate revenue growth (MoM and YoY)."""
    conn = get_tenant_connection(tenant_id)
    cursor = conn.cursor()

    try:
        tenant_short_id = tenant_id.replace("-", "_")[:8].upper()

        # Get monthly revenue (positive transactions)
        cursor.execute(f"""
            SELECT 
                DATE_TRUNC('month', booked_date) as month,
                SUM(amount) as monthly_revenue
            FROM ARCIMS_PROD.TINK_{tenant_short_id}.TRANSACTIONS
            WHERE amount > 0
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """)

        results = cursor.fetchall()

        if len(results) < 2:
            return {
                "mom_growth": None,
                "yoy_growth": None,
                "message": "Insufficient data for growth calculation",
            }

        # Month over month
        current_month = float(results[0][1]) if results[0][1] else 0
        prev_month = float(results[1][1]) if results[1][1] else 0

        mom_growth = (
            ((current_month - prev_month) / prev_month * 100) if prev_month else None
        )

        # Year over year (if 12 months available)
        yoy_growth = None
        if len(results) >= 12:
            year_ago = float(results[11][1]) if results[11][1] else 0
            yoy_growth = (
                ((current_month - year_ago) / year_ago * 100) if year_ago else None
            )

        return {
            "mom_growth": round(mom_growth, 2) if mom_growth else None,
            "yoy_growth": round(yoy_growth, 2) if yoy_growth else None,
            "current_month_revenue": current_month,
            "currency": "SEK",
        }
    finally:
        cursor.close()
        conn.close()


@router.get("/{tenant_id}/gross-margin")
async def get_gross_margin(tenant_id: str):
    """
    Calculate gross margin using Fortnox account data.
    Gross Margin = (Revenue - COGS) / Revenue
    """
    conn = get_tenant_connection(tenant_id)
    cursor = conn.cursor()

    try:
        tenant_short_id = tenant_id.replace("-", "_")[:8].upper()

        # This is simplified - in production you'd need proper account mapping
        # Revenue accounts typically 3000-3999 in Swedish BAS
        # COGS accounts typically 4000-6999

        cursor.execute(f"""
            SELECT 
                CASE 
                    WHEN NUMBER BETWEEN 3000 AND 3999 THEN 'revenue'
                    WHEN NUMBER BETWEEN 4000 AND 6999 THEN 'cogs'
                END as account_type,
                COUNT(*) as account_count
            FROM ARCIMS_PROD.FORTNOX_{tenant_short_id}.ACCOUNT
            WHERE NUMBER BETWEEN 3000 AND 6999
            GROUP BY account_type
        """)

        results = cursor.fetchall()

        revenue_accounts = 0
        cogs_accounts = 0

        for row in results:
            if row[0] == "revenue":
                revenue_accounts = row[1]
            elif row[0] == "cogs":
                cogs_accounts = row[1]

        return {
            "revenue_accounts": revenue_accounts,
            "cogs_accounts": cogs_accounts,
            "message": "Gross margin calculation requires transaction data. Currently showing account structure.",
            "note": "Connect to Fortnox vouchers for actual margin calculation",
        }
    finally:
        cursor.close()
        conn.close()


@router.get("/{tenant_id}/dashboard-summary")
async def get_dashboard_summary(tenant_id: str):
    """Get all key metrics in one call."""
    cash = await get_cash_position(tenant_id)
    burn = await get_burn_rate(tenant_id)
    runway = await get_runway(tenant_id)
    growth = await get_revenue_growth(tenant_id)

    return {
        "cash_position": cash,
        "burn_rate": burn,
        "runway": runway,
        "revenue_growth": growth,
        "last_updated": datetime.utcnow().isoformat(),
    }
