from app.services.snowflake_service import SnowflakeService

# Test connection
service = SnowflakeService()
conn = service._get_connection()
print("✓ Connection successful")
conn.close()
