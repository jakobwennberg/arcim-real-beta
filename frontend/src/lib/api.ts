const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Tenant {
  tenant_id: string;
  company_name: string | null;
  clerk_user_id: string;
  email: string;
  snowflake_role: string;
  onboarding_state: string;
  created_at: string;
  data_ready: boolean;
  fivetran_group_id?: string;
  fivetran_connector_id?: string;
}

export interface FivetranSetup {
  group_id: string;
  connector_id: string;
  connect_card_uri: string;
  service: string;
}

export async function getTenantByClerkId(clerkUserId: string): Promise<Tenant | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/tenants/${clerkUserId}`);
    
    if (response.status === 404) {
      return null;
    }
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching tenant:', error);
    throw error;
  }
}

export async function updateCompanyName(tenantId: string, companyName: string): Promise<Tenant> {
  const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/company?company_name=${encodeURIComponent(companyName)}`, {
    method: 'PATCH',
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

export async function updateOnboardingState(tenantId: string, state: string): Promise<Tenant> {
  const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/state?state=${state}`, {
    method: 'PATCH',
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

export async function setupFivetran(tenantId: string): Promise<FivetranSetup> {
  const response = await fetch(`${API_BASE_URL}/api/fivetran/setup/${tenantId}`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

export async function getFivetranStatus(tenantId: string) {
  const response = await fetch(`${API_BASE_URL}/api/fivetran/status/${tenantId}`);
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}