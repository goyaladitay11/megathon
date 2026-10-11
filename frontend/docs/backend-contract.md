# Frontend handoff contract

This is a frontend-only handoff for the backend developer. `lib/model.ts` defines the display types, and `lib/api.ts` contains a disabled integration seam. The app currently uses fixed sample illustrations, makes no backend requests and does not implement model calculations or an LLM service. No endpoint names or backend setup are required to run it.

## Functions to implement later

These reserved function signatures are a starting point for integration. The current components read sample data directly and do not call them. Your backend adapter can map your API into these return values; then connect the personal loading, Apply, question and portfolio flows to those functions. The frontend does not prescribe your server routes.

| Function in `lib/api.ts` | Future input and return |
| --- | --- |
| `assessProperty(property, profile?, signal?)` | Receive the complete `Property` and optional name/goal context; return a `Promise<Scenario>` for that property |
| `runScenario(property, selected, assessment, question?, signal?)` | Receive a property, selected `Upgrade[]`, existing assessment and optional question; return a confirmed `Promise<Scenario>` |
| `explainScenario(property, scenario, query, signal?)` | Receive the confirmed scenario and question; return `Promise<{ message: string; scenario?: Scenario }>` |
| `loadPortfolio(signal?)` | Return `Promise<{ rows: PortfolioRow[]; warnings: string[] }>` for the intended business portfolio |

`PortfolioRow` contains `property`, `baseline`, `package` and `selected`. The report types live in `lib/model.ts`. `signal` is an optional `AbortSignal` so changing input or navigating can cancel obsolete work. `live` is currently `false` and is not consumed by the preview components. Changing this constant alone will not connect the UI. Keep the delivery in sample mode until the adapter and component request flows are implemented and verified.

The local name/goal context is `{ displayName: string, goal: "comfort" | "efficiency" | "sell" }`. It supports greetings and stated preferences; it is not a model result. User-entered property details must be sent as a full object when integration is added so outputs can be tied to the right property.

## `Property`

| Fields | Meaning |
| --- | --- |
| `id`, `name`, optional `customerId` | Property identity, display name and optional customer identity |
| `region`, `type`, `yearBuilt`, `floorArea`, `bedrooms` | Location and property characteristics; floor area in m² |
| `epcRating` | Recorded current EPC band A–G |
| `electricityKwh`, `gasKwh` | Annual purchased electricity imports and gas, in kWh/year |
| `currentValue`, `budget`, `roofAccess` | Current value/budget in GBP and stated roof access |
| optional `insulation`, `heating`, `glazing`, `solar`, `smartControls` | Existing features collected by the intake |

Existing feature values are defined in the TypeScript type. Preserve the distinction between measured zero and unavailable observations when adapting a backend that supports missing values. The current homeowner form collects annual observations; do not quietly invent readings or a score for incomplete input.

## `Scenario`

| Fields | Display responsibility |
| --- | --- |
| `id`, `propertyId`, `mode`, `selectedRetrofits` | Identify the confirmed report, its property, sample/live origin and included improvements |
| `score`, `classification`, `components` | Green Home Score and seven component sub-scores, labels, weights, contributions and reasons |
| `baselineElectricityKwh`, `baselineGasKwh`, `baselinePurchasedEnergyKwh` | Explicit baseline values for before/after comparisons |
| `electricityKwh`, `gasKwh`, `purchasedEnergyKwh` | Scenario annual purchased energy in kWh/year |
| `electricitySavingKwh`, `gasSavingKwh`, optional `energySavingKwh` | Signed per-fuel changes and net saving; negative means a consumption increase |
| `energyIntensityKwhM2`, `improvementPotentialPct` | Returned annual intensity and feasible purchased-energy reduction percentage |
| `annualEmissionsKg`, `carbonReductionKg`, `carbonSource` | Annual emissions/reduction in kg CO₂e/year and documented source note |
| `baselineValue`, `valueLow`, `valueHigh`, `valueUpliftLowPct`, `valueUpliftHighPct`, `valueCaveat` | Baseline value, indicative value and percentage ranges, and limitations |
| `cost`, `recommendations` | Package cost in GBP and feasible, prioritised recommendations with suitability, reason, individual estimates and cost ranges |
| `explanation`, `draft`, `draftSource` | Explanation text and optional structured report with accurate provenance |
| `assumptions`, `warnings`, `keyIssues`, `narrativeUnavailableReason` | Assumptions, data-quality notes, property issues and an explanation of unavailable narrative |
| `currentScoreOnly`, `projectedEpcRating` | Explicitly distinguish a current score from a scenario score; projected EPC is optional and separate from recorded EPC |

Consult the type definition for which fields are optional and which accept `null`. A missing estimate must display as unavailable rather than zero. Value bounds must be provided together as an ordered indicative range. Costs can be unavailable; the frontend must not infer a package total from individual figures.

The score weights referenced by the PDFs are efficiency 25%, intensity 20%, insulation 15%, heating 15%, glazing 10%, renewables 10% and smart controls 5%. Return each component's contribution and reason. If a response combines a current-property score with recommended-package impacts, set `currentScoreOnly` and label that separation. Do not invent an after-score or future EPC when those outputs are absent.

Upgrade IDs used by the frontend are `insulation`, `glazing`, `heat_pump`, `solar` and `thermostat`. Map your catalogue IDs inside the future adapter. Validate that the confirmed selection belongs to the requested property and that selected upgrades are feasible.

## `StructuredDraft`

The intended LLM output is displayed using:

```ts
type StructuredDraft = {
  scenarioId: string;
  summary: string;
  sections: {
    id: string;
    title: string;
    body: string;
    evidenceIds?: string[];
  }[];
  why: {
    title: string;
    body: string;
    evidenceIds?: string[];
  }[];
  limitations: string[];
};
```

The UI presents the summary, structured sections and separate reasons for “why this result?”. `scenarioId` must match the computed report being explained. Evidence IDs can reference supplied components, recommendations or metrics; the LLM must explain the backend's numbers instead of creating new ones. Mark static/template text as such rather than presenting it as real AI.

## What-if integration flow

Keep proposed controls separate from the confirmed report. Submit a full property and explicit upgrade selection. The backend reruns the relevant energy, carbon and valuation calculations for that package, accounting for interactions, and then produces its structured explanation. Display the new report only when its identity and selection match the request. Handle failures visibly without replacing them with sample estimates.

The frontend currently offers only three stored sample plans: starting home, insulation with solar, and the complete package. Other selections and free-text questions need this future integration; they do not trigger network calls in this delivery.

## Reference scope

The two PDFs in `docs/references/` describe the wider system and its intended outputs. They are reference material, not instructions to build a backend, train models or implement hackathon evaluation inside this frontend. [project-reference.md](project-reference.md) maps their sections to the current screens.
