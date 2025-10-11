from app.services.snowflake_service import SnowflakeService

service = SnowflakeService()
conn = service._get_connection(use_admin=True)
cursor = conn.cursor()

# Get all Fortnox schemas
cursor.execute("SHOW SCHEMAS IN DATABASE ARCIMS_PROD")
schemas = [row[1] for row in cursor.fetchall() if row[1].startswith("FORTNOX_")]

print(f"Found {len(schemas)} Fortnox schemas")

for schema in schemas:
    print(f"\nGranting access to {schema}...")

    try:
        # Grant usage on schema
        cursor.execute(
            f"GRANT USAGE ON SCHEMA ARCIMS_PROD.{schema} TO ROLE {service.admin_role}"
        )

        # Grant select on all tables
        cursor.execute(
            f"GRANT SELECT ON ALL TABLES IN SCHEMA ARCIMS_PROD.{schema} TO ROLE {service.admin_role}"
        )

        # Grant select on future tables
        cursor.execute(
            f"GRANT SELECT ON FUTURE TABLES IN SCHEMA ARCIMS_PROD.{schema} TO ROLE {service.admin_role}"
        )

        print(f"  ✓ Granted")
    except Exception as e:
        print(f"  ⚠️  {e}")

cursor.close()
conn.close()

print("\n✅ Done")
