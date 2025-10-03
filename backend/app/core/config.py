from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str

    # Clerk
    clerk_secret_key: str
    clerk_webhook_secret: str

    # Snowflake
    snowflake_account: str
    snowflake_user: str
    snowflake_private_key_path: str
    snowflake_database: str = "ARCIMS_PROD"
    snowflake_schema: str = "PUBLIC"
    snowflake_warehouse: str = "FIVETRAN_WH"

    # Fivetran
    fivetran_auth_token: str

    class Config:
        env_file = ".env"


settings = Settings()
