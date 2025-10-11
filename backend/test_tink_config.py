# backend/test_tink_config.py
from app.core.config import settings

print(f"Tink Client ID: {settings.tink_client_id}")
print(f"Tink Client Secret: {settings.tink_client_secret[:10]}...")
