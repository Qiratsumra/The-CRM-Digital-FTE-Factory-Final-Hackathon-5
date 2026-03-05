"use client";

import { useState } from "react";
import { checkHealth, submitTicket } from "@/lib/api";

export default function TestApiPage() {
  const [health, setHealth] = useState<unknown>(null);
  const [testTicket, setTestTicket] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const testHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await checkHealth();
      setHealth(data);
      console.log('[Test API] Health check:', data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Health check failed");
    } finally {
      setLoading(false);
    }
  };

  const testSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await submitTicket({
        name: "Test User",
        email: "test@example.com",
        subject: "API Connection Test",
        category: "general",
        priority: "low",
        message: "This is a test message to verify API connection is working.",
      });
      setTestTicket(data);
      console.log('[Test API] Ticket submitted:', data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submit failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">API Connection Test</h1>
        
        <div className="space-y-4">
          <button
            onClick={testHealth}
            disabled={loading}
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? "Testing..." : "Test Health Endpoint"}
          </button>

          <button
            onClick={testSubmit}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Testing..." : "Test Submit Ticket"}
          </button>
        </div>

        {error && (
          <div className="mt-6 p-4 bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-red-800 dark:text-red-200 font-semibold">Error:</p>
            <p className="text-red-700 dark:text-red-300">{error}</p>
          </div>
        )}

        {health && (
          <div className="mt-6 p-4 bg-green-100 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <p className="text-green-800 dark:text-green-200 font-semibold mb-2">✅ Health Check Passed:</p>
            <pre className="text-sm text-green-700 dark:text-green-300 overflow-auto">
              {JSON.stringify(health, null, 2)}
            </pre>
          </div>
        )}

        {testTicket && (
          <div className="mt-6 p-4 bg-blue-100 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-blue-800 dark:text-blue-200 font-semibold mb-2">✅ Ticket Submitted:</p>
            <pre className="text-sm text-blue-700 dark:text-blue-300 overflow-auto">
              {JSON.stringify(testTicket, null, 2)}
            </pre>
          </div>
        )}

        <div className="mt-8 p-4 bg-zinc-100 dark:bg-zinc-800 rounded-lg">
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            <strong>Backend URL:</strong> https://crm-digital-fte-factory-final-hackathon.onrender.com<br/>
            <strong>Check console logs</strong> for detailed API request/response information.
          </p>
        </div>
      </div>
    </div>
  );
}
