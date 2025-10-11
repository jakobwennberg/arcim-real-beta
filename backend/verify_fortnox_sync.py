from app.services.snowflake_service import SnowflakeService
from app.services.tenant_service import TenantService

# Get your test tenant - use actual Clerk user ID
tenant_service = TenantService()

# First, let's see all tenants
conn = tenant_service._get_connection()
cursor = conn.cursor()
cursor.execute(
    "SELECT tenant_id, company_name, clerk_user_id, onboarding_state, data_ready FROM tenants"
)
tenants = cursor.fetchall()

print("Available tenants:")
for t in tenants:
    print(
        f"  ID: {t[0][:13]}... | Company: {t[1]} | Clerk: {t[2][:10]}... | State: {t[3]} | Ready: {t[4]}"
    )

cursor.close()
conn.close()

# Pick the most recent tenant
if not tenants:
    print("❌ No tenants found in database")
    exit(1)

tenant_id = tenants[-1][0]  # Use last tenant
print(f"\n🔍 Checking tenant: {tenant_id}")

tenant = tenant_service.get_tenant_by_id(tenant_id)

print(f"✓ Tenant found")
print(f"  Company: {tenant['company_name']}")
print(f"  State: {tenant['onboarding_state']}")
print(f"  Data ready: {tenant['data_ready']}")
print(f"  Fivetran connector: {tenant.get('fivetran_connector_id')}")

# Connect to Snowflake
service = SnowflakeService()
conn = service._get_connection(use_admin=True)
cursor = conn.cursor()

# Check schemas
print("\n📁 All schemas in ARCIMS_PROD:")
cursor.execute("SHOW SCHEMAS IN DATABASE ARCIMS_PROD")
schemas = [row[1] for row in cursor.fetchall()]
for schema in schemas:
    if schema.startswith("FORTNOX_"):
        print(f"  ✓ {schema}")

# Look for this tenant's Fortnox schema
tenant_short_id = tenant["tenant_id"].replace("-", "_")[:8].upper()
fortnox_schema = f"FORTNOX_{tenant_short_id}"

print(f"\n🔍 Looking for schema: {fortnox_schema}")

if fortnox_schema in schemas:
    print(f"✓ Schema exists!")

    # Check tables
    cursor.execute(f"SHOW TABLES IN SCHEMA ARCIMS_PROD.{fortnox_schema}")
    tables = cursor.fetchall()

    if tables:
        print(f"✓ Found {len(tables)} tables:")
        for table in tables[:10]:  # Show first 10
            table_name = table[1]
            # Get row count
            cursor.execute(
                f"SELECT COUNT(*) FROM ARCIMS_PROD.{fortnox_schema}.{table_name}"
            )
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} rows")

        # Sample data from first table with data
        for table in tables:
            table_name = table[1]
            cursor.execute(
                f"SELECT COUNT(*) FROM ARCIMS_PROD.{fortnox_schema}.{table_name}"
            )
            if cursor.fetchone()[0] > 0:
                print(f"\n📊 Sample from {table_name}:")
                cursor.execute(
                    f"SELECT * FROM ARCIMS_PROD.{fortnox_schema}.{table_name} LIMIT 3"
                )
                rows = cursor.fetchall()
                for row in rows[:3]:
                    print(f"  {row[:5]}...")  # Show first 5 columns
                break
    else:
        print("⚠️  Schema exists but no tables yet")
else:
    print(f"❌ Schema not found: {fortnox_schema}")
    print(f"\nAvailable Fortnox schemas:")
    for s in schemas:
        if s.startswith("FORTNOX_"):
            print(f"  {s}")

cursor.close()
conn.close()
