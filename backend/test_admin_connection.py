import snowflake.connector
from cryptography.hazmat.primitives import serialization

path = "/Users/jakobwennberg/arcims/arcim_admin_rsa_key.p8"
with open(path, "rb") as f:
    key = serialization.load_pem_private_key(f.read(), password=None)
pkb = key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

print("Connecting to Snowflake...")
conn = snowflake.connector.connect(
    user="ARCIM_ADMIN",
    account="ZNAWDCX-ZTB41864",
    private_key=pkb,
    role="ARCIM_ADMIN_ROLE",
    warehouse="FIVETRAN_WH",
)
print("✅ Connected!")
conn.close()
