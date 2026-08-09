import type {
  Customer,
  CustomerCreate,
  CustomerOverview,
  CustomerSummary,
  DecisionMakerRecord,
  NewsRecord,
  OpportunityBoardResponse,
} from "../types";

const BASE_URL = "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
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
  listSignals: () => request<CustomerSummary[]>("/signals"),
  getOpportunityBoard: () => request<OpportunityBoardResponse>("/opportunities"),
  getOverview: (customerId: string) => request<CustomerOverview>(`/customers/${customerId}/overview`),
  createCustomer: (payload: CustomerCreate) =>
    request<Customer>("/customers", { method: "POST", body: JSON.stringify(payload) }),
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
};
