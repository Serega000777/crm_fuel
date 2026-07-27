export type Fuel = { id:string; name:string; code:string; stock_liters:string; sale_price_kopecks:number; average_cost_kopecks:number; minimum_stock_liters:string; color:string };
export type Dashboard = { revenue_kopecks:number; gross_profit_kopecks:number; cash_balance_kopecks:number; total_stock_liters:string; fuels:Fuel[] };
const base = import.meta.env.VITE_API_URL || "http://localhost:8000";
const initData = window.Telegram?.WebApp?.initData;
const authHeaders = (): Record<string,string> => initData ? { Authorization:`tma ${initData}` } : { "X-Dev-User":"1" };
async function request<T>(path:string, options:RequestInit={}):Promise<T> {
  const response = await fetch(`${base}${path}`, { ...options, headers:{ "Content-Type":"application/json", ...authHeaders(), ...options.headers } });
  if (!response.ok) { const body = await response.json().catch(()=>null); throw new Error(body?.detail || "Не удалось выполнить операцию"); }
  return response.json();
}
export const api = {
  dashboard:()=>request<Dashboard>("/api/v1/dashboard"),
  price:(id:string, value:number)=>request<Fuel>(`/api/v1/fuels/${id}/price`,{method:"PATCH",body:JSON.stringify({sale_price_kopecks:value})}),
  purchase:(payload:object)=>request("/api/v1/purchases",{method:"POST",headers:{"Idempotency-Key":crypto.randomUUID()},body:JSON.stringify(payload)}),
  sale:(payload:object)=>request("/api/v1/sales",{method:"POST",headers:{"Idempotency-Key":crypto.randomUUID()},body:JSON.stringify(payload)}),
};
declare global { interface Window { Telegram?: { WebApp?: { initData?:string; ready():void; expand():void } } } }

