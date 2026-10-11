// Display contracts only. Scores, savings, carbon and value estimates are supplied by the backend.
export type Upgrade =
  "insulation" | "glazing" | "heat_pump" | "solar" | "thermostat";
export type Property = {
  id: string;
  name: string;
  region: string;
  type: string;
  yearBuilt: number;
  floorArea: number;
  bedrooms: number;
  epcRating: string;
  electricityKwh: number;
  gasKwh: number;
  currentValue: number;
  budget: number;
  roofAccess: boolean;
  customerId?: string;
  insulation?: "poor" | "average" | "good";
  heating?: "gas_boiler" | "electric_resistive" | "oil_boiler" | "heat_pump";
  glazing?: "single" | "double" | "triple";
  solar?: "none" | "2kw" | "4kw";
  smartControls?: boolean;
};
export function isProperty(value: unknown): value is Property {
  if (!value || typeof value !== "object") return false;
  const p = value as Property;
  return (
    [p.id, p.name, p.region, p.type].every(
      (v) => typeof v === "string" && Boolean(v.trim()),
    ) &&
    Number.isInteger(p.yearBuilt) &&
    p.yearBuilt >= 1800 &&
    p.yearBuilt <= new Date().getFullYear() &&
    Number.isFinite(p.floorArea) &&
    p.floorArea > 10 &&
    p.floorArea < 1000 &&
    Number.isInteger(p.bedrooms) &&
    p.bedrooms >= 1 &&
    p.bedrooms <= 10 &&
    typeof p.epcRating === "string" &&
    /^[A-G]$/.test(p.epcRating) &&
    [p.electricityKwh, p.gasKwh, p.currentValue, p.budget].every(
      (n) => Number.isFinite(n) && n >= 0,
    ) &&
    typeof p.roofAccess === "boolean"
  );
}
export type StructuredDraft = {
  scenarioId: string;
  summary: string;
  sections: {
    id: string;
    title: string;
    body: string;
    evidenceIds?: string[];
  }[];
  why: { title: string; body: string; evidenceIds?: string[] }[];
  limitations: string[];
};
export type Scenario = {
  id: string;
  propertyId: string;
  mode: "demo" | "live";
  selectedRetrofits: Upgrade[];
  score: number;
  classification: string;
  components: {
    id: string;
    label: string;
    weight: number;
    score: number;
    reason: string;
    contribution?: number | null;
  }[];
  electricityKwh: number;
  gasKwh: number;
  purchasedEnergyKwh: number;
  electricitySavingKwh: number;
  gasSavingKwh: number;
  baselineElectricityKwh?: number | null;
  baselineGasKwh?: number | null;
  baselinePurchasedEnergyKwh?: number | null;
  baselineValue?: number | null;
  energyIntensityKwhM2?: number | null;
  energySavingKwh?: number | null;
  annualEmissionsKg: number | null;
  carbonReductionKg: number | null;
  improvementPotentialPct: number | null;
  valueLow: number | null;
  valueHigh: number | null;
  valueUpliftLowPct?: number | null;
  valueUpliftHighPct?: number | null;
  projectedEpcRating?: string | null;
  cost: number | null;
  explanation: string;
  assumptions: string[];
  recommendations: {
    id: Upgrade;
    feasible: boolean;
    blockedReason?: string;
    suitability?: "High" | "Medium" | "Low";
    reason?: string;
    priority?: number;
    electricitySavingKwh?: number | null;
    gasSavingKwh?: number | null;
    carbonReductionKg?: number | null;
    cost?: number | null;
    costLow?: number | null;
    costHigh?: number | null;
    notes?: string;
  }[];
  draft?: StructuredDraft;
  draftSource?: "backend" | "sample";
  keyIssues?: string[];
  warnings?: string[];
  carbonSource?: string;
  valueCaveat?: string;
  narrativeUnavailableReason?: string;
  currentScoreOnly?: boolean;
};

export const example: Property = {
  id: "demo-home",
  name: "Our family home",
  region: "Bristol",
  type: "semi-detached",
  yearBuilt: 1985,
  floorArea: 120,
  bedrooms: 3,
  epcRating: "E",
  electricityKwh: 4800,
  gasKwh: 12000,
  currentValue: 350000,
  budget: 18000,
  roofAccess: true,
  insulation: "poor",
  heating: "gas_boiler",
  glazing: "single",
  solar: "none",
  smartControls: false,
};

export const upgrades: {
  id: Upgrade;
  label: string;
  cost: number;
  description: string;
}[] = [
  {
    id: "insulation",
    label: "Loft insulation",
    cost: 1400,
    description: "Keep the warmth where it belongs.",
  },
  {
    id: "glazing",
    label: "Double glazing",
    cost: 5200,
    description: "A quieter, cosier view of the world.",
  },
  {
    id: "heat_pump",
    label: "Air-source heat pump",
    cost: 8500,
    description: "A different way to heat your home.",
  },
  {
    id: "solar",
    label: "Solar panels",
    cost: 6100,
    description: "Let a little sunshine power your day.",
  },
  {
    id: "thermostat",
    label: "Smart thermostat",
    cost: 250,
    description: "Comfort that follows your routine.",
  },
];

export const componentIds = [
  "efficiency",
  "intensity",
  "insulation",
  "heating",
  "glazing",
  "renewables",
  "controls",
];
export const money = (n: number) =>
  new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
  }).format(n);
export const number = (n: number) => Math.round(n).toLocaleString("en-GB");
