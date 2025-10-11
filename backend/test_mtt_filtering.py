from app.services.snowflake_service import SnowflakeService
from app.services.tenant_service import TenantService
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import snowflake.connector

tenant_service = TenantService()

# Get all tenants
conn = tenant_service._get_connection()
cursor = conn.cursor()
cursor.execute("SELECT tenant_id, snowflake_role FROM tenants")
tenants = cursor.fetchall()
cursor.close()
conn.close()

# Test first tenant
tenant_id, role_name = tenants[-1]  # Use last tenant

print(f"Testing MTT access for tenant: {tenant_id[:13]}...")
print(f"Using role: {role_name}")

service = SnowflakeService()

# Load private key
with open(service.private_key_path, "rb") as key_file:
    p_key = serialization.load_pem_private_key(
        key_file.read(), password=None, backend=default_backend()
    )

pkb = p_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

# Connect AS the tenant role
conn = snowflake.connector.connect(
    user=service.user,
    account=service.account,
    private_key=pkb,
    role=role_name,  # Tenant role
    warehouse=service.warehouse,
    database=service.database,
    schema=service.schema,
)

cursor = conn.cursor()

# Check what schemas this role can see
tenant_short_id = tenant_id.replace("-", "_")[:8].upper()
fortnox_schema = f"FORTNOX_{tenant_short_id}"

try:
    # Try to access tenant's own schema
    cursor.execute(f"SHOW TABLES IN SCHEMA ARCIMS_PROD.{fortnox_schema}")
    tables = cursor.fetchall()

    if tables:
        print(f"✓ Tenant role can see {len(tables)} tables in own schema")

        # Try to query first table
        table_name = tables[0][1]
        cursor.execute(
            f"SELECT COUNT(*) FROM ARCIMS_PROD.{fortnox_schema}.{table_name}"
        )
        count = cursor.fetchone()[0]
        print(f"✓ Can query {table_name}: {count} rows")
    else:
        print("⚠️  No tables visible")

except Exception as e:
    print(f"❌ Cannot access own schema: {e}")

# Try to access another tenant's schema (should fail)
other_tenants = [t for t in tenants if t[0] != tenant_id]
if other_tenants:
    other_id = other_tenants[0][0]
    other_short_id = other_id.replace("-", "_")[:8].upper()
    other_schema = f"FORTNOX_{other_short_id}"

    try:
        cursor.execute(f"SHOW TABLES IN SCHEMA ARCIMS_PROD.{other_schema}")
        tables = cursor.fetchall()
        if tables:
            print(f"❌ SECURITY ISSUE: Can see other tenant's schema!")
        else:
            print(f"✓ Cannot see other tenant's tables (correct)")
    except Exception as e:
        print(f"✓ Cannot access other tenant's schema (correct)")

cursor.close()
conn.close()
