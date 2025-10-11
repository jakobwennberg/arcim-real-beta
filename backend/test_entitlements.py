from app.services.snowflake_service import SnowflakeService
from app.services.tenant_service import TenantService

tenant_service = TenantService()

# Get all tenants
conn = tenant_service._get_connection()
cursor = conn.cursor()
cursor.execute("SELECT tenant_id, snowflake_role FROM tenants")
tenants = cursor.fetchall()
cursor.close()
conn.close()

print(f"Checking entitlements for {len(tenants)} tenants")

service = SnowflakeService()
conn = service._get_connection(use_admin=True)
cursor = conn.cursor()

# Check if entitlements table exists
try:
    cursor.execute("SELECT role_name, tenant_id FROM ARCIMS_PROD.PUBLIC.ENTITLEMENTS")
    entitlements = cursor.fetchall()

    print(f"\n✓ Entitlements table exists with {len(entitlements)} entries:")
    for ent in entitlements:
        print(f"  {ent[0]} → {ent[1][:13]}...")

    # Check if all tenants have entitlements
    tenant_ids = {t[0] for t in tenants}
    ent_tenant_ids = {e[1] for e in entitlements}

    missing = tenant_ids - ent_tenant_ids
    if missing:
        print(f"\n⚠️  Missing entitlements for {len(missing)} tenants:")
        for tid in missing:
            print(f"  {tid[:13]}...")
    else:
        print(f"\n✓ All {len(tenants)} tenants have entitlements")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\n Creating entitlements table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ARCIMS_PROD.PUBLIC.ENTITLEMENTS (
            role_name VARCHAR(255),
            tenant_id VARCHAR(36)
        )
    """)

    # Insert entries for all tenants
    for tenant_id, role_name in tenants:
        cursor.execute(f"""
            INSERT INTO ARCIMS_PROD.PUBLIC.ENTITLEMENTS (role_name, tenant_id)
            VALUES ('{role_name}', '{tenant_id}')
        """)

    print(f"✓ Created entitlements for {len(tenants)} tenants")

cursor.close()
conn.close()
