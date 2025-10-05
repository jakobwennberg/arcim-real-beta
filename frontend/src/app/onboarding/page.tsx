'use client';

import { useUser } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import { getTenantByClerkId, updateCompanyName, setupFivetran, Tenant } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function OnboardingPage() {
  const { user, isLoaded } = useUser();
  const router = useRouter();
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [companyName, setCompanyName] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [step, setStep] = useState<'company' | 'connecting'>('company');

  useEffect(() => {
    async function loadTenant() {
      if (!isLoaded || !user) return;
      
      try {
        const tenantData = await getTenantByClerkId(user.id);
        setTenant(tenantData);
        
        // Determine which step to show
        if (tenantData?.company_name) {
          if (tenantData.onboarding_state === 'pending') {
            setStep('company');
            setCompanyName(tenantData.company_name);
          } else {
            setStep('connecting');
          }
        } else {
          setStep('company');
        }
      } catch (err) {
        setError("Failed to load tenant data");
      } finally {
        setLoading(false);
      }
    }
    
    loadTenant();
  }, [user, isLoaded]);

  async function handleCompanySubmit(e: React.FormEvent) {
    e.preventDefault();
    
    if (!tenant || !companyName.trim()) return;
    
    setSaving(true);
    setError("");
    
    try {
      // Save company name
      await updateCompanyName(tenant.tenant_id, companyName.trim());
      
      // Setup Fivetran and get Connect Card URI
      const fivetranSetup = await setupFivetran(tenant.tenant_id);
      
      // Redirect to Connect Card
      window.location.href = fivetranSetup.connect_card_uri;
      
    } catch (err) {
      setError("Failed to setup data connection");
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  if (!tenant) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
          <p className="text-gray-600">Tenant account not found. Please contact support.</p>
        </div>
      </div>
    );
  }

  if (step === 'company') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-2xl w-full">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to Arcims!
          </h1>
          <p className="text-gray-600 mb-8">
            Let's get your financial dashboard set up.
          </p>

          <form onSubmit={handleCompanySubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <input
                type="email"
                id="email"
                value={tenant.email}
                disabled
                className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-600"
              />
            </div>

            <div>
              <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-2">
                Company Name *
              </label>
              <input
                type="text"
                id="company"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Acme AB"
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={saving || !companyName.trim()}
              className="w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {saving ? "Setting up..." : "Connect Data Sources"}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              Next step: Connect your ERP (Fortnox) and banking data via secure authorization
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-2xl w-full">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Connecting Data Sources
        </h1>
        <p className="text-gray-600">
          Please wait while we prepare your connection...
        </p>
      </div>
    </div>
  );
}