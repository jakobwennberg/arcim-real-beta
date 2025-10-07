from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str

    # Clerk
    clerk_secret_key: str
    clerk_webhook_secret: str

    # Snowflake (Fivetran user)
    snowflake_account: str
    snowflake_user: str
    snowflake_private_key_path: str
    snowflake_database: str = "ARCIMS_PROD"
    snowflake_schema: str = "PUBLIC"
    snowflake_warehouse: str = "FIVETRAN_WH"

    # Snowflake (admin / Arcim provisioning user)
    snowflake_admin_user: str = "arcim_admin_user"
    snowflake_admin_role: str = "ARCIM_ADMIN_ROLE"
    snowflake_admin_private_key_path: str = (
        "/Users/jakobwennberg/arcims/arcim_admin_rsa_key.p8"
    )

    # Fivetran
    fivetran_auth_token: str

    # Fortnox
    fortnox_client_id: str
    fortnox_client_secret: str
    fortnox_scopes: str

    # Frontend
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
