"use client";

import { useState, useEffect } from "react";
import { getMetrics, lookupCustomer, MetricsResponse, CustomerLookupResponse } from "@/lib/api";
import Link from "next/link";

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [apiKey, setApiKey] = useState<string>("dev-api-key");

  // Customer lookup state
  const [lookupQuery, setLookupQuery] = useState("");
  const [lookupResult, setLookupResult] = useState<CustomerLookupResponse | null>(null);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupError, setLookupError] = useState<string | null>(null);

  useEffect(() => {
    fetchMetrics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate]);

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMetrics(selectedDate, apiKey);
      setMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lookupQuery.trim()) return;
    setLookupLoading(true);
    setLookupError(null);
    setLookupResult(null);
    try {
      const data = await lookupCustomer(lookupQuery.trim());
      setLookupResult(data);
    } catch (err) {
      setLookupError(err instanceof Error ? err.message : "Customer not found");
    } finally {
      setLookupLoading(false);
    }
  };

  const getSentimentColor = (sentiment: number) => {
    if (sentiment >= 0.7) return "text-green-600 bg-green-100";
    if (sentiment >= 0.4) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  };

  const getSentimentLabel = (sentiment: number) => {
    if (sentiment >= 0.7) return "Positive";
    if (sentiment >= 0.4) return "Neutral";
    return "Negative";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-50 to-zinc-100 dark:from-zinc-950 dark:to-zinc-900">
      {/* Header */}
      <header className="bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-zinc-900 dark:bg-zinc-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white dark:text-zinc-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                  Admin Dashboard
                </h1>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  Customer Success Metrics
                </p>
              </div>
            </div>
            <nav className="flex gap-4">
              <Link href="/" className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100">
                Home
              </Link>
              <Link href="/process" className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100">
                Track Ticket
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Controls */}
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-6 border border-zinc-200 dark:border-zinc-800 mb-8">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                Date
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full px-4 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-zinc-500 focus:border-transparent"
              />
            </div>
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                API Key
              </label>
              <input
                type="text"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full px-4 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-zinc-500 focus:border-transparent"
                placeholder="dev-api-key"
              />
            </div>
            <button
              onClick={fetchMetrics}
              disabled={loading}
              className="px-6 py-2 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-lg font-medium hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Loading...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-6 mb-8">
            <div className="flex items-center gap-3">
              <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h3 className="font-semibold text-red-900 dark:text-red-200">Error Loading Metrics</h3>
                <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && !error && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <svg className="animate-spin h-12 w-12 text-zinc-900 dark:text-zinc-100 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <p className="text-zinc-600 dark:text-zinc-400">Loading metrics...</p>
            </div>
          </div>
        )}

        {/* Metrics Grid */}
        {!loading && !error && metrics && (
          <>
            {/* Overall Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white dark:bg-zinc-900 rounded-2xl p-6 border border-zinc-200 dark:border-zinc-800">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Total Tickets</span>
                </div>
                <p className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
                  {Object.values(metrics).reduce((sum, m) => sum + (m?.total || 0), 0)}
                </p>
              </div>

              <div className="bg-white dark:bg-zinc-900 rounded-2xl p-6 border border-zinc-200 dark:border-zinc-800">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Resolved</span>
                </div>
                <p className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
                  {Object.values(metrics).reduce((sum, m) => sum + (m?.total || 0) - (m?.escalations || 0), 0)}
                </p>
              </div>

              <div className="bg-white dark:bg-zinc-900 rounded-2xl p-6 border border-zinc-200 dark:border-zinc-800">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Escalations</span>
                </div>
                <p className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
                  {Object.values(metrics).reduce((sum, m) => sum + (m?.escalations || 0), 0)}
                </p>
              </div>

              <div className="bg-white dark:bg-zinc-900 rounded-2xl p-6 border border-zinc-200 dark:border-zinc-800">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Avg Response</span>
                </div>
                <p className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
                  {(() => {
                    const total = Object.values(metrics).reduce((sum, m) => sum + (m?.total || 0), 0);
                    const weighted = Object.values(metrics).reduce((sum, m) => sum + ((m?.avg_response_time_sec || 0) * (m?.total || 0)), 0);
                    return total > 0 ? Math.round(weighted / total) : 0;
                  })()}s
                </p>
              </div>
            </div>

            {/* Channel Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {Object.entries(metrics).map(([channel, data]) => (
                <div key={channel} className="bg-white dark:bg-zinc-900 rounded-2xl p-6 border border-zinc-200 dark:border-zinc-800">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 capitalize">
                      {channel.replace("_", " ")}
                    </h3>
                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${getSentimentColor(data.avg_sentiment)}`}>
                      {getSentimentLabel(data.avg_sentiment)} ({data.avg_sentiment.toFixed(2)})
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-zinc-600 dark:text-zinc-400">Total Tickets</span>
                      <span className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">{data.total}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm text-zinc-600 dark:text-zinc-400">Escalations</span>
                      <span className="text-lg font-semibold text-red-600 dark:text-red-400">{data.escalations}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm text-zinc-600 dark:text-zinc-400">Avg Response Time</span>
                      <span className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">{data.avg_response_time_sec}s</span>
                    </div>

                    <div className="pt-4 border-t border-zinc-200 dark:border-zinc-800">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-zinc-600 dark:text-zinc-400">Escalation Rate</span>
                        <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                          {data.total > 0 ? ((data.escalations / data.total) * 100).toFixed(1) : 0}%
                        </span>
                      </div>
                      <div className="w-full bg-zinc-200 dark:bg-zinc-800 rounded-full h-2">
                        <div
                          className="bg-red-600 h-2 rounded-full transition-all"
                          style={{ width: `${data.total > 0 ? (data.escalations / data.total) * 100 : 0}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {!loading && !error && !metrics && (
          <div className="text-center py-20">
            <svg className="w-16 h-16 text-zinc-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p className="text-zinc-600 dark:text-zinc-400">No metrics available for this date</p>
          </div>
        )}

        {/* Customer Lookup Section */}
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-6 border border-zinc-200 dark:border-zinc-800">
          <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-zinc-600 dark:text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Customer Lookup
          </h2>
          <form onSubmit={handleLookup} className="flex gap-3 mb-4">
            <input
              type="text"
              value={lookupQuery}
              onChange={(e) => setLookupQuery(e.target.value)}
              placeholder="Search by email or phone number..."
              className="flex-1 px-4 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-zinc-500 focus:border-transparent"
            />
            <button
              type="submit"
              disabled={lookupLoading || !lookupQuery.trim()}
              className="px-5 py-2 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-lg font-medium hover:bg-zinc-800 dark:hover:bg-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {lookupLoading ? (
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              )}
              Search
            </button>
          </form>

          {lookupError && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 text-sm text-red-700 dark:text-red-300">
              {lookupError}
            </div>
          )}

          {lookupResult && (
            <div className="bg-zinc-50 dark:bg-zinc-800 rounded-xl p-5 border border-zinc-200 dark:border-zinc-700">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {lookupResult.name && (
                  <div>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-1">Name</p>
                    <p className="font-semibold text-zinc-900 dark:text-zinc-100">{lookupResult.name}</p>
                  </div>
                )}
                {lookupResult.email && (
                  <div>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-1">Email</p>
                    <p className="font-semibold text-zinc-900 dark:text-zinc-100">{lookupResult.email}</p>
                  </div>
                )}
                {lookupResult.phone && (
                  <div>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-1">Phone</p>
                    <p className="font-semibold text-zinc-900 dark:text-zinc-100">{lookupResult.phone}</p>
                  </div>
                )}
                {lookupResult.total_tickets !== undefined && (
                  <div>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-1">Total Tickets</p>
                    <p className="font-semibold text-zinc-900 dark:text-zinc-100">{lookupResult.total_tickets}</p>
                  </div>
                )}
                {lookupResult.last_ticket_id && (
                  <div>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-1">Last Ticket ID</p>
                    <Link
                      href={`/process?ticket=${lookupResult.last_ticket_id}`}
                      className="font-semibold text-blue-600 dark:text-blue-400 hover:underline font-mono text-sm"
                    >
                      {lookupResult.last_ticket_id.slice(0, 16)}...
                    </Link>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
