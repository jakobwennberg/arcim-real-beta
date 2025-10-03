import { UserButton } from "@clerk/nextjs";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-900">
      <header className="bg-gray-800 border-b border-gray-700 px-8 py-4">
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-bold text-white">Arcims</h1>
          <UserButton afterSignOutUrl="/" />
        </div>
      </header>
      
      <main className="p-8">
        <p className="text-gray-400">(Dashboard metrics will appear here)</p>
      </main>
    </div>
  );
}