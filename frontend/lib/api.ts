/**
 * Centralized API client for the Customer Success FTE backend.
 * Backend: https://crm-digital-fte-factory-final-hackathon.onrender.com
 * API Docs: https://crm-digital-fte-factory-final-hackathon.onrender.com/docs
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL?.trim() || "https://crm-digital-fte-factory-final-hackathon.onrender.com";

// Log the base URL in development mode for debugging
if (process.env.NODE_ENV === 'development') {
  console.log('[API Client] Using BASE_URL:', BASE_URL);
}

// ─── Types ───────────────────────────────────────────────────────────────────


export interface SupportFormData {
  name: string;
  email: string;
  subject: string;
  category: string;
  priority: string;
  message: string;
  channel?: string;
}

export interface TicketResponse {
  ticket_id: string;
  status: string;
  channel: string;
  category?: string;
  priority?: string;
  created_at: string;
  last_updated: string;
  whatsapp_only?: boolean;
}

export interface AgentProcessResponse {
  ticket_id: string;
  status: string;
  response: string;
  channel: string;
}

export interface ChannelMetrics {
  total: number;
  avg_sentiment: number;
  escalations: number;
  avg_response_time_sec: number;
}

export interface MetricsResponse {
  email?: ChannelMetrics;
  whatsapp?: ChannelMetrics;
  web_form?: ChannelMetrics;
}

export interface CustomerLookupResponse {
  email?: string;
  name?: string;
  phone?: string;
  total_tickets?: number;
  last_ticket_id?: string;
  [key: string]: unknown;
}

export interface HealthResponse {
  status: string;
  [key: string]: unknown;
}

export interface WhatsAppWebhookData {
  phone: string;
  message: string;
}

export interface WhatsAppWebhookResponse {
  ticket_id: string;
  response?: string;
  [key: string]: unknown;
}

export interface EmailWebhookData {
  from: string;
  subject: string;
  body: string;
  channel: string;
}

export interface EmailWebhookResponse {
  ticket_id: string;
  response?: string;
  [key: string]: unknown;
}

export interface AgentProcessBatchRequest {
  ticket_ids?: string[];
}

export interface AgentProcessBatchResponse {
  processed_count: number;
  results: Array<{
    ticket_id: string;
    status: string;
    response?: string;
    error?: string;
  }>;
}

// ─── API Helpers ─────────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  // Remove leading slash from path to avoid double slashes
  const cleanPath = path.startsWith('/') ? path.substring(1) : path;
  // Remove trailing slash from base URL
  const cleanBase = BASE_URL.endsWith('/') ? BASE_URL.slice(0, -1) : BASE_URL;
  const url = `${cleanBase}/${cleanPath}`;

  if (process.env.NODE_ENV === 'development') {
    console.log(`[API Client] Fetching: ${url}`);
    console.log('[API Client] Options:', options);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 120000); // 120s timeout (Render cold start + AI processing)

  try {
    const res = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string>),
      },
      ...options,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // Log response for debugging
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API Client] Response: ${res.status} ${res.statusText}`);
      console.log('[API Client] Response headers:', Object.fromEntries(res.headers.entries()));
    }

    if (!res.ok) {
      let message = `Request failed: ${res.status} ${res.statusText}`;
      try {
        const text = await res.text();
        if (process.env.NODE_ENV === 'development') {
          console.log('[API Client] Error response text:', text || '(empty)');
        }
        if (text) {
          try {
            const errorBody = JSON.parse(text);
            const hasContent = errorBody && Object.keys(errorBody).length > 0;
            if (process.env.NODE_ENV === 'development') {
              if (hasContent) {
                console.error('[API Client] Error body:', errorBody);
              } else {
                console.warn('[API Client] Error body: empty response from server');
              }
            }
            if (errorBody?.detail) {
              message = Array.isArray(errorBody.detail)
                ? errorBody.detail.map((d: { msg: string }) => d.msg).join(", ")
                : String(errorBody.detail);
            } else if (errorBody?.message) {
              message = errorBody.message;
            } else if (errorBody?.error) {
              message = errorBody.error;
            } else if (!hasContent) {
              message = `Request failed: ${res.status} ${res.statusText} (no error details provided)`;
            }
          } catch {
            // If JSON parse fails, use the text directly
            if (process.env.NODE_ENV === 'development') {
              console.error('[API Client] Error text (not JSON):', text);
            }
            message = text || message;
          }
        }
      } catch (parseError) {
        // ignore parse errors, use default message
        if (process.env.NODE_ENV === 'development') {
          console.error('[API Client] Error parsing response:', parseError);
        }
      }
      throw new Error(message);
    }

    const data = await res.json() as Promise<T>;

    if (process.env.NODE_ENV === 'development') {
      console.log('[API Client] Data:', data);
    }

    return data;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timed out. The backend may be starting up (cold start). Please try again.');
    }
    throw error;
  }
}

// ─── API Functions ────────────────────────────────────────────────────────────

/** GET / — Root */
export async function checkRoot(): Promise<unknown> {
  return apiFetch("/");
}

/** GET /health — Health check */
export async function checkHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

/** POST /support/submit — Submit a support ticket */
export async function submitTicket(data: SupportFormData): Promise<{ ticket_id: string }> {
  return apiFetch<{ ticket_id: string }>("/support/submit", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** GET /support/ticket/{ticket_id} — Get ticket status */
export async function getTicket(ticketId: string): Promise<TicketResponse> {
  return apiFetch<TicketResponse>(`/support/ticket/${encodeURIComponent(ticketId)}`);
}

/** POST /agent/process/{ticket_id} — Process ticket with AI agent */
export async function processTicket(ticketId: string): Promise<AgentProcessResponse> {
  return apiFetch<AgentProcessResponse>(`/agent/process/${encodeURIComponent(ticketId)}`, {
    method: "POST",
    headers: {
      // Send API key for protected endpoints
      "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "dev-api-key",
    },
  });
}

/** POST /agent/process-batch — Process all pending tickets */
export async function processBatch(): Promise<unknown> {
  return apiFetch("/agent/process-batch", { method: "POST" });
}

/** GET /metrics/channels — Get channel metrics */
export async function getMetrics(date?: string, apiKey?: string): Promise<MetricsResponse> {
  const params = new URLSearchParams();
  if (date) params.set("date", date);
  const query = params.toString() ? `?${params.toString()}` : "";

  return apiFetch<MetricsResponse>(`/metrics/channels${query}`, {
    headers: apiKey ? { "X-API-Key": apiKey } : {},
  });
}

/** GET /customers/lookup — Look up a customer */
export async function lookupCustomer(query: string): Promise<CustomerLookupResponse> {
  const params = new URLSearchParams({ query });
  return apiFetch<CustomerLookupResponse>(`/customers/lookup?${params.toString()}`);
}

/** POST /webhooks/whatsapp/mcp — WhatsApp MCP Webhook */
export async function sendWhatsAppMessage(data: WhatsAppWebhookData): Promise<WhatsAppWebhookResponse> {
  return apiFetch<WhatsAppWebhookResponse>("/webhooks/whatsapp/mcp", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** GET /webhooks/whatsapp/status — WhatsApp MCP Status */
export async function getWhatsAppStatus(): Promise<unknown> {
  return apiFetch("/webhooks/whatsapp/status");
}

/** POST /webhooks/gmail — Gmail Webhook (Email support) */
export async function sendEmailWebhook(data: EmailWebhookData): Promise<EmailWebhookResponse> {
  return apiFetch<EmailWebhookResponse>("/webhooks/gmail", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** POST /webhooks/whatsapp/rep — WhatsApp MCP Webhook (Alternative endpoint) */
export async function sendWhatsAppWebhook(data: WhatsAppWebhookData): Promise<WhatsAppWebhookResponse> {
  return apiFetch<WhatsAppWebhookResponse>("/webhooks/whatsapp/rep", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** GET /webhooks/whatsapp/rep/status — WhatsApp MCP Rep Status */
export async function getWhatsAppRepStatus(): Promise<unknown> {
  return apiFetch("/webhooks/whatsapp/rep/status");
}