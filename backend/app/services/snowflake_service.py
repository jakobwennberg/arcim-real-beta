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

    def _get_private_key(self):
        """Load and parse private key for authentication."""
        with open(self.private_key_path, "rb") as key_file:
            p_key = serialization.load_pem_private_key(
                key_file.read(), password=None, backend=default_backend()
            )

        pkb = p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return pkb

    def _get_connection(self):
        """Get Snowflake connection using key-pair auth."""
        return snowflake.connector.connect(
            user=self.user,
            account=self.account,
            private_key=self._get_private_key(),
            warehouse=self.warehouse,
            database=self.database,
            schema=self.schema,
        )

    def create_tenant_role(self, tenant_id: str) -> str:
        """
        Creates Snowflake role for tenant.
        Grants SELECT on secure views.
        Returns role name.
        """
        role_name = f"TENANT_{tenant_id.replace('-', '_').upper()}"

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Create role
            cursor.execute(f"CREATE ROLE IF NOT EXISTS {role_name}")

            # Grant usage on warehouse
            cursor.execute(
                f"GRANT USAGE ON WAREHOUSE {self.warehouse} TO ROLE {role_name}"
            )

            # Grant usage on database and schema
            cursor.execute(
                f"GRANT USAGE ON DATABASE {self.database} TO ROLE {role_name}"
            )
            cursor.execute(
                f"GRANT USAGE ON SCHEMA {self.database}.{self.schema} TO ROLE {role_name}"
            )

            # Grant SELECT on all future tables (for Fivetran writes)
            cursor.execute(f"""
                GRANT SELECT ON ALL TABLES IN SCHEMA {self.database}.{self.schema} TO ROLE {role_name}
            """)
            cursor.execute(f"""
                GRANT SELECT ON FUTURE TABLES IN SCHEMA {self.database}.{self.schema} TO ROLE {role_name}
            """)

            # Grant role to fivetran_user so Fivetran can use it
            cursor.execute(f"GRANT ROLE {role_name} TO USER {self.user}")

            return role_name

        finally:
            cursor.close()
            conn.close()

    def create_entitlement_entry(self, tenant_id: str, role_name: str):
        """
        Creates entry in entitlements table mapping role to tenant_id.
        Required for MTT secure views to filter data.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(f"""
                INSERT INTO {self.database}.{self.schema}.ENTITLEMENTS (role_name, tenant_id)
                VALUES ('{role_name}', '{tenant_id}')
            """)

        finally:
            cursor.close()
            conn.close()
