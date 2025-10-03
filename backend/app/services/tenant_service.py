import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional
from app.core.config import settings


class TenantService:
    def __init__(self):
        self.db_url = settings.database_url

    def _get_connection(self):
        return psycopg2.connect(self.db_url)

    def create_tenant(
        self, company_name: Optional[str], clerk_user_id: str, email: str
    ) -> dict:
        """
        Creates tenant record in PostgreSQL.
        Company name can be null initially, collected during onboarding.
        Returns tenant data including generated tenant_id.
        """
        tenant_id = str(uuid.uuid4())
        snowflake_role = f"TENANT_{tenant_id.replace('-', '_').upper()}"

        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Insert tenant record
            cursor.execute(
                """
                INSERT INTO tenants (
                    tenant_id, company_name, clerk_user_id, email, 
                    snowflake_role, onboarding_state, created_at, data_ready
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """,
                (
                    tenant_id,
                    company_name,
                    clerk_user_id,
                    email,
                    snowflake_role,
                    "pending",
                    datetime.utcnow(),
                    False,
                ),
            )

            tenant = cursor.fetchone()
            conn.commit()

            return dict(tenant)

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_tenant_by_clerk_id(self, clerk_user_id: str) -> Optional[dict]:
        """Fetch tenant by Clerk user ID."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                """
                SELECT * FROM tenants WHERE clerk_user_id = %s
            """,
                (clerk_user_id,),
            )

            tenant = cursor.fetchone()
            return dict(tenant) if tenant else None

        finally:
            cursor.close()
            conn.close()

    def get_tenant_by_id(self, tenant_id: str) -> Optional[dict]:
        """Fetch tenant by tenant_id."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                """
                SELECT * FROM tenants WHERE tenant_id = %s
            """,
                (tenant_id,),
            )

            tenant = cursor.fetchone()
            return dict(tenant) if tenant else None

        finally:
            cursor.close()
            conn.close()

    def update_company_name(self, tenant_id: str, company_name: str) -> Optional[dict]:
        """Update company name during onboarding."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                """
                UPDATE tenants 
                SET company_name = %s, updated_at = %s
                WHERE tenant_id = %s
                RETURNING *
            """,
                (company_name, datetime.utcnow(), tenant_id),
            )

            tenant = cursor.fetchone()
            conn.commit()

            return dict(tenant) if tenant else None

        finally:
            cursor.close()
            conn.close()

    def update_onboarding_state(self, tenant_id: str, state: str) -> Optional[dict]:
        """Update tenant onboarding state."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                """
                UPDATE tenants 
                SET onboarding_state = %s, updated_at = %s
                WHERE tenant_id = %s
                RETURNING *
            """,
                (state, datetime.utcnow(), tenant_id),
            )

            tenant = cursor.fetchone()
            conn.commit()

            return dict(tenant) if tenant else None

        finally:
            cursor.close()
            conn.close()

    def mark_data_ready(self, tenant_id: str) -> Optional[dict]:
        """Mark tenant data as ready after Fivetran sync completes."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                """
                UPDATE tenants 
                SET data_ready = TRUE, onboarding_state = 'ready', updated_at = %s
                WHERE tenant_id = %s
                RETURNING *
            """,
                (datetime.utcnow(), tenant_id),
            )

            tenant = cursor.fetchone()
            conn.commit()

            return dict(tenant) if tenant else None

        finally:
            cursor.close()
            conn.close()
