'use client';

import { useUser } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import { getTenantByClerkId, getFivetranStatus } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function ConnectionCompletePage() {
  const { user, isLoaded } = useUser();
  const router = useRouter();
  const [status, setStatus] = useState<'checking' | 'connected' | 'failed'>('checking');
  const [message, setMessage] = useState('Verifying your connection...');

  useEffect(() => {
    async function checkConnection() {
      if (!isLoaded || !user) return;

      try {
        const tenant = await getTenantByClerkId(user.id);
        if (!tenant) {
          setStatus('failed');
          setMessage('Tenant not found');
          return;
        }

        // Check Fivetran connector status
        const fivetranStatus = await getFivetranStatus(tenant.tenant_id);
        
        if (fivetranStatus.setup_state === 'connected') {
          setStatus('connected');
          setMessage('Connection successful! Your data will sync within 24 hours.');
          
          // Redirect to dashboard after 3 seconds
          setTimeout(() => {
            router.push('/dashboard');
          }, 3000);
        } else if (fivetranStatus.setup_state === 'broken') {
          setStatus('failed');
          setMessage('Connection failed. Please try again.');
        } else {
          setStatus('checking');
          setMessage('Finalizing connection...');
          
          // Retry after 2 seconds
          setTimeout(checkConnection, 2000);
        }
      } catch (err) {
        setStatus('failed');
        setMessage('Failed to verify connection');
      }
    }

    checkConnection();
  }, [user, isLoaded, router]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-2xl w-full text-center">
        {status === 'checking' && (
          <>
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">{message}</h1>
            <p className="text-gray-600">This may take a moment...</p>
          </>
        )}
        
        {status === 'connected' && (
          <>
            <div className="text-green-600 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Connection Successful!</h1>
            <p className="text-gray-600 mb-4">{message}</p>
            <p className="text-sm text-gray-500">Redirecting to dashboard...</p>
          </>
        )}
        
        {status === 'failed' && (
          <>
            <div className="text-red-600 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Connection Failed</h1>
            <p className="text-gray-600 mb-4">{message}</p>
            <button
              onClick={() => router.push('/onboarding')}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Try Again
            </button>
          </>
        )}
      </div>
    </div>
  );
}