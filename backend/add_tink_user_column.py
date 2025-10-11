# backend/add_tink_user_column.py
import psycopg2
from app.core.config import settings

conn = psycopg2.connect(settings.database_url)
cursor = conn.cursor()

cursor.execute("""
    ALTER TABLE tenants 
    ADD COLUMN IF NOT EXISTS tink_user_id VARCHAR(255)
""")

conn.commit()
cursor.close()
conn.close()

print("✓ Added tink_user_id column")
