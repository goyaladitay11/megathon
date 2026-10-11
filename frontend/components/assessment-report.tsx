"use client";

import { useId, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  Leaf,
  Sparkles,
} from "lucide-react";
import {
  money,
  number,
  upgrades,
  type Property,
  type Scenario,
} from "@/lib/model";

const percent = (value: number | null | undefined) =>
  value == null
    ? "Not provided"
    : `${value.toLocaleString("en-GB", { maximumFractionDigits: 1 })}%`;
const kwh = (value: number | null | undefined) =>
  value == null ? "Not provided" : `${number(value)} kWh/yr`;
const carbon = (value: number | null | undefined) =>
  value == null ? "Not provided" : `${number(value)} kg CO₂e/yr`;

function ResultCard({
  label,
  value,
  detail,
  reveal,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  reveal: string;
  tone: string;
}) {
  return (
    <article className={`gh-result gh-float ${tone}`} tabIndex={0}>
      <span className="eyebrow">{label}</span>
      <strong>{value}</strong>
      <span className="gh-result-detail">{detail}</span>
      <span className="gh-float-detail">
        <ArrowUpRight size={14} />
        {reveal}
      </span>
    </article>
  );
}

export default function AssessmentReport({
  scenario,
  baseline,
  property,
  displayName,
  view,
}: {
  scenario: Scenario;
  baseline: Scenario | null;
  property: Property;
  displayName: string;
  view: "dashboard" | "simulate";
}) {
  const [tab, setTab] = useState<"report" | "why">("report");
  const tabId = useId();
  const sample = scenario.mode === "demo";
  const draft = scenario.draft;
  const unavailableNarrative =
    scenario.narrativeUnavailableReason ||
    "This preview does not include a new explanation for this plan. Explore the current score-component reasons in Why this result.";
  const feasible = scenario.recommendations.filter((r) => r.feasible);
  const unavailable = scenario.recommendations.filter((r) => !r.feasible);
  const range =
    scenario.valueLow == null || scenario.valueHigh == null
      ? "Not provided"
      : `${money(scenario.valueLow)}–${money(scenario.valueHigh)}`;
  const uplift =
    scenario.valueUpliftLowPct == null || scenario.valueUpliftHighPct == null
      ? "Uplift range not provided"
      : `${percent(scenario.valueUpliftLowPct)}–${percent(scenario.valueUpliftHighPct)} indicative uplift`;

  return (
    <div className="gh-report">
      <section className="gh-report-opening" aria-label="Assessment summary">
        <article className="gh-score gh-float" tabIndex={0}>
          <div className="gh-card-top">
            <span className="eyebrow">CURRENT GREEN HOME SCORE</span>
            <Leaf size={20} />
          </div>
          <div className="gh-score-number">
            <strong>{scenario.score}</strong>
            <span>/ 100</span>
          </div>
          <span className="gh-classification">{scenario.classification}</span>
          <p>
            {sample
              ? "Seven components describe the sample home today. Renovation impacts are shown separately."
              : "Seven components describe the home today. Renovation impacts are shown separately."}
          </p>
          <span className="gh-float-detail">
            <ArrowUpRight size={14} />
            Open “Why this result” to explore the evidence.
          </span>
        </article>
        <article className="gh-report-intro">
          <span className="eyebrow">
            {sample ? "FIXED SAMPLE REPORT" : "CONFIRMED PROPERTY REPORT"}
          </span>
          <h2>
            {displayName
              ? `${displayName}, a clearer picture.`
              : "A clearer picture."}
            <br />
            <em>A thoughtful next step.</em>
          </h2>
          <p>
            {sample
              ? "Explore how your report will look using a fixed example. These figures belong to the sample property, not the details you entered."
              : "Your property's results, suitable improvements and their potential impact, together in one place."}
          </p>
          <div className="gh-intro-tags">
            <span>
              <Check size={14} />
              {scenario.selectedRetrofits.length
                ? sample
                  ? "Stored sample package"
                  : "Confirmed renovation package"
                : sample
                  ? "Sample starting home"
                  : "Current home assessment"}
            </span>
            <span>
              <Check size={14} />
              {sample ? "Illustrative data" : "Backend model outputs"}
            </span>
          </div>
          <small className="gh-scenario-ref">
            Report reference · {scenario.id}
          </small>
        </article>
      </section>

      {Boolean(scenario.keyIssues?.length) && (
        <section
          className="gh-key-issues"
          aria-label="Key issues identified by the assessment"
        >
          <span className="eyebrow">WHERE THIS HOME NEEDS ATTENTION</span>
          <div>
            {scenario.keyIssues?.map((issue, index) => (
              <span key={`issue-${index}`}>{issue}</span>
            ))}
          </div>
        </section>
      )}
      {Boolean(scenario.warnings?.length) && (
        <aside className="gh-data-warnings" aria-label="Data quality notes">
          <span className="eyebrow">DATA QUALITY NOTES</span>
          <ul>
            {scenario.warnings?.map((warning, index) => (
              <li key={`warning-${index}`}>{warning}</li>
            ))}
          </ul>
        </aside>
      )}

      <div className="gh-result-grid">
        <ResultCard
          label="Estimated purchased energy after"
          value={kwh(scenario.purchasedEnergyKwh)}
          detail={
            scenario.energyIntensityKwhM2 == null
              ? "Energy intensity not provided"
              : `Current intensity · ${scenario.energyIntensityKwhM2.toLocaleString("en-GB", { maximumFractionDigits: 1 })} kWh/m² per year`
          }
          reveal="Grid electricity imports and gas, reported separately below."
          tone="gh-ivory"
        />
        <ResultCard
          label="Potential energy saving"
          value={kwh(scenario.energySavingKwh)}
          detail={`${percent(scenario.improvementPotentialPct)} purchased energy reduction`}
          reveal="The package estimate accounts for interactions between upgrades."
          tone="gh-lilac"
        />
        <ResultCard
          label="Potential carbon reduction"
          value={carbon(scenario.carbonReductionKg)}
          detail={
            scenario.carbonSource
              ? sample
                ? "Sample per-fuel emissions factors"
                : "Using documented per-fuel emissions factors"
              : "Emissions-factor source not supplied"
          }
          reveal="A negative reduction means emissions increase."
          tone="gh-peach"
        />
      </div>

      <div
        className="gh-report-navigation"
        role="tablist"
        aria-label="Explore your report"
      >
        <button
          id={`${tabId}-report-tab`}
          role="tab"
          aria-selected={tab === "report"}
          aria-controls={`${tabId}-report`}
          tabIndex={tab === "report" ? 0 : -1}
          onClick={() => setTab("report")}
          onKeyDown={(event) => {
            if (["ArrowRight", "ArrowLeft", "End"].includes(event.key)) {
              event.preventDefault();
              setTab("why");
              document.getElementById(`${tabId}-why-tab`)?.focus();
            }
          }}
        >
          Your report <ArrowUpRight size={16} />
        </button>
        <button
          id={`${tabId}-why-tab`}
          role="tab"
          aria-selected={tab === "why"}
          aria-controls={`${tabId}-why`}
          tabIndex={tab === "why" ? 0 : -1}
          onClick={() => setTab("why")}
          onKeyDown={(event) => {
            if (["ArrowRight", "ArrowLeft", "Home"].includes(event.key)) {
              event.preventDefault();
              setTab("report");
              document.getElementById(`${tabId}-report-tab`)?.focus();
            }
          }}
        >
          Why this result <Sparkles size={16} />
        </button>
      </div>

      <section
        id={`${tabId}-report`}
        role="tabpanel"
        aria-labelledby={`${tabId}-report-tab`}
        hidden={tab !== "report"}
      >
        <section
          className="gh-draft"
          aria-label="Structured assessment explanation"
        >
          <div className="gh-section-title">
            <span className="eyebrow">
              {sample
                ? "FIXED SAMPLE DRAFT · NO LIVE LLM"
                : draft
                  ? "STRUCTURED EXPLANATION"
                  : "EXPLANATION NOT AVAILABLE"}
            </span>
            <h2>The results, in everyday words.</h2>
          </div>
          <p className="gh-draft-summary">
            {draft?.summary || scenario.explanation || unavailableNarrative}
          </p>
          {draft?.sections.length ? (
            <div className="gh-draft-sections">
              {draft.sections.map((section) => (
                <article
                  className="gh-draft-section gh-float"
                  tabIndex={0}
                  key={section.id}
                >
                  <span className="gh-section-marker" aria-hidden="true" />
                  <h3>{section.title}</h3>
                  <p>{section.body}</p>
                  {section.evidenceIds?.length ? (
                    <small className="gh-evidence">
                      Report evidence · {section.evidenceIds.join(" · ")}
                    </small>
                  ) : null}
                </article>
              ))}
            </div>
          ) : (
            <small className="gh-pending-detail">
              Structured sections are not included in this sample plan.
            </small>
          )}
          <small className="gh-source-note">
            {draft
              ? sample
                ? "This fixed sample draft demonstrates the layout. It is not a live LLM response."
                : "This explanation was supplied alongside the report figures. Its sources and limitations are shown with the result."
              : "The sample figures remain available. Current score-component reasons can be explored in Why this result."}
          </small>
        </section>

        <section
          className="gh-section"
          aria-label="Prioritised retrofit recommendations"
        >
          <div className="gh-section-title gh-heading-row">
            <div>
              <span className="eyebrow">SUITABLE IMPROVEMENTS</span>
              <h2>
                A little change.
                <br />
                <em>In the right order.</em>
              </h2>
            </div>
            <p>
              Each recommendation has a reason. Explore per-fuel estimates and
              suitability before choosing your package.
            </p>
          </div>
          {feasible.length ? (
            <div className="gh-recommendations">
              {feasible.map((recommendation, index) => {
                const label =
                  upgrades.find((upgrade) => upgrade.id === recommendation.id)
                    ?.label || recommendation.id;
                return (
                  <article
                    className="gh-recommendation gh-float"
                    key={recommendation.id}
                    tabIndex={0}
                  >
                    <div className="gh-card-top">
                      <span className="eyebrow">
                        {String(recommendation.priority ?? index + 1).padStart(
                          2,
                          "0",
                        )}{" "}
                        / RECOMMENDED
                      </span>
                      <span
                        className={`gh-suitability ${recommendation.suitability?.toLowerCase() || ""}`}
                      >
                        {recommendation.suitability
                          ? `${recommendation.suitability} suitability`
                          : "Suitability not provided"}
                      </span>
                    </div>
                    <h3>{label}</h3>
                    <p>
                      {recommendation.reason ||
                        "The recommendation reason has not been supplied."}
                    </p>
                    <dl className="gh-retrofit-stats">
                      <div>
                        <dt>Electricity saving</dt>
                        <dd>{kwh(recommendation.electricitySavingKwh)}</dd>
                      </div>
                      <div>
                        <dt>Gas saving</dt>
                        <dd>{kwh(recommendation.gasSavingKwh)}</dd>
                      </div>
                      <div>
                        <dt>Estimated cost</dt>
                        <dd>
                          {recommendation.cost == null
                            ? "Not provided"
                            : money(recommendation.cost)}
                        </dd>
                      </div>
                    </dl>
                    {recommendation.notes ? (
                      <small className="gh-recommendation-notes">
                        {recommendation.notes}
                      </small>
                    ) : null}
                    <span className="gh-float-detail">
                      <ArrowUpRight size={14} />
                      {recommendation.carbonReductionKg == null
                        ? "Savings are standalone estimates, not a package total."
                        : `Potential carbon reduction · ${carbon(recommendation.carbonReductionKg)}`}
                    </span>
                  </article>
                );
              })}
            </div>
          ) : (
            <p className="gh-empty">
              No feasible recommendations were supplied for this property.
            </p>
          )}
          <p className="gh-source-note">
            Order and feasibility are fixed sample values. Standalone savings
            are estimates and cannot be added together to predict a package.
          </p>
          {unavailable.length ? (
            <details className="gh-excluded">
              <summary>
                Other improvements considered <ChevronDown size={16} />
              </summary>
              <ul>
                {unavailable.map((recommendation) => (
                  <li key={recommendation.id}>
                    <strong>
                      {upgrades.find(
                        (upgrade) => upgrade.id === recommendation.id,
                      )?.label || recommendation.id}
                    </strong>
                    <span>
                      {recommendation.blockedReason ||
                        "Not feasible for this property."}
                    </span>
                  </li>
                ))}
              </ul>
            </details>
          ) : null}
        </section>

        <section className="gh-section" aria-label="Energy changes by fuel">
          <div className="gh-section-title">
            <span className="eyebrow">BEFORE / AFTER / BY FUEL</span>
            <h2>
              Two fuels.
              <br />
              <em>One complete picture.</em>
            </h2>
            <p>
              A heating upgrade can reduce gas while increasing electricity.
              Negative savings show that increase.
            </p>
          </div>
          <div className="gh-fuel-grid">
            {[
              {
                name: "Grid electricity imports",
                before: scenario.baselineElectricityKwh,
                after: scenario.electricityKwh,
                saving: scenario.electricitySavingKwh,
              },
              {
                name: "Gas consumption",
                before: scenario.baselineGasKwh,
                after: scenario.gasKwh,
                saving: scenario.gasSavingKwh,
              },
            ].map((fuel) => (
              <article
                className="gh-fuel-card gh-float"
                tabIndex={0}
                key={fuel.name}
              >
                <h3>{fuel.name}</h3>
                <dl>
                  <div>
                    <dt>Baseline</dt>
                    <dd>{kwh(fuel.before)}</dd>
                  </div>
                  <div>
                    <dt>After this package</dt>
                    <dd>{kwh(fuel.after)}</dd>
                  </div>
                  <div
                    className={
                      fuel.saving < 0 ? "gh-saving gh-increase" : "gh-saving"
                    }
                  >
                    <dt>Estimated annual saving</dt>
                    <dd>{kwh(fuel.saving)}</dd>
                  </div>
                </dl>
                <span className="gh-float-detail">
                  <ArrowUpRight size={14} />
                  {fuel.saving < 0
                    ? "The negative saving indicates increased consumption."
                    : fuel.name === "Grid electricity imports"
                      ? "Solar can reduce imports; underlying demand is a separate measure."
                      : "This is the confirmed package estimate, including interactions."}
                </span>
              </article>
            ))}
          </div>
        </section>

        <section
          className="gh-value-section"
          aria-label="Indicative property value impact"
        >
          <div className="gh-section-title">
            <span className="eyebrow">POTENTIAL PROPERTY-VALUE IMPACT</span>
            <h2>
              A range.
              <br />
              <em>A more informed conversation.</em>
            </h2>
            <p>
              An indicative estimate for the same property. Discuss it with your
              local agent; a renovation cannot guarantee a sale price.
            </p>
          </div>
          <div className="gh-value-track">
            <article>
              <span>Current value</span>
              <strong>
                {scenario.baselineValue == null
                  ? "Not provided"
                  : money(scenario.baselineValue)}
              </strong>
              <small>Comparison baseline</small>
            </article>
            <ArrowRight size={18} />
            <article>
              <span>Energy rating</span>
              <strong>
                {property.epcRating}
                {scenario.projectedEpcRating
                  ? ` → ${scenario.projectedEpcRating}`
                  : ""}
              </strong>
              <small>
                {scenario.projectedEpcRating
                  ? "Recorded → predicted"
                  : "Future rating not provided"}
              </small>
            </article>
            <ArrowRight size={18} />
            <article className="gh-value-range gh-float" tabIndex={0}>
              <span>Potential value range</span>
              <strong>{range}</strong>
              <small>{uplift}</small>
              <span className="gh-float-detail">
                <ArrowUpRight size={14} />
                Indicative impact, not a guaranteed or proven causal increase.
              </span>
            </article>
          </div>
          {scenario.valueCaveat ? (
            <p className="gh-value-caveat">{scenario.valueCaveat}</p>
          ) : null}
          <div className="gh-package-cost">
            <span>Estimated package cost</span>
            <strong>
              {scenario.cost == null ? "Not provided" : money(scenario.cost)}
            </strong>
            <span>
              {scenario.cost == null
                ? "Package cost not supplied"
                : scenario.cost > property.budget
                  ? "Above the stated budget"
                  : "Within the stated budget"}{" "}
              · budget {money(property.budget)}
            </span>
          </div>
        </section>
      </section>

      <section
        id={`${tabId}-why`}
        role="tabpanel"
        aria-labelledby={`${tabId}-why-tab`}
        hidden={tab !== "why"}
      >
        <section className="gh-why-intro">
          <span className="eyebrow">
            {sample
              ? "SAMPLE REASONS · NO LIVE LLM"
              : draft
                ? "REASONS BEHIND THE REPORT"
                : "CURRENT SCORE REASONS"}
          </span>
          <h2>
            Why this result?
            <br />
            <em>Follow the evidence.</em>
          </h2>
          <p>
            {sample
              ? "These fixed sample reasons show the explanation layout, separately from the structured report draft."
              : "Explore the reasons supplied for this scenario. The explanation refers to the model outputs already shown in your report."}
          </p>
        </section>
        {draft?.why.length ? (
          <div className="gh-why-list">
            {draft.why.map((reason, index) => (
              <details key={`${reason.title}-${index}`} open={index === 0}>
                <summary>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <strong>{reason.title}</strong>
                  <ChevronDown size={17} />
                </summary>
                <p>{reason.body}</p>
                {reason.evidenceIds?.length ? (
                  <small className="gh-evidence">
                    Report evidence · {reason.evidenceIds.join(" · ")}
                  </small>
                ) : null}
              </details>
            ))}
          </div>
        ) : (
          <article className="gh-why-fallback">
            <p>{scenario.explanation || unavailableNarrative}</p>
            <small>
              A separate structured “why” response is not available in this
              report.
            </small>
          </article>
        )}
        <section
          className="gh-section"
          aria-label="Score component contributions"
        >
          <div className="gh-section-title">
            <span className="eyebrow">THE SEVEN COMPONENTS</span>
            <h2>The details behind the score.</h2>
            <p>
              Sub-scores, contributions and reasons are supplied with the
              assessment.
            </p>
          </div>
          <div className="gh-components">
            {scenario.components.map((component) => (
              <details key={component.id}>
                <summary>
                  <div className="gh-component-heading">
                    <strong>{component.label}</strong>
                    <span>
                      {new Intl.NumberFormat("en-GB", {
                        style: "percent",
                        maximumFractionDigits: 0,
                      }).format(component.weight)}{" "}
                      weight ·{" "}
                      {component.contribution == null
                        ? "Contribution not provided"
                        : `${component.contribution.toLocaleString("en-GB", { maximumFractionDigits: 1 })} points contributed`}
                    </span>
                  </div>
                  <div className="gh-component-score">
                    <strong>
                      {component.score}
                      <small>/100</small>
                    </strong>
                    <ChevronDown size={16} />
                  </div>
                </summary>
                <div className="gh-component-meter" aria-hidden="true">
                  <span style={{ width: `${component.score}%` }} />
                </div>
                <p>
                  {component.reason ||
                    "No reason was supplied for this component."}
                </p>
              </details>
            ))}
          </div>
        </section>
      </section>

      <details className="gh-limitations">
        <summary>
          Assumptions, sources and what is still unknown{" "}
          <ChevronDown size={17} />
        </summary>
        <ul>
          {scenario.assumptions.map((assumption, index) => (
            <li key={`assumption-${index}`}>{assumption}</li>
          ))}
          {draft?.limitations.map((limitation, index) => (
            <li key={`draft-limitation-${index}`}>{limitation}</li>
          ))}
        </ul>
        {scenario.carbonSource ? (
          <p>
            <strong>Emissions-factor source</strong>
            <br />
            {scenario.carbonSource}
          </p>
        ) : null}
        {!scenario.assumptions.length && !draft?.limitations.length ? (
          <p>No assumptions or limitations were supplied with this report.</p>
        ) : null}
      </details>
    </div>
  );
}
