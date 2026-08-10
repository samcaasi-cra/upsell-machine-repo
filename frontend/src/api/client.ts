import type {
  Customer,
  CustomerCreate,
  CustomerOverview,
  CustomerSummary,
  DecisionMakerRecord,
  NewsRecord,
  OpportunityBoardResponse,
} from "../types";

// Set VITE_API_BASE_URL at build time to point at a deployed backend; falls back to
// the local dev server so nothing needs configuring to work locally.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const TOKEN_KEY = "upsell-machine-token";

export const authToken = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (token: string) => sessionStorage.setItem(TOKEN_KEY, token),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};

/** Raised on a 401 so the app can drop back to the login screen. */
export class UnauthorizedError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = authToken.get();
  const resp = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (resp.status === 401) {
    authToken.clear();
    throw new UnauthorizedError("Session expired — please sign in again.");
  }
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}

export const api = {
  checkHealth: () => request<{ status: string; auth_required: boolean; csm_name: string }>("/health"),
  login: (password: string) =>
    request<{ token: string; auth_required: boolean }>("/login", {
      method: "POST",
      body: JSON.stringify({ password }),
    }),
  listSignals: () => request<CustomerSummary[]>("/signals"),
  getOpportunityBoard: (includeConcepts = false) =>
    request<OpportunityBoardResponse>(`/opportunities${includeConcepts ? "?include_concepts=true" : ""}`),
  getOverview: (customerId: string) => request<CustomerOverview>(`/customers/${customerId}/overview`),
  createCustomer: (payload: CustomerCreate) =>
    request<Customer>("/customers", { method: "POST", body: JSON.stringify(payload) }),
  syncFromPortfolio: () =>
    request<{ added: Customer[]; added_count: number; portfolio_size: number }>(
      "/customers/sync-from-portfolio",
      { method: "POST" }
    ),
  getDecisionMakerPrompt: (customerId: string) =>
    request<{ prompt: string }>(`/customers/${customerId}/decision-makers/prompt`),
  importDecisionMakers: (customerId: string, text: string) =>
    request<DecisionMakerRecord>(`/customers/${customerId}/decision-makers/import`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  getNewsPrompt: (customerId: string) => request<{ prompt: string }>(`/customers/${customerId}/news/prompt`),
  importNews: (customerId: string, text: string) =>
    request<NewsRecord>(`/customers/${customerId}/news/import`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  getCapabilities: () => request<{ auto_research: boolean }>("/capabilities"),
  getAgentStatus: () => request<{ enabled: boolean; provider: string | null }>("/agent/status"),
  getToday: (refresh = false) =>
    request<{
      date: string;
      generated_at: string;
      priorities: {
        customer: string;
        headline: string;
        why: string;
        action: string;
        email_subject: string;
        email_body: string;
      }[];
      tokens: { prompt: number; completion: number };
      tool_calls: string[];
      pseudonymised: boolean;
      error?: string;
    }>(`/today${refresh ? "?refresh=true" : ""}`),
  agentChat: (messages: { role: string; content: string }[]) =>
    request<{
      reply: string;
      tool_calls: { tool: string; arguments: Record<string, unknown> }[];
      tokens: { prompt: number; completion: number };
      provider: string;
      model: string;
    }>("/agent/chat", { method: "POST", body: JSON.stringify({ messages }) }),
  getResearchStatus: () =>
    request<{
      enabled: boolean;
      running: boolean;
      last_run_at: string | null;
      last_result: { events_added: number; customers_processed: number } | null;
      due_today: boolean;
    }>("/research-status"),
  runResearchNow: () => request<{ status: string; detail?: string }>("/research-run-now", { method: "POST" }),
  autoResearchDecisionMakers: (customerId: string) =>
    request<DecisionMakerRecord>(`/customers/${customerId}/decision-makers/auto-research`, { method: "POST" }),
  autoResearchNews: (customerId: string) =>
    request<NewsRecord>(`/customers/${customerId}/news/auto-research`, { method: "POST" }),
};
