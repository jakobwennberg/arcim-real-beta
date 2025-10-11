# backend/check_tenant_status.py
from app.services.tenant_service import TenantService

service = TenantService()
tenant = service.get_tenant_by_clerk_id("your_clerk_id")

print(f"Onboarding state: {tenant['onboarding_state']}")
print(f"Data ready: {tenant['data_ready']}")
print(f"Fivetran connector: {tenant.get('fivetran_connector_id')}")
