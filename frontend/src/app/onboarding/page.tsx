export default function OnboardingPage() {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-2xl">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Welcome to Arcims!</h1>
          <p className="text-gray-600 mb-6">
            Next step: Connect your ERP and banking data sources.
          </p>
          <p className="text-sm text-gray-500">
            (Fivetran Connect Card will be embedded here)
          </p>
        </div>
      </div>
    );
  }