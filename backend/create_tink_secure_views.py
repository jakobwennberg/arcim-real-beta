from app.services.snowflake_service import SnowflakeService

service = SnowflakeService()
conn = service._get_connection(use_admin=True)
cursor = conn.cursor()

print("Creating secure views for Tink data...")

# Secure view for accounts
cursor.execute("""
    CREATE OR REPLACE SECURE VIEW ARCIMS_PROD.PUBLIC.TINK_ACCOUNTS_SECURE AS
    SELECT a.*
    FROM ARCIMS_PROD.TINK_0973369A.ACCOUNTS a
    JOIN ARCIMS_PROD.PUBLIC.ENTITLEMENTS e
        ON e.tenant_id = a.tenant_id
    WHERE e.role_name = CURRENT_ROLE()
""")
print("✓ Created TINK_ACCOUNTS_SECURE")

# Secure view for transactions
cursor.execute("""
    CREATE OR REPLACE SECURE VIEW ARCIMS_PROD.PUBLIC.TINK_TRANSACTIONS_SECURE AS
    SELECT t.*
    FROM ARCIMS_PROD.TINK_0973369A.TRANSACTIONS t
    JOIN ARCIMS_PROD.PUBLIC.ENTITLEMENTS e
        ON e.tenant_id = t.tenant_id
    WHERE e.role_name = CURRENT_ROLE()
""")
print("✓ Created TINK_TRANSACTIONS_SECURE")

# Grant access to tenant roles
cursor.execute("""
    GRANT SELECT ON VIEW ARCIMS_PROD.PUBLIC.TINK_ACCOUNTS_SECURE 
    TO ROLE TENANT_0973369A_5994_4878_8D0D_04D87BC630FF
""")

cursor.execute("""
    GRANT SELECT ON VIEW ARCIMS_PROD.PUBLIC.TINK_TRANSACTIONS_SECURE 
    TO ROLE TENANT_0973369A_5994_4878_8D0D_04D87BC630FF
""")

print("✓ Granted permissions to tenant role")

cursor.close()
conn.close()

print("\n=== Test secure view access ===")

# Test as tenant role
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import snowflake.connector

with open(service.private_key_path, "rb") as f:
    key = serialization.load_pem_private_key(
        f.read(), password=None, backend=default_backend()
    )

pkb = key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

conn = snowflake.connector.connect(
    user=service.user,
    account=service.account,
    private_key=pkb,
    role="TENANT_0973369A_5994_4878_8D0D_04D87BC630FF",
    warehouse=service.warehouse,
    database=service.database,
)

cursor = conn.cursor()

# Query via secure view
cursor.execute("SELECT COUNT(*) FROM ARCIMS_PROD.PUBLIC.TINK_ACCOUNTS_SECURE")
count = cursor.fetchone()[0]
print(f"Tenant can see {count} accounts via secure view")

cursor.execute("SELECT COUNT(*) FROM ARCIMS_PROD.PUBLIC.TINK_TRANSACTIONS_SECURE")
count = cursor.fetchone()[0]
print(f"Tenant can see {count} transactions via secure view")

cursor.close()
conn.close()
