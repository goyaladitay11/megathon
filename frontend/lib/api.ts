import type { Property, Scenario, Upgrade } from "./model";

/** Frontend handoff seam. Your backend developer can implement these functions later. */
export const live = false;

export type PortfolioRow = {
  property: Property;
  baseline: Scenario;
  package: Scenario;
  selected: Upgrade[];
};

const connectionRequired = (signal?: AbortSignal): never => {
  if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
  throw new Error(
    "This is the standalone frontend preview. Connect your backend to supply custom property results and explanations.",
  );
};

export async function assessProperty(
  _property: Property,
  _profile?: unknown,
  signal?: AbortSignal,
): Promise<Scenario> {
  return connectionRequired(signal);
}

export async function runScenario(
  _property: Property,
  _selected: Upgrade[],
  _assessment: Scenario,
  _question?: string,
  signal?: AbortSignal,
): Promise<Scenario> {
  return connectionRequired(signal);
}

export async function explainScenario(
  _property: Property,
  _scenario: Scenario,
  _query: string,
  signal?: AbortSignal,
): Promise<{ message: string; scenario?: Scenario }> {
  return connectionRequired(signal);
}

export async function loadPortfolio(
  signal?: AbortSignal,
): Promise<{ rows: PortfolioRow[]; warnings: string[] }> {
  return connectionRequired(signal);
}
