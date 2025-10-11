# backend/create_secure_views.py
from app.services.snowflake_service import SnowflakeService

service = SnowflakeService()
conn = service._get_connection(use_admin=True)
cursor = conn.cursor()

# Example: Create secure view for invoices
cursor.execute("""
    CREATE OR REPLACE SECURE VIEW ARCIMS_PROD.PUBLIC.invoices_secure AS
    SELECT i.*
    FROM ARCIMS_PROD.fortnox_<tenant_short_id>.invoices i
    JOIN ARCIMS_PROD.PUBLIC.ENTITLEMENTS e
        ON e.tenant_id = i.tenant_id
    WHERE e.role_name = CURRENT_ROLE()
""")

cursor.close()
conn.close()
