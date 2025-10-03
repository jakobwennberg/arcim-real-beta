CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(36) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    clerk_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    snowflake_role VARCHAR(255) NOT NULL,
    onboarding_state VARCHAR(50) NOT NULL DEFAULT 'pending',
    data_ready BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clerk_user_id ON tenants(clerk_user_id);
CREATE INDEX idx_tenant_id ON tenants(tenant_id);