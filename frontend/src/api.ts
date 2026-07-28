export type Fuel = {
  id: string;
  name: string;
  code: string;
  stock_liters: string;
  sale_price_kopecks: number;
  average_cost_kopecks: number;
  minimum_stock_liters: string;
  color: string;
};
export type Dashboard = {
  revenue_kopecks: number;
  gross_profit_kopecks: number;
  expenses_kopecks: number;
  net_profit_kopecks: number;
  cash_balance_kopecks: number;
  total_stock_liters: string;
  fuels: Fuel[];
};
export type Operation = {
  id: string;
  type: string;
  fuel_id: string | null;
  total_kopecks: number;
  cost_kopecks: number;
  liters: string | null;
  payment_method: string | null;
  description: string | null;
  reversal_of_id: string | null;
  created_at: string;
};
export type PurchaseAnalysis = {
  fuel_cost_kopecks: number;
  additional_cost_kopecks: number;
  landed_cost_kopecks: number;
  batch_cost_per_liter_kopecks: number;
  projected_average_cost_kopecks: number;
  sale_price_kopecks: number;
  projected_margin_per_liter_kopecks: number;
  projected_margin_basis_points: number;
  profitable: boolean;
  analysis_source: "local_rules";
  advisory: {
    summary: string;
    risks: string[];
    recommendation: string;
  };
};
export type PeriodReport = {
  date_from: string;
  date_to: string;
  revenue_kopecks: number;
  cogs_kopecks: number;
  gross_profit_kopecks: number;
  expenses_kopecks: number;
  net_profit_kopecks: number;
  cash_flow_kopecks: number;
  purchased_liters: string;
  sold_liters: string;
  operations_count: number;
  fuel_details: {
    fuel_id: string;
    fuel_name: string;
    purchased_liters: string;
    sold_liters: string;
    revenue_kopecks: number;
    cogs_kopecks: number;
    gross_profit_kopecks: number;
  }[];
};
const base = import.meta.env.VITE_API_URL || "http://localhost:8000";
const initData = window.Telegram?.WebApp?.initData;
const authHeaders = (): Record<string, string> =>
  initData ? { Authorization: `tma ${initData}` } : { "X-Dev-User": "1" };
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    ...options,
    signal: options.signal || AbortSignal.timeout(15_000),
    headers: { "Content-Type": "application/json", ...authHeaders(), ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || "Не удалось выполнить операцию");
  }
  return response.json();
}
export function parseKopecks(value: string): number {
  const normalized = value.trim().replace(",", ".");
  if (!/^\d+(?:\.\d{1,2})?$/.test(normalized))
    throw new Error("Введите сумму с точностью до копеек");
  const [rubles, kopecks = ""] = normalized.split(".");
  const result = BigInt(rubles) * 100n + BigInt(kopecks.padEnd(2, "0"));
  if (result > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error("Сумма слишком велика");
  return Number(result);
}
export const api = {
  dashboard: () => request<Dashboard>("/api/v1/dashboard"),
  price: (id: string, value: number) =>
    request<Fuel>(`/api/v1/fuels/${id}/price`, {
      method: "PATCH",
      body: JSON.stringify({ sale_price_kopecks: value }),
    }),
  minimumStock: (id: string, value: string) =>
    request<Fuel>(`/api/v1/fuels/${id}/minimum-stock`, {
      method: "PATCH",
      body: JSON.stringify({ minimum_stock_liters: value }),
    }),
  purchase: (payload: object) =>
    request("/api/v1/purchases", {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify(payload),
    }),
  analyzePurchase: (payload: object) =>
    request<PurchaseAnalysis>("/api/v1/purchases/analyze", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  sale: (payload: object) =>
    request("/api/v1/sales", {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify(payload),
    }),
  adjustInventory: (payload: object) =>
    request("/api/v1/inventory/adjustments", {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify(payload),
    }),
  expense: (payload: object) =>
    request("/api/v1/expenses", {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify(payload),
    }),
  collect: (payload: object) =>
    request("/api/v1/collections", {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify(payload),
    }),
  operations: (offset = 0, operationType = "") =>
    request<Operation[]>(
      `/api/v1/operations?limit=50&offset=${offset}${
        operationType ? `&operation_type=${encodeURIComponent(operationType)}` : ""
      }`,
    ),
  report: (dateFrom: string, dateTo: string) =>
    request<PeriodReport>(
      `/api/v1/reports/period?date_from=${encodeURIComponent(dateFrom)}&date_to=${encodeURIComponent(dateTo)}`,
    ),
  exportReport: async (dateFrom: string, dateTo: string) => {
    const response = await fetch(
      `${base}/api/v1/reports/period.csv?date_from=${encodeURIComponent(dateFrom)}&date_to=${encodeURIComponent(dateTo)}`,
      { headers: authHeaders(), signal: AbortSignal.timeout(15_000) },
    );
    if (!response.ok) throw new Error("Не удалось выгрузить отчёт");
    const link = document.createElement("a");
    link.href = URL.createObjectURL(await response.blob());
    link.download = `crm-fuel-${dateFrom}-${dateTo}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  },
  reverse: (id: string, reason: string) =>
    request(`/api/v1/operations/${id}/reversal`, {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify({ reason }),
    }),
};
declare global {
  interface Window {
    Telegram?: { WebApp?: { initData?: string; ready(): void; expand(): void } };
  }
}
