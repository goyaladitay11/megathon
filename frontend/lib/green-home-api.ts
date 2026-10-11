const BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export type Property = { property_id: string; property_type: string; age: number; floor_area_m2: number; region: string; energy_rating: string; heating: string; insulation: string; glazing: string; annual_electricity_kwh?: number | null; annual_gas_kwh?: number | null };
export type Explanation = { summary: string; reasons: string[]; tradeoffs: string[]; limitations: string[] };
export type Energy = { baseline_electricity_kwh: number; baseline_gas_kwh: number; after_electricity_kwh: number; after_gas_kwh: number; total_purchased_energy_savings_kwh: number; improvement_potential_percent: number | null; };
export type Carbon = { net_carbon_saving_tonnes: number };
export type Valuation = { is_available: boolean; uplift_range_label: string; indicative_value_min_gbp: number | null; indicative_value_max_gbp: number | null; caveat: string; unavailable_reason: string | null; };
export type ChatResponse = { property_id: string; scenario_recognized: string; parsed_retrofit_ids: string[]; unsupported_requested_items: string[]; explanation: Explanation; simulated_energy: Energy | null; simulated_carbon: Carbon | null; simulated_valuation: Valuation | null; grounding_verified: boolean; engine_used: string };
export type Analysis = { score_details: { final_score: number; classification: string; components: { component_name: string; contribution: number; weight: number }[] }; key_issue_flags: string[]; data_quality_warnings: string[] };
async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, { cache: 'no-store', ...init });
  if (!response.ok) {
    let reason = '';
    try { const body = await response.json(); reason = JSON.stringify(body.detail || body).slice(0, 350); } catch { /* response has no JSON */ }
    throw new Error(`API ${response.status}${reason ? ': ' + reason : ''}`);
  }
  return response.json() as Promise<T>;
}
export const getProperties = () => json<Property[]>('/api/v1/properties');
export const analyze = (property: Property) => json<Analysis>('/api/v1/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(property) });
export const chat = (property_id: string, query: string, selected_retrofit_ids?: string[]) => json<ChatResponse>('/api/v1/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ property_id, query, ...(selected_retrofit_ids?.length ? { selected_retrofit_ids } : {}) }) });
