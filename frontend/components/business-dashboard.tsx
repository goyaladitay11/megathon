"use client";

import Link from "next/link";
import { useEffect, useId, useMemo, useState } from "react";
import {
  ArrowDownUp,
  ArrowUpRight,
  ChevronDown,
  Download,
  Home,
  Search,
  Sparkles,
} from "lucide-react";
import { loadPortfolio } from "../lib/api";
import {
  money,
  number,
  upgrades,
  type Property,
  type Scenario,
  type Upgrade,
} from "../lib/model";

type Row = {
  property: Property;
  baseline: Scenario;
  package: Scenario;
  selected: Upgrade[];
};
type Sort = "potential" | "score" | "intensity" | "cost";

const intensity = (row: Row) => row.baseline.energyIntensityKwhM2 ?? null;
const poor = (row: Row) =>
  ["poor", "very poor"].includes(row.baseline.classification.toLowerCase());
const percent = (value: number | null | undefined) =>
  value == null
    ? "Unavailable"
    : `${value.toLocaleString("en-GB", { maximumFractionDigits: 1 })}%`;
const energy = (value: number | null | undefined) =>
  value == null ? "Unavailable" : `${number(value)} kWh / yr`;
const currency = (value: number | null | undefined) =>
  value == null ? "Unavailable" : money(value);
const signedEnergy = (value: number | null | undefined) =>
  value == null
    ? "Unavailable"
    : `${value > 0 ? "+" : ""}${number(value)} kWh / yr`;
const retrofitLabel = (id: Upgrade) =>
  upgrades.find((upgrade) => upgrade.id === id)?.label || id;
const recommendationCost = (
  recommendation: Scenario["recommendations"][number],
) => {
  if (recommendation.cost != null) return money(recommendation.cost);
  if (recommendation.costLow != null && recommendation.costHigh != null)
    return `${money(recommendation.costLow)}–${money(recommendation.costHigh)}`;
  return "Unavailable";
};
const baselineFuel = (
  row: Row,
  field:
    "baselineElectricityKwh" | "baselineGasKwh" | "baselinePurchasedEnergyKwh",
) => row.package[field] ?? row.baseline[field] ?? null;

function exportRows(rows: Row[]) {
  const header = [
    "Data origin",
    "Data mode",
    "Property ID",
    "Property",
    "Region",
    "Type",
    "Current assessment report",
    "Recommended package report",
    "Current Green Home Score",
    "Current efficiency classification",
    "Current energy intensity kWh/m2/year",
    "Recommended package improvement potential %",
    "Baseline electricity imports kWh/year",
    "Baseline gas kWh/year",
    "Baseline purchased energy kWh/year",
    "Package electricity imports kWh/year",
    "Package gas kWh/year",
    "Package purchased energy kWh/year",
    "Electricity saving kWh/year",
    "Gas saving kWh/year",
    "Net purchased energy saving kWh/year",
    "Carbon reduction kg CO2e/year",
    "Recommended package cost GBP",
    "Current value GBP",
    "Potential value low GBP",
    "Potential value high GBP",
    "Indicative uplift low %",
    "Indicative uplift high %",
    "Selected measures",
    "Score components",
    "Prioritised recommendations",
    "Structured explanation",
    "Why this result",
    "Explanation provenance",
    "Explanation unavailable reason",
    "Key issue flags",
    "Data-quality warnings",
    "Assumptions",
  ];
  const cell = (value: unknown) => {
    let content = value == null ? "Unavailable" : String(value);
    if (typeof value === "string" && /^\s*[=+\-@]/.test(content))
      content = `'${content}`;
    return `"${content.replaceAll('"', '""')}"`;
  };
  const provenance =
    "Static demonstration portfolio; illustrative figures and sample text, not ML or LLM output";
  const values = rows.map(
    ({ property, baseline, package: scenario, selected }) => [
      provenance,
      "sample",
      property.id,
      property.name,
      property.region,
      property.type,
      baseline.id,
      scenario.id,
      baseline.score,
      baseline.classification,
      intensity({ property, baseline, package: scenario, selected }),
      scenario.improvementPotentialPct,
      baselineFuel(
        { property, baseline, package: scenario, selected },
        "baselineElectricityKwh",
      ),
      baselineFuel(
        { property, baseline, package: scenario, selected },
        "baselineGasKwh",
      ),
      baselineFuel(
        { property, baseline, package: scenario, selected },
        "baselinePurchasedEnergyKwh",
      ),
      scenario.electricityKwh,
      scenario.gasKwh,
      scenario.purchasedEnergyKwh,
      scenario.electricitySavingKwh,
      scenario.gasSavingKwh,
      scenario.energySavingKwh,
      scenario.carbonReductionKg,
      scenario.cost,
      scenario.baselineValue,
      scenario.valueLow,
      scenario.valueHigh,
      scenario.valueUpliftLowPct,
      scenario.valueUpliftHighPct,
      selected.map(retrofitLabel).join("; "),
      JSON.stringify(baseline.components),
      JSON.stringify(scenario.recommendations),
      scenario.draft
        ? JSON.stringify({
            summary: scenario.draft.summary,
            sections: scenario.draft.sections,
          })
        : scenario.explanation,
      scenario.draft?.why.length ? JSON.stringify(scenario.draft.why) : null,
      "Static sample explanation; not an AI response",
      scenario.narrativeUnavailableReason,
      (baseline.keyIssues || scenario.keyIssues || []).join("; "),
      Array.from(
        new Set([...(baseline.warnings || []), ...(scenario.warnings || [])]),
      ).join("; "),
      [...scenario.assumptions, ...(scenario.draft?.limitations || [])].join(
        "; ",
      ),
    ],
  );
  const csv = [[provenance], header, ...values]
    .map((row) => row.map(cell).join(","))
    .join("\r\n");
  const url = URL.createObjectURL(
    new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = "green-home-sample-portfolio.csv";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function BusinessDashboard() {
  const [portfolio, setPortfolio] = useState<Row[]>([]);
  const [loadingError, setLoadingError] = useState("");
  useEffect(() => {
    let live = true;
    loadPortfolio().then(v => { if(live) setPortfolio(v.rows); }).catch(e => { if(live) setLoadingError(String(e)); });
    return () => { live = false; };
  }, []);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [sort, setSort] = useState<Sort>("potential");
  const [descending, setDescending] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  const rows = useMemo(
    () =>
      portfolio
        .filter(
          (row) =>
            `${row.property.name} ${row.property.id} ${row.property.region} ${row.property.type}`
              .toLowerCase()
              .includes(query.toLowerCase()) &&
            (filter === "all" ||
              (filter === "poor" ? poor(row) : row.property.region === filter)),
        )
        .sort((a, b) => {
          const get = (row: Row) =>
            sort === "potential"
              ? row.package.improvementPotentialPct
              : sort === "score"
                ? row.baseline.score
                : sort === "cost"
                  ? row.package.cost
                  : intensity(row);
          const x = get(a),
            y = get(b);
          return x == null
            ? y == null
              ? 0
              : 1
            : y == null
              ? -1
              : (descending ? y - x : x - y) ||
                a.property.name.localeCompare(b.property.name);
        }),
    [portfolio, query, filter, sort, descending],
  );

  const available = rows.filter(
    (row) => row.package.improvementPotentialPct != null,
  );
  const average = available.length
    ? available.reduce(
        (sum, row) => sum + row.package.improvementPotentialPct!,
        0,
      ) / available.length
    : null;
  const carbonRows = rows.filter(
    (row) => row.package.carbonReductionKg != null,
  );
  const regions = Array.from(
    new Set(portfolio.map((row) => row.property.region)),
  ).sort();
  const stats = [
    {
      label: "Properties in view",
      value: `${rows.length} / ${portfolio.length}`,
      note: "Current filters",
      reveal: "Search or filter to focus the comparison.",
    },
    {
      label: "Poor / Very poor",
      value: String(rows.filter(poor).length),
      note: "Reported efficiency classification",
      reveal: "Expand a property to read the score component reasons.",
    },
    {
      label: "Mean improvement potential",
      value: percent(average),
      note: `${available.length} available estimates`,
      reveal:
        "The mean uses only the estimates supplied in the visible reports.",
    },
    {
      label: "Potential carbon reduction",
      value: carbonRows.length
        ? `${(carbonRows.reduce((sum, row) => sum + row.package.carbonReductionKg!, 0) / 1000).toLocaleString("en-GB", { maximumFractionDigits: 1 })} t / yr`
        : "Unavailable",
      note: `${carbonRows.length} available estimates`,
      reveal:
        "Total of the visible reports. A negative figure means an increase.",
    },
  ];

  return (
    <div className="b-app">
      <header className="b-header">
        <Link href="/" className="b-brand">
          <Home size={23} />
          greenhome <small>/ twin</small>
        </Link>
        <nav aria-label="Workspace">
          <Link href="/dashboard">My property</Link>
          <Link href="/business" aria-current="page">
            Business portfolio
          </Link>
        </nav>
        <Link className="b-button" href="/home">
          Homeowner view ↗
        </Link>
      </header>
      <main className="b-main">
        <div className="b-heading">
          <div>
            <span className="b-kicker">THE BIGGER PICTURE / BUSINESS</span>
            <h1>
              More potential.
              <br />
              <span>Across the portfolio.</span>
            </h1>
            <p>
              Compare property reports and find where suitable improvements
              could make the biggest difference.
            </p>
          </div>
          <span className="b-heading-tag">
            <span className="b-dot" />
            Sample portfolio
          </span>
        </div>
        <p className="b-disclosure">
          {portfolio.length} illustrative properties demonstrate the portfolio
          view. Scores, savings and written explanations are fixed examples, not
          results for real customers or responses from an AI system. Estimates
          are not guarantees or market valuations.
        </p>
        <section className="b-stats" aria-label="Visible portfolio summary">
          {stats.map((stat, index) => (
            <article
              tabIndex={0}
              key={stat.label}
              className={`b-float ${index === 1 ? "b-lilac" : index === 2 ? "b-green" : ""}`}
            >
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
              <p>{stat.note}</p>
              <span className="b-float-detail">
                <ArrowUpRight size={14} aria-hidden="true" />
                {stat.reveal}
              </span>
            </article>
          ))}
        </section>
        <section
          className="b-portfolio"
          aria-labelledby="property-explorer-title"
        >
          <div className="b-section-title">
            <h2 id="property-explorer-title">Property explorer</h2>
            <button
              className="b-button"
              disabled={!rows.length}
              onClick={() => exportRows(rows)}
            >
              <Download size={16} />
              Export visible rows
            </button>
          </div>
          <div className="b-toolbar">
            <label className="b-search">
              <Search size={17} />
              <input
                aria-label="Search property or location"
                placeholder="Search property or location"
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <select
              aria-label="Filter properties"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            >
              <option value="all">All properties</option>
              <option value="poor">Poor / Very poor</option>
              {regions.map((region) => (
                <option key={region}>{region}</option>
              ))}
            </select>
            <select
              aria-label="Sort properties by"
              value={sort}
              onChange={(event) => setSort(event.target.value as Sort)}
            >
              {[
                ["potential", "Improvement potential"],
                ["score", "Current Green Home Score"],
                ["intensity", "Energy intensity"],
                ["cost", "Package cost"],
              ].map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            <button
              className="b-sort"
              onClick={() => setDescending((value) => !value)}
              aria-label={
                descending
                  ? "Switch to ascending order"
                  : "Switch to descending order"
              }
            >
              <ArrowDownUp size={16} />
              {descending ? "High → low" : "Low → high"}
            </button>
          </div>
          <p className="b-list-note">
            Rankings use the values supplied in each report. Unavailable values
            stay last. Expand a row to explore suitable measures, the full
            package and why those recommendations were made.
          </p>
          {!rows.length ? (
            <div className="b-empty">
              <h3>No properties to show.</h3>
              <button
                className="b-button"
                onClick={() => {
                  setQuery("");
                  setFilter("all");
                }}
              >
                Reset filters
              </button>
            </div>
          ) : (
            <div className="b-table-wrap">
              <table>
                <caption className="b-sr">
                  Current property scores and recommended package estimates;
                  expand a row to read its assessment and explanation.
                </caption>
                <thead>
                  <tr>
                    {[
                      "Property",
                      "Current score / 100",
                      "kWh / m² / year",
                      "Improvement potential",
                      "Package cost",
                      "Details",
                    ].map((label) => (
                      <th scope="col" key={label}>
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, index) => (
                    <PropertyRows
                      key={row.property.id}
                      row={row}
                      index={index}
                      open={expanded === row.property.id}
                      toggle={() =>
                        setExpanded((current) =>
                          current === row.property.id ? null : row.property.id,
                        )
                      }
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
      <footer className="b-footer">
        <span>greenhome / twin</span>
        <span>Clearer reports. Thoughtful decisions.</span>
      </footer>
    </div>
  );
}

function PropertyRows({
  row,
  index,
  open,
  toggle,
}: {
  row: Row;
  index: number;
  open: boolean;
  toggle: () => void;
}) {
  const property = row.property,
    scenario = row.package,
    baseline = row.baseline;
  const [tab, setTab] = useState<"report" | "why">("report");
  const id = useId();
  const feasible = scenario.recommendations.filter(
    (recommendation) => recommendation.feasible,
  );
  const excluded = scenario.recommendations.filter(
    (recommendation) => !recommendation.feasible,
  );
  const reportWarnings = Array.from(
    new Set([...(baseline.warnings || []), ...(scenario.warnings || [])]),
  );
  const keyIssues = Array.from(
    new Set([...(baseline.keyIssues || []), ...(scenario.keyIssues || [])]),
  );
  const range =
    scenario.valueLow == null || scenario.valueHigh == null
      ? "Unavailable"
      : `${money(scenario.valueLow)}–${money(scenario.valueHigh)}`;
  const metrics = [
    {
      label: "Net purchased energy saving",
      value: energy(scenario.energySavingKwh),
      note: "Full package estimate",
    },
    {
      label: "Electricity saving",
      value: signedEnergy(scenario.electricitySavingKwh),
      note: "Negative means increased imports",
    },
    {
      label: "Gas saving",
      value: signedEnergy(scenario.gasSavingKwh),
      note: "Negative means increased consumption",
    },
    {
      label: "Potential carbon reduction",
      value:
        scenario.carbonReductionKg == null
          ? "Unavailable"
          : `${number(scenario.carbonReductionKg)} kg CO₂e / yr`,
      note: "Negative means increased emissions",
    },
  ];
  const moveTab = (
    event: React.KeyboardEvent<HTMLButtonElement>,
    next: "report" | "why",
  ) => {
    if (["ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      const target =
        event.key === "Home" ? "report" : event.key === "End" ? "why" : next;
      setTab(target);
      document.getElementById(`${id}-${target}-tab`)?.focus();
    }
  };

  return (
    <>
      <tr className={`b-row ${open ? "b-open" : ""}`}>
        <td>
          <div className="b-property">
            <span className="b-rank">{index + 1}</span>
            <div>
              <strong>{property.name}</strong>
              <small>
                {property.region} · {property.type} · {property.floorArea} m²
              </small>
              <small className="b-reference">{property.id}</small>
            </div>
          </div>
        </td>
        <td>
          <strong>{baseline.score}</strong>
          <span className={`b-status ${poor(row) ? "b-poor" : ""}`}>
            {baseline.classification}
          </span>
        </td>
        <td>
          {intensity(row) == null ? "Unavailable" : number(intensity(row)!)}
          <small>Reported baseline</small>
        </td>
        <td>
          <strong className="b-potential">
            {percent(scenario.improvementPotentialPct)}
          </strong>
        </td>
        <td>
          {currency(scenario.cost)}
          <small>
            {scenario.cost == null
              ? "Not supplied in report"
              : "Recommended package estimate"}
          </small>
        </td>
        <td>
          <button
            className="b-expand"
            aria-label={`${open ? "Hide" : "Show"} details for ${property.name}`}
            aria-expanded={open}
            aria-controls={`${id}-details`}
            onClick={toggle}
          >
            <ChevronDown
              size={19}
              style={{ transform: open ? "rotate(180deg)" : undefined }}
            />
          </button>
        </td>
      </tr>
      {open && (
        <tr className="b-detail-row" id={`${id}-details`}>
          <td colSpan={6}>
            <div className="b-detail">
              <div className="b-detail-heading">
                <div>
                  <span className="b-kicker">
                    PROPERTY REPORT / {property.id}
                  </span>
                  <h3>{property.name} · recommended package</h3>
                </div>
                <span>Sample property report</span>
              </div>
              <p>
                Score and classification describe the current home. Energy,
                carbon and value estimates describe the recommended package.
              </p>
              <div className="b-detail-metrics">
                {metrics.map((metric) => (
                  <article className="b-float" tabIndex={0} key={metric.label}>
                    <small>{metric.label}</small>
                    <strong>{metric.value}</strong>
                    <span className="b-float-detail">
                      <ArrowUpRight size={13} aria-hidden="true" />
                      {metric.note}
                    </span>
                  </article>
                ))}
              </div>
              {reportWarnings.length ? (
                <section
                  className="b-data-warnings"
                  aria-label="Property data-quality notes"
                >
                  <strong>Data-quality notes</strong>
                  <ul>
                    {reportWarnings.map((warning, position) => (
                      <li key={position}>{warning}</li>
                    ))}
                  </ul>
                </section>
              ) : null}
              <div
                className="b-report-tabs"
                role="tablist"
                aria-label={`Explore the report for ${property.name}`}
              >
                <button
                  id={`${id}-report-tab`}
                  role="tab"
                  aria-selected={tab === "report"}
                  aria-controls={`${id}-report`}
                  tabIndex={tab === "report" ? 0 : -1}
                  onClick={() => setTab("report")}
                  onKeyDown={(event) => moveTab(event, "why")}
                >
                  Assessment report <ArrowUpRight size={15} />
                </button>
                <button
                  id={`${id}-why-tab`}
                  role="tab"
                  aria-selected={tab === "why"}
                  aria-controls={`${id}-why`}
                  tabIndex={tab === "why" ? 0 : -1}
                  onClick={() => setTab("why")}
                  onKeyDown={(event) => moveTab(event, "report")}
                >
                  Why these results <Sparkles size={15} />
                </button>
              </div>
              <section
                id={`${id}-report`}
                role="tabpanel"
                aria-labelledby={`${id}-report-tab`}
                hidden={tab !== "report"}
              >
                <div className="b-draft">
                  <span className="b-kicker">SAMPLE STRUCTURED DRAFT</span>
                  <h4>The report, in everyday words.</h4>
                  <p>
                    {scenario.draft?.summary ||
                      scenario.explanation ||
                      scenario.narrativeUnavailableReason ||
                      "An explanation has not been supplied for this report."}
                  </p>
                  {scenario.draft?.sections.length ? (
                    <div className="b-draft-grid">
                      {scenario.draft.sections.map((section) => (
                        <article key={section.id}>
                          <h5>{section.title}</h5>
                          <p>{section.body}</p>
                          {section.evidenceIds?.length ? (
                            <small>
                              Report evidence ·{" "}
                              {section.evidenceIds.join(" · ")}
                            </small>
                          ) : null}
                        </article>
                      ))}
                    </div>
                  ) : (
                    <small>
                      Separate structured sections have not been supplied.
                    </small>
                  )}
                </div>
                {keyIssues.length ? (
                  <section className="b-issues">
                    <strong>Key issues reported for this property</strong>
                    <ul>
                      {keyIssues.map((issue, position) => (
                        <li key={position}>{issue}</li>
                      ))}
                    </ul>
                  </section>
                ) : null}
                <section
                  className="b-report-section"
                  aria-label="Prioritised feasible improvements"
                >
                  <div className="b-report-heading">
                    <h4>Suitable improvements, in order.</h4>
                    <p>
                      Standalone per-fuel estimates. These figures cannot be
                      added to predict the complete package.
                    </p>
                  </div>
                  {feasible.length ? (
                    <div className="b-recommendations">
                      {feasible.map((recommendation, position) => (
                        <article
                          className="b-float"
                          tabIndex={0}
                          key={recommendation.id}
                        >
                          <span className="b-kicker">
                            {String(
                              recommendation.priority ?? position + 1,
                            ).padStart(2, "0")}{" "}
                            /{" "}
                            {recommendation.suitability
                              ? `${recommendation.suitability} suitability`
                              : "Suitability unavailable"}
                          </span>
                          <h5>{retrofitLabel(recommendation.id)}</h5>
                          <p>
                            {recommendation.reason ||
                              "A recommendation reason has not been supplied."}
                          </p>
                          {recommendation.notes ? (
                            <small className="b-recommendation-note">
                              {recommendation.notes}
                            </small>
                          ) : null}
                          <dl>
                            <div>
                              <dt>Electricity saving</dt>
                              <dd>
                                {signedEnergy(
                                  recommendation.electricitySavingKwh,
                                )}
                              </dd>
                            </div>
                            <div>
                              <dt>Gas saving</dt>
                              <dd>
                                {signedEnergy(recommendation.gasSavingKwh)}
                              </dd>
                            </div>
                            <div>
                              <dt>Estimated cost</dt>
                              <dd>{recommendationCost(recommendation)}</dd>
                            </div>
                          </dl>
                          <span className="b-float-detail">
                            <ArrowUpRight size={13} aria-hidden="true" />
                            {row.selected.includes(recommendation.id)
                              ? "Included in this property's reported package."
                              : "A feasible improvement in this sample assessment."}
                          </span>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p>
                      No feasible improvements were supplied for this property.
                    </p>
                  )}
                  {excluded.length ? (
                    <details className="b-excluded">
                      <summary>Other measures considered</summary>
                      <ul>
                        {excluded.map((recommendation) => (
                          <li key={recommendation.id}>
                            <strong>{retrofitLabel(recommendation.id)}</strong>{" "}
                            ·{" "}
                            {recommendation.blockedReason ||
                              "Not feasible for this property."}
                          </li>
                        ))}
                      </ul>
                    </details>
                  ) : null}
                </section>
                <section
                  className="b-report-section"
                  aria-label="Full package energy by fuel"
                >
                  <div className="b-report-heading">
                    <h4>The complete package, by fuel.</h4>
                    <p>Negative savings show an increase in consumption.</p>
                  </div>
                  <div className="b-fuel-grid">
                    {[
                      {
                        label: "Grid electricity imports",
                        before: baselineFuel(row, "baselineElectricityKwh"),
                        after: scenario.electricityKwh,
                        saving: scenario.electricitySavingKwh,
                      },
                      {
                        label: "Gas consumption",
                        before: baselineFuel(row, "baselineGasKwh"),
                        after: scenario.gasKwh,
                        saving: scenario.gasSavingKwh,
                      },
                    ].map((fuel) => (
                      <article key={fuel.label}>
                        <h5>{fuel.label}</h5>
                        <dl>
                          <div>
                            <dt>Baseline</dt>
                            <dd>{energy(fuel.before)}</dd>
                          </div>
                          <div>
                            <dt>After the package</dt>
                            <dd>{energy(fuel.after)}</dd>
                          </div>
                          <div
                            className={fuel.saving < 0 ? "b-fuel-increase" : ""}
                          >
                            <dt>Estimated saving</dt>
                            <dd>{signedEnergy(fuel.saving)}</dd>
                          </div>
                        </dl>
                      </article>
                    ))}
                  </div>
                  <p>
                    Annual purchased energy:{" "}
                    {energy(baselineFuel(row, "baselinePurchasedEnergyKwh"))}{" "}
                    before · {energy(scenario.purchasedEnergyKwh)} after. This
                    sample package includes interactions between the measures.
                  </p>
                  <div className="b-measures">
                    {row.selected.length ? (
                      row.selected.map((measure) => (
                        <span key={measure}>{retrofitLabel(measure)}</span>
                      ))
                    ) : (
                      <span>No measures in this package</span>
                    )}
                  </div>
                </section>
                <section
                  className="b-value-panel b-float"
                  tabIndex={0}
                  aria-label="Indicative property value range"
                >
                  <span className="b-kicker">
                    POTENTIAL PROPERTY-VALUE IMPACT
                  </span>
                  <h4>{range}</h4>
                  <p>
                    Current value {currency(scenario.baselineValue)} ·{" "}
                    {scenario.valueUpliftLowPct == null ||
                    scenario.valueUpliftHighPct == null
                      ? "Indicative uplift range unavailable"
                      : `${percent(scenario.valueUpliftLowPct)}–${percent(scenario.valueUpliftHighPct)} indicative uplift`}
                  </p>
                  <p>
                    Package cost {currency(scenario.cost)} · An owner budget has
                    not been provided for these example properties.
                  </p>
                  <span className="b-float-detail">
                    <ArrowUpRight size={13} aria-hidden="true" />
                    An indicative estimate, not a guaranteed or proven causal
                    increase.
                  </span>
                </section>
              </section>
              <section
                id={`${id}-why`}
                role="tabpanel"
                aria-labelledby={`${id}-why-tab`}
                hidden={tab !== "why"}
              >
                <div className="b-draft">
                  <span className="b-kicker">SAMPLE EXPLANATION</span>
                  <h4>Why these results?</h4>
                  <p>
                    Follow the reported reasons and score components for this
                    property.
                  </p>
                  {scenario.draft?.why.length ? (
                    <div className="b-why-list">
                      {scenario.draft.why.map((reason, position) => (
                        <details
                          key={`${reason.title}-${position}`}
                          open={position === 0}
                        >
                          <summary>{reason.title}</summary>
                          <p>{reason.body}</p>
                          {reason.evidenceIds?.length ? (
                            <small>
                              Report evidence · {reason.evidenceIds.join(" · ")}
                            </small>
                          ) : null}
                        </details>
                      ))}
                    </div>
                  ) : (
                    <p>
                      A separate structured “why” response has not been
                      supplied.{" "}
                      {scenario.narrativeUnavailableReason ||
                        scenario.explanation}
                    </p>
                  )}
                </div>
                <section
                  className="b-report-section"
                  aria-label="Score component contributions"
                >
                  <div className="b-report-heading">
                    <h4>What contributes to the score.</h4>
                    <p>
                      Current score {baseline.score}/100 ·{" "}
                      {baseline.classification}. Contributions and reasons are
                      supplied by the assessment.
                    </p>
                  </div>
                  <div className="b-components">
                    {baseline.components.map((component) => (
                      <details key={component.id}>
                        <summary>
                          <strong>{component.label}</strong>
                          <span>
                            {component.score}/100 ·{" "}
                            {component.contribution == null
                              ? "Contribution unavailable"
                              : `${component.contribution.toLocaleString("en-GB", { maximumFractionDigits: 1 })} points contributed`}
                            <ChevronDown size={15} />
                          </span>
                        </summary>
                        <p>
                          {component.reason ||
                            "No reason was supplied for this component."}
                        </p>
                        <small>
                          {new Intl.NumberFormat("en-GB", {
                            style: "percent",
                            maximumFractionDigits: 0,
                          }).format(component.weight)}{" "}
                          weight in the reported score
                        </small>
                      </details>
                    ))}
                  </div>
                </section>
              </section>
              <details className="b-assumptions">
                <summary>Assumptions, sources and limitations</summary>
                <ul>
                  {[
                    ...scenario.assumptions,
                    ...(scenario.draft?.limitations || []),
                    ...(scenario.warnings || []),
                  ].map((assumption, position) => (
                    <li key={position}>{assumption}</li>
                  ))}
                </ul>
                {!scenario.assumptions.length &&
                !scenario.draft?.limitations.length &&
                !scenario.warnings?.length ? (
                  <p>No assumptions or limitations were supplied.</p>
                ) : null}
                {scenario.carbonSource ? (
                  <p>Carbon factors · {scenario.carbonSource}</p>
                ) : null}
                {scenario.valueCaveat ? <p>{scenario.valueCaveat}</p> : null}
                <p>Report reference · {scenario.id}</p>
              </details>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
