import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from app.core.config import settings


class SnowflakeService:
    def __init__(self):
        self.account = settings.snowflake_account
        self.user = settings.snowflake_user
        self.database = settings.snowflake_database
        self.schema = settings.snowflake_schema
        self.warehouse = settings.snowflake_warehouse
        self.private_key_path = settings.snowflake_private_key_path

        # Admin credentials
        self.admin_user = settings.snowflake_admin_user
        self.admin_role = settings.snowflake_admin_role
        self.admin_private_key_path = settings.snowflake_admin_private_key_path

    def _get_private_key(self, key_path):
        """Load and parse private key for authentication."""
        with open(key_path, "rb") as key_file:
            p_key = serialization.load_pem_private_key(
                key_file.read(), password=None, backend=default_backend()
            )

        pkb = p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return pkb

    def _get_connection(self, use_admin=False):
        """Get Snowflake connection using key-pair auth."""
        if use_admin:
            return snowflake.connector.connect(
                user=self.admin_user,
                account=self.account,
                private_key=self._get_private_key(self.admin_private_key_path),
                role=self.admin_role,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema,
            )
        else:
            return snowflake.connector.connect(
                user=self.user,
                account=self.account,
                private_key=self._get_private_key(self.private_key_path),
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema,
            )

    def create_tenant_role(self, tenant_id: str) -> str:
        role_name = f"TENANT_{tenant_id.replace('-', '_').upper()}"

        conn = self._get_connection(use_admin=True)
        cursor = conn.cursor()
        try:
            print(f"Creating role: {role_name}")
            cursor.execute(f"CREATE ROLE IF NOT EXISTS {role_name}")

            # Warehouse access
            cursor.execute(
                f"GRANT USAGE, OPERATE ON WAREHOUSE {self.warehouse} TO ROLE {role_name}"
            )

            # Database-level access (needed + create schema)
            cursor.execute(
                f"GRANT USAGE ON DATABASE {self.database} TO ROLE {role_name}"
            )
            cursor.execute(
                f"GRANT CREATE SCHEMA ON DATABASE {self.database} TO ROLE {role_name}"
            )

            # Existing/public schema for shared objects (ENTITLEMENTS/secure views)
            cursor.execute(
                f"GRANT USAGE ON SCHEMA {self.database}.{self.schema} TO ROLE {role_name}"
            )

            # Ensure read on shared views/tables (if you expose from PUBLIC)
            cursor.execute(
                f"GRANT SELECT ON ALL VIEWS IN SCHEMA {self.database}.{self.schema} TO ROLE {role_name}"
            )
            cursor.execute(
                f"GRANT SELECT ON FUTURE VIEWS IN SCHEMA {self.database}.{self.schema} TO ROLE {role_name}"
            )

            # ⭐ Auto-grants for any NEW schemas Fivetran creates (e.g., fortnox_<id>)
            cursor.execute(
                f"GRANT USAGE ON FUTURE SCHEMAS IN DATABASE {self.database} TO ROLE {role_name}"
            )
            cursor.execute(
                f"GRANT CREATE TABLE, CREATE VIEW, CREATE STAGE "
                f"ON FUTURE SCHEMAS IN DATABASE {self.database} TO ROLE {role_name}"
            )

            # Let the Fivetran user assume this tenant role
            cursor.execute(f"GRANT ROLE {role_name} TO USER {self.user}")

            print(f"Role {role_name} created and granted successfully")
            return role_name
        finally:
            cursor.close()
            conn.close()

    def create_entitlement_entry(self, tenant_id: str, role_name: str):
        """
        Creates entry in entitlements table mapping role to tenant_id.
        Required for MTT secure views to filter data.
        """
        conn = self._get_connection(use_admin=True)
        cursor = conn.cursor()

        try:
            print(f"Creating entitlement entry for {role_name} -> {tenant_id}")

            cursor.execute(f"""
                INSERT INTO {self.database}.{self.schema}.ENTITLEMENTS (role_name, tenant_id)
                VALUES ('{role_name}', '{tenant_id}')
            """)

            print(f"Entitlement entry created")

        finally:
            cursor.close()
            conn.close()
