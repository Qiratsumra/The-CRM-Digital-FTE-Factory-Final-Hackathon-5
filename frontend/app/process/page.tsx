"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { getTicket, processTicket } from "@/lib/api";

function ProcessTicketContent() {
  const searchParams = useSearchParams();
  const [ticketId, setTicketId] = useState("");
  const [ticket, setTicket] = useState<{
    ticket_id: string;
    status: string;
    channel: string;
    category?: string;
    priority?: string;
    created_at: string;
    last_updated: string;
    whatsapp_only?: boolean;
  } | null>(null);
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState(0);

  // Track processing time
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (processing) {
      interval = setInterval(() => {
        setProcessingTime(prev => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [processing]);

  useEffect(() => {
    const ticketParam = searchParams.get("ticket");
    if (ticketParam) {
      setTicketId(ticketParam);
      setTimeout(() => {
        document.querySelector("form")?.requestSubmit();
      }, 500);
    }
  }, [searchParams]);

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketId.trim()) return;

    setLoading(true);
    setError(null);
    setTicket(null);
    setAiResponse(null);

    try {
      const data = await getTicket(ticketId.trim());
      setTicket(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch ticket");
    } finally {
      setLoading(false);
    }
  };

  const handleProcess = async () => {
    if (!ticket) return;

    setProcessing(true);
    setError(null);

    try {
      console.log('[ProcessPage] Processing ticket:', ticket.ticket_id);
      const data = await processTicket(ticket.ticket_id);
      console.log('[ProcessPage] AI response received:', data);
      setAiResponse(data.response);
      setTicket({ ...ticket, status: data.status });
    } catch (err) {
      console.error('[ProcessPage] Processing error:', err);
      setError(err instanceof Error ? err.message : "Failed to process ticket");
    } finally {
      setProcessing(false);
    }
  };

  const getChannelInfo = (channel: string) => {
    switch (channel) {
      case "email":
        return {
          name: "Email",
          icon: (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z" />
            </svg>
          ),
          color: "red",
          bgColor: "bg-red-100 dark:bg-red-900/30",
          textColor: "text-red-600 dark:text-red-400",
          borderColor: "border-red-200 dark:border-red-900",
        };
      case "whatsapp":
        return {
          name: "WhatsApp",
          icon: (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z" />
            </svg>
          ),
          color: "green",
          bgColor: "bg-green-100 dark:bg-green-900/30",
          textColor: "text-green-600 dark:text-green-400",
          borderColor: "border-green-200 dark:border-green-900",
        };
      default:
        return {
          name: "Web Form",
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          ),
          color: "zinc",
          bgColor: "bg-zinc-100 dark:bg-zinc-800",
          textColor: "text-zinc-600 dark:text-zinc-400",
          borderColor: "border-zinc-200 dark:border-zinc-800",
        };
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "resolved":
        return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400";
      case "escalated":
        return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
      case "pending":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400";
      default:
        return "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-400";
    }
  };

  const channelInfo = ticket ? getChannelInfo(ticket.channel) : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-50 to-zinc-100 dark:from-zinc-950 dark:to-zinc-900">
      <header className="bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm border-b border-zinc-200 dark:border-zinc-800 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Link href="/" className="text-sm text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100">
            ← Back to Home
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-zinc-900 dark:text-zinc-100 mb-4">
            Track Your Ticket
          </h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            Enter your ticket ID to check status and get AI responses
          </p>
        </div>

        {/* Lookup Form */}
        <div className="bg-white dark:bg-zinc-900 rounded-3xl p-8 border-2 border-zinc-200 dark:border-zinc-800 mb-8">
          <form onSubmit={handleLookup} className="space-y-4">
            <div>
              <label htmlFor="ticketId" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                Ticket ID
              </label>
              <div className="flex gap-3">
                <input
                  type="text"
                  id="ticketId"
                  value={ticketId}
                  onChange={(e) => setTicketId(e.target.value)}
                  className="flex-1 px-4 py-3 bg-zinc-50 dark:bg-zinc-800 border-2 border-zinc-200 dark:border-zinc-700 rounded-xl focus:outline-none focus:border-zinc-500 transition-colors font-mono"
                  placeholder="Enter your ticket ID"
                />
                <button
                  type="submit"
                  disabled={loading || !ticketId.trim()}
                  className="px-6 py-3 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-xl font-semibold hover:bg-zinc-800 dark:hover:bg-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {loading ? (
                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  ) : (
                    "Lookup"
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-6 mb-8">
            <div className="flex items-start gap-3">
              <svg className="w-6 h-6 text-red-600 dark:text-red-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h3 className="font-semibold text-red-900 dark:text-red-100 mb-2">Error</h3>
                <p className="text-red-700 dark:text-red-300">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Ticket Details */}
        {ticket && (
          <div className={`bg-white dark:bg-zinc-900 rounded-3xl p-8 border-2 ${channelInfo?.borderColor} mb-8`}>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 ${channelInfo?.bgColor} ${channelInfo?.textColor} rounded-xl flex items-center justify-center`}>
                  {channelInfo?.icon}
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
                    Ticket {ticket.ticket_id.slice(0, 8)}...
                  </h2>
                  <div className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md ${channelInfo?.bgColor} ${channelInfo?.textColor}`}>
                      {channelInfo?.icon}
                      {channelInfo?.name}
                    </span>
                    <span>•</span>
                    <span className={`px-2 py-1 rounded-md ${getStatusColor(ticket.status)}`}>
                      {ticket.status}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-4 mb-6">
              <div className="bg-zinc-50 dark:bg-zinc-800 rounded-xl p-4">
                <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-1">Category</p>
                <p className="font-medium text-zinc-900 dark:text-zinc-100">{ticket.category || "N/A"}</p>
              </div>
              <div className="bg-zinc-50 dark:bg-zinc-800 rounded-xl p-4">
                <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-1">Priority</p>
                <p className="font-medium text-zinc-900 dark:text-zinc-100 capitalize">{ticket.priority || "N/A"}</p>
              </div>
              <div className="bg-zinc-50 dark:bg-zinc-800 rounded-xl p-4">
                <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-1">Created</p>
                <p className="font-medium text-zinc-900 dark:text-zinc-100">
                  {new Date(ticket.created_at).toLocaleString()}
                </p>
              </div>
              <div className="bg-zinc-50 dark:bg-zinc-800 rounded-xl p-4">
                <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-1">Last Updated</p>
                <p className="font-medium text-zinc-900 dark:text-zinc-100">
                  {new Date(ticket.last_updated).toLocaleString()}
                </p>
              </div>
            </div>

            {/* WhatsApp-only notice */}
            {ticket.whatsapp_only && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4 mb-6">
                <div className="flex items-start gap-3">
                  <svg className="w-6 h-6 text-green-600 dark:text-green-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="flex-1">
                    <h3 className="font-semibold text-green-900 dark:text-green-100 mb-1">
                      WhatsApp-Only Conversation
                    </h3>
                    <p className="text-sm text-green-700 dark:text-green-300">
                      This conversation is only available on WhatsApp for privacy and security. 
                      Check your WhatsApp app to view the full message history and responses.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {ticket.status === "pending" && (
              <button
                onClick={handleProcess}
                disabled={processing}
                className={`w-full inline-flex items-center justify-center gap-2 px-6 py-4 rounded-xl font-semibold text-lg transition-all ${
                  channelInfo?.color === "red"
                    ? "bg-red-600 hover:bg-red-700 text-white"
                    : channelInfo?.color === "green"
                    ? "bg-green-600 hover:bg-green-700 text-white"
                    : "bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {processing ? (
                  <>
                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Processing... {Math.floor(processingTime / 60)}m {processingTime % 60}s elapsed
                  </>
                ) : (
                  <>
                    <svg className="w-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Generate AI Response
                  </>
                )}
              </button>
            )}

            {processing && (
              <div className="mt-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                <div className="flex items-center gap-3">
                  <div className="animate-pulse w-3 h-3 bg-blue-500 rounded-full"></div>
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    <strong>AI is processing your ticket...</strong>
                    {processingTime < 30 && " (Backend is likely starting up)"}
                    {processingTime >= 30 && processingTime < 60 && " (Waking up backend...)"}
                    {processingTime >= 60 && " (Generating AI response...)"}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* AI Response */}
        {aiResponse && (
          <div className={`bg-white dark:bg-zinc-900 rounded-3xl p-8 border-2 ${channelInfo?.borderColor}`}>
            <div className="flex items-center gap-3 mb-6">
              <div className={`w-10 h-10 ${channelInfo?.bgColor} ${channelInfo?.textColor} rounded-xl flex items-center justify-center`}>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">AI Response</h3>
            </div>

            <div className="bg-zinc-50 dark:bg-zinc-800 rounded-xl p-6 mb-6">
              <p className="text-zinc-900 dark:text-zinc-100 whitespace-pre-wrap leading-relaxed">
                {aiResponse}
              </p>
            </div>

            <div className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400 mb-6">
              <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Response sent via {channelInfo?.name}
            </div>

            <div className="flex gap-3">
              <Link
                href="/"
                className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-4 bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-xl font-semibold hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-all"
              >
                Back to Home
              </Link>
              <Link
                href={`/support/${ticket?.channel === "email" ? "email" : ticket?.channel === "whatsapp" ? "whatsapp" : "webform"}`}
                className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-4 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-xl font-semibold hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-all"
              >
                Submit Another
              </Link>
            </div>
          </div>
        )}

        {/* Help Text */}
        {!ticket && !aiResponse && (
          <div className="text-center text-zinc-600 dark:text-zinc-400">
            <p className="text-sm">
              Don&apos;t have a ticket ID?{" "}
              <Link href="/" className="text-zinc-900 dark:text-zinc-100 font-medium hover:underline">
                Submit a new ticket
              </Link>
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

function ProcessTicketPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-zinc-50 to-zinc-100 dark:from-zinc-950 dark:to-zinc-900 flex items-center justify-center">
        <div className="text-center">
          <svg className="animate-spin h-10 w-10 mx-auto mb-4 text-zinc-600" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-zinc-600 dark:text-zinc-400">Loading...</p>
        </div>
      </div>
    }>
      <ProcessTicketContent />
    </Suspense>
  );
}

export default ProcessTicketPage;
