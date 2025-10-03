import { SignedIn, SignedOut, SignInButton, SignUpButton, UserButton } from "@clerk/nextjs";
import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 px-8 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Arcims</h1>
          
          <SignedOut>
            <div className="flex gap-4">
              <SignInButton mode="modal">
                <button className="px-4 py-2 text-gray-700 hover:text-gray-900">
                  Sign In
                </button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Get Started
                </button>
              </SignUpButton>
            </div>
          </SignedOut>
          
          <SignedIn>
            <div className="flex gap-4 items-center">
              <Link href="/dashboard" className="text-gray-700 hover:text-gray-900">
                Dashboard
              </Link>
              <UserButton afterSignOutUrl="/" />
            </div>
          </SignedIn>
        </div>
      </header>

      {/* Hero */}
      <main className="max-w-7xl mx-auto px-8 py-24">
        <div className="text-center">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            Financial clarity for Swedish SMEs
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Unified dashboard aggregating Fortnox/Visma and Swedish banking data with AI-powered insights.
          </p>
          <SignedOut>
            <SignUpButton mode="modal">
              <button className="px-8 py-4 bg-blue-600 text-white text-lg rounded-lg hover:bg-blue-700">
                Start Free Trial
              </button>
            </SignUpButton>
          </SignedOut>
          <SignedIn>
            <Link href="/dashboard">
              <button className="px-8 py-4 bg-blue-600 text-white text-lg rounded-lg hover:bg-blue-700">
                Go to Dashboard
              </button>
            </Link>
          </SignedIn>
        </div>
      </main>
    </div>
  );
}