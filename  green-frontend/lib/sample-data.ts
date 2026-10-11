import snapshots from "./sample-reports.json";
import type { Property, Scenario } from "./model";
import type { PortfolioRow } from "./api";

// Fixed illustrations for the standalone frontend. No predictions or API requests.
export const sampleProperty = snapshots.property as Property;
export const sampleBaseline = snapshots.baseline as Scenario;
export const samplePackage = snapshots.package as Scenario;
export const sampleCompletePackage = snapshots.complete as Scenario;
export const sampleScenarios = [
  sampleBaseline,
  samplePackage,
  sampleCompletePackage,
];
export const samplePortfolio = snapshots.portfolio as PortfolioRow[];
export const sampleSource = snapshots.source;
