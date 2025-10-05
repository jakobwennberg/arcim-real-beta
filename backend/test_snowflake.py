from app.services.snowflake_service import SnowflakeService

# Test connection
service = SnowflakeService()
conn = service._get_connection()
print("✓ Connection successful")

cursor = conn.cursor()
cursor.execute("SELECT CURRENT_ROLE(), CURRENT_USER(), CURRENT_DATABASE()")
result = cursor.fetchone()
print(f"Role: {result[0]}, User: {result[1]}, Database: {result[2]}")

cursor.close()
conn.close()
