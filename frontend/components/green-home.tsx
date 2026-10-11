"use client";
import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { motion, useReducedMotion } from "motion/react";
import {
  ArrowUpRight,
  ArrowLeft,
  Check,
  Plus,
  Leaf,
  Download,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import InteractiveLanding from "./interactive-landing";
import AssessmentReport from "./assessment-report";
import {
  isProperty,
  money,
  upgrades,
  type Property,
  type Scenario,
  type Upgrade,
} from "@/lib/model";
import {
  sampleProperty,
  sampleBaseline,
  samplePackage,
  sampleCompletePackage,
  sampleScenarios,
} from "@/lib/sample-data";

const propertyKey = "green-home-twin-local-v1";
const profileKey = "green-home-twin-profile-v1";
type View = "landing" | "home" | "dashboard" | "simulate";
type Profile = { displayName: string; goal: "comfort" | "efficiency" | "sell" };
const goalNames = {
  comfort: "Everyday comfort",
  efficiency: "Energy efficiency",
  sell: "Prepare to sell",
};
const selectionKey = (ids: Upgrade[]) => ids.slice().sort().join(",");

export default function GreenHome({ view }: { view: View }) {
  const [property, setProperty] = useState<Property>(sampleProperty);
  const [profile, setProfile] = useState<Profile>({
    displayName: "",
    goal: "sell",
  });
  const [ready, setReady] = useState(false);
  const [step, setStep] = useState(0);
  const [featuresConfirmed, setFeaturesConfirmed] = useState(false);
  const [selected, setSelected] = useState<Upgrade[]>([]);
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [comparisonBase, setComparisonBase] = useState<Scenario | null>(null);
  const [error, setError] = useState("");
  const busy = false;
  const reduced = useReducedMotion();
  const useSample = true;
  const reportProperty = sampleProperty;
  const selectedKey = selectionKey(selected);
  const scenarioCurrent = Boolean(
    scenario &&
    scenario.propertyId === reportProperty.id &&
    selectionKey(scenario.selectedRetrofits) === selectedKey,
  );
  const pageHref = (path: string) => path;

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(propertyKey) || "null");
      if (isProperty(stored)) setProperty(stored);
    } catch {
      /* Browser storage is optional. */
    }
    try {
      const stored = JSON.parse(localStorage.getItem(profileKey) || "null");
      if (
        stored &&
        typeof stored.displayName === "string" &&
        ["comfort", "efficiency", "sell"].includes(stored.goal)
      )
        setProfile({
          displayName: stored.displayName.trim().slice(0, 60),
          goal: stored.goal,
        });
    } catch {
      /* Invalid saved profiles use the defaults. */
    }
    const params = new URLSearchParams(window.location.search);
    const goal = params.get("goal");
    if (["comfort", "efficiency", "sell"].includes(goal || ""))
      setProfile((p) => ({ ...p, goal: goal as Profile["goal"] }));
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready || (view !== "dashboard" && view !== "simulate")) return;
    setComparisonBase(sampleCompletePackage);
    setScenario(sampleCompletePackage);
    setSelected(sampleCompletePackage.selectedRetrofits);
    setError("");
  }, [ready, view]);

  function changeSelected(ids: Upgrade[]) {
    setError("");
    setSelected(ids);
  }

  function loadSample(result: Scenario) {
    setScenario(result);
    setSelected(result.selectedRetrofits);
    setError("");
  }

  function applyScenario() {
    const fixture = sampleScenarios.find(
      (item) => selectionKey(item.selectedRetrofits) === selectedKey,
    );
    if (!fixture) {
      setError(
        "This frontend preview includes three fixed sample plans. Choose Starting home, Insulation + solar, or Complete package. Custom predictions become available after backend integration.",
      );
      return;
    }
    loadSample(fixture);
  }

  function exportResult() {
    if (!scenario || !scenarioCurrent || busy || Boolean(error)) return;
    const url = URL.createObjectURL(
      new Blob(
        [
          JSON.stringify(
            {
              profile,
              property: reportProperty,
              ...(useSample
                ? {
                    enteredProperty: property,
                    notice:
                      "Fixed sample report. Entered property has not been calculated.",
                  }
                : {}),
              assessment: scenario,
            },
            null,
            2,
          ),
        ],
        { type: "application/json" },
      ),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "green-home-property-plan.json";
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function save(event: FormEvent) {
    event.preventDefault();
    setError("");

    if (step === 0) {
      if (!profile.displayName.trim()) {
        setError("What should we call you?");
        return;
      }
      setProfile((p) => ({ ...p, displayName: p.displayName.trim() }));
      setStep(1);
      return;
    }

    if (
      !property.name.trim() ||
      !property.region.trim() ||
      !Number.isFinite(property.floorArea) ||
      property.floorArea <= 10 ||
      property.floorArea >= 1000 ||
      !Number.isInteger(property.yearBuilt) ||
      property.yearBuilt < 1800 ||
      property.yearBuilt > new Date().getFullYear() ||
      !Number.isInteger(property.bedrooms) ||
      property.bedrooms < 1 ||
      property.bedrooms > 10
    ) {
      setError(
        "Use a floor area above 10 and below 1,000 m², 1–10 bedrooms, and a year built from 1800 to the current year.",
      );
      return;
    }

    if (step === 1) {
      if (
        !property.insulation ||
        !property.heating ||
        !property.glazing ||
        !property.solar ||
        typeof property.smartControls !== "boolean" ||
        !featuresConfirmed
      ) {
        setError(
          "Select and confirm the existing home features before continuing.",
        );
        return;
      }
      setStep(2);
      return;
    }

    if (
      ![
        property.electricityKwh,
        property.gasKwh,
        property.currentValue,
        property.budget,
      ].every((n) => Number.isFinite(n) && n >= 0)
    ) {
      setError("Use non-negative annual totals, value and budget.");
      return;
    }

    if (property.currentValue <= 0) {
      setError("Enter a positive current property value.");
      return;
    }

    try {
      localStorage.setItem(
        profileKey,
        JSON.stringify({
          ...profile,
          displayName: profile.displayName.trim(),
        }),
      );
      localStorage.setItem(
        propertyKey,
        JSON.stringify({
          ...property,
          name: property.name.trim(),
          region: property.region.trim(),
          id:
            property.id === sampleProperty.id
              ? `property-${Date.now()}`
              : property.id,
        }),
      );
      window.location.assign(pageHref("/dashboard/"));
    } catch {
      setError(
        "Your browser could not save the plan. Please enable local storage.",
      );
    }
  }

  const input = (
    key: keyof Property,
    label: string,
    type = "number",
    min = 0,
  ) => (
    <label className="field" key={key}>
      {label}
      <input
        type={type}
        min={type === "number" ? min : undefined}
        max={
          key === "yearBuilt"
            ? new Date().getFullYear()
            : key === "bedrooms"
              ? 10
              : key === "floorArea"
                ? 999.9
                : undefined
        }
        step={
          type === "number"
            ? key === "yearBuilt" || key === "bedrooms"
              ? 1
              : "any"
            : undefined
        }
        required
        value={
          type === "number" && !Number.isFinite(Number(property[key]))
            ? ""
            : String(property[key])
        }
        onChange={(e) =>
          setProperty((p) => ({
            ...p,
            [key]:
              type === "number"
                ? e.target.value === ""
                  ? Number.NaN
                  : Number(e.target.value)
                : e.target.value,
          }))
        }
      />
    </label>
  );

  const name = profile.displayName || "Your property";

  return (
    <div className="j-app">
      <header>
        <Link className="brand" href="/">
          <Leaf size={24} />
          greenhome <small>/ twin</small>
        </Link>
        <nav>
          {view === "landing" ? (
            <>
              <a href="#playground">Play with it</a>
              <a href="#journey">How it works</a>
              <Link href="/business">
                For business <ArrowUpRight size={13} />
              </Link>
            </>
          ) : (
            <>
              <Link
                href={pageHref("/home")}
                aria-current={view === "home" ? "page" : undefined}
              >
                Your details
              </Link>
              <Link
                href={pageHref("/dashboard")}
                aria-current={view === "dashboard" ? "page" : undefined}
              >
                Your assessment
              </Link>
              <Link
                href={pageHref("/simulate")}
                aria-current={view === "simulate" ? "page" : undefined}
              >
                Renovation studio
              </Link>
              <Link href="/business">
                Business <ArrowUpRight size={13} />
              </Link>
            </>
          )}
        </nav>
        <Link
          className="button nav-cta"
          href={view === "landing" ? "/home" : "/"}
        >
          {view === "landing" ? "Start your plan" : "Overview"}{" "}
          <ArrowUpRight size={14} />
        </Link>
      </header>

      {view !== "landing" && (
        <div className="mode">
          Frontend preview · fixed sample reports · no live ML or LLM
        </div>
      )}

      <main>
        {view === "landing" ? (
          <InteractiveLanding />
        ) : (
          <div className="workspace">
            {view === "home" ? (
              <div className="j-intake">
                <aside className="j-intake-aside">
                  <span className="j-kicker">
                    <span /> A PLAN THAT STARTS WITH YOU
                  </span>
                  <h1>
                    {step === 0 ? (
                      <>
                        First, a hello.
                        <br />
                        <em>Then, a new chapter.</em>
                      </>
                    ) : (
                      <>
                        {profile.displayName},<br />
                        <em>let’s find the potential.</em>
                      </>
                    )}
                  </h1>
                  <p>
                    Tell us what you want to improve. We’ll bring your property,
                    budget and renovation possibilities into one clearer
                    picture.
                  </p>
                  <ol className="j-intake-steps">
                    {[
                      "Meet you",
                      "Understand the property",
                      "Set the starting point",
                    ].map((s, i) => (
                      <li
                        key={s}
                        className={
                          step === i ? "current" : step > i ? "done" : ""
                        }
                      >
                        <span>{step > i ? <Check size={15} /> : i + 1}</span>
                        {s}
                      </li>
                    ))}
                  </ol>
                  <div className="j-intake-note">
                    <Sparkles size={20} />
                    <p>
                      {goalNames[profile.goal]} is your priority. Explore the
                      report using fixed, clearly labelled sample data.
                    </p>
                  </div>
                  <Link
                    className="j-text-link"
                    href="/dashboard?preview=sample"
                  >
                    Just exploring? Open the example <ArrowUpRight size={15} />
                  </Link>
                </aside>

                <motion.form
                  key={step}
                  initial={{ opacity: reduced ? 1 : 0, y: reduced ? 0 : 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="card property-form"
                  onSubmit={save}
                >
                  <span className="eyebrow">STEP {step + 1} OF 3</span>
                  <h2>
                    {
                      [
                        "What should we call you?",
                        "The place with potential.",
                        "A clearer starting point.",
                      ][step]
                    }
                  </h2>

                  {step === 0 ? (
                    <>
                      <label className="field">
                        Your first name
                        <input
                          autoComplete="given-name"
                          maxLength={60}
                          placeholder="e.g. Jaydeep"
                          value={profile.displayName}
                          required
                          onChange={(e) =>
                            setProfile((p) => ({
                              ...p,
                              displayName: e.target.value,
                            }))
                          }
                        />
                      </label>
                      <fieldset className="j-goal-picker">
                        <legend>What brings you here?</legend>
                        {(["comfort", "efficiency", "sell"] as const).map(
                          (goal) => (
                            <label
                              className={
                                profile.goal === goal ? "selected" : ""
                              }
                              key={goal}
                            >
                              <input
                                type="radio"
                                name="goal"
                                value={goal}
                                checked={profile.goal === goal}
                                onChange={() =>
                                  setProfile((p) => ({ ...p, goal }))
                                }
                              />
                              <span>{goalNames[goal]}</span>
                              <ArrowUpRight size={17} />
                            </label>
                          ),
                        )}
                      </fieldset>
                      <p className="note">
                        No email needed. Your name, goal and property details
                        stay in this browser. They personalise this preview; no
                        data is sent to a backend.
                      </p>
                    </>
                  ) : step === 1 ? (
                    <>
                      {input("name", "Property name or reference", "text")}
                      <label className="field">
                        Property type
                        <select
                          value={property.type}
                          onChange={(e) =>
                            setProperty((p) => ({
                              ...p,
                              type: e.target.value,
                              roofAccess: e.target.value !== "flat",
                            }))
                          }
                        >
                          {[
                            "detached",
                            "semi-detached",
                            "terraced",
                            "flat",
                          ].map((t) => (
                            <option key={t}>{t}</option>
                          ))}
                        </select>
                      </label>
                      <div className="form-grid">
                        {input("region", "Town or region", "text")}
                        {input("yearBuilt", "Year built", "number", 1800)}
                        {input("floorArea", "Floor area (m²)", "number", 10.1)}
                        {input("bedrooms", "Bedrooms", "number", 1)}
                      </div>
                      <fieldset className="gh-current-features">
                        <legend>Existing home features</legend>
                        <p className="note">
                          Initial prefilled values describe the sample property.
                          Check and update every feature to match your home,
                          then confirm the details below. Missing saved features
                          are left blank.
                        </p>
                        <div className="form-grid">
                          <label className="field">
                            Insulation
                            <select
                              required
                              value={property.insulation || ""}
                              onChange={(event) => {
                                setFeaturesConfirmed(false);
                                setProperty((p) => ({
                                  ...p,
                                  insulation: event.target
                                    .value as Property["insulation"],
                                }));
                              }}
                            >
                              <option value="" disabled>
                                Choose the current feature
                              </option>
                              <option value="poor">Poor</option>
                              <option value="average">Average</option>
                              <option value="good">Good</option>
                            </select>
                          </label>
                          <label className="field">
                            Heating system
                            <select
                              required
                              value={property.heating || ""}
                              onChange={(event) => {
                                setFeaturesConfirmed(false);
                                setProperty((p) => ({
                                  ...p,
                                  heating: event.target
                                    .value as Property["heating"],
                                }));
                              }}
                            >
                              <option value="" disabled>
                                Choose the current feature
                              </option>
                              <option value="gas_boiler">Gas boiler</option>
                              <option value="electric_resistive">
                                Electric heating
                              </option>
                              <option value="oil_boiler">Oil boiler</option>
                              <option value="heat_pump">Heat pump</option>
                            </select>
                          </label>
                          <label className="field">
                            Windows and glazing
                            <select
                              required
                              value={property.glazing || ""}
                              onChange={(event) => {
                                setFeaturesConfirmed(false);
                                setProperty((p) => ({
                                  ...p,
                                  glazing: event.target
                                    .value as Property["glazing"],
                                }));
                              }}
                            >
                              <option value="" disabled>
                                Choose the current feature
                              </option>
                              <option value="single">Single glazing</option>
                              <option value="double">Double glazing</option>
                              <option value="triple">Triple glazing</option>
                            </select>
                          </label>
                          <label className="field">
                            Installed solar
                            <select
                              required
                              value={property.solar || ""}
                              onChange={(event) => {
                                setFeaturesConfirmed(false);
                                setProperty((p) => ({
                                  ...p,
                                  solar: event.target
                                    .value as Property["solar"],
                                }));
                              }}
                            >
                              <option value="" disabled>
                                Choose the current feature
                              </option>
                              <option value="none">None</option>
                              <option value="2kw">2 kW</option>
                              <option value="4kw">4 kW</option>
                            </select>
                          </label>
                          <label className="field">
                            Smart heating controls
                            <select
                              required
                              value={
                                typeof property.smartControls === "boolean"
                                  ? property.smartControls
                                    ? "yes"
                                    : "no"
                                  : ""
                              }
                              onChange={(event) => {
                                setFeaturesConfirmed(false);
                                setProperty((p) => ({
                                  ...p,
                                  smartControls: event.target.value === "yes",
                                }));
                              }}
                            >
                              <option value="" disabled>
                                Choose the current feature
                              </option>
                              <option value="yes">Installed</option>
                              <option value="no">Not installed</option>
                            </select>
                          </label>
                        </div>
                        <label className="checkbox gh-features-confirm">
                          <input
                            type="checkbox"
                            required
                            checked={featuresConfirmed}
                            onChange={(event) =>
                              setFeaturesConfirmed(event.target.checked)
                            }
                          />
                          I have checked these features and they reflect my home
                          today.
                        </label>
                      </fieldset>
                      <small>
                        Prefilled property fields are editable example values.
                        Check each feature against your home.
                      </small>
                    </>
                  ) : (
                    <>
                      <p>
                        Use measured annual totals. Zero means measured zero,
                        not missing data. If you don’t know a total, return with
                        your bill before assessing.
                      </p>
                      <div className="form-grid">
                        {input(
                          "electricityKwh",
                          "Annual grid electricity (kWh)",
                        )}
                        {input("gasKwh", "Annual gas (kWh)")}
                        {input(
                          "currentValue",
                          "Current property value (£)",
                          "number",
                          1,
                        )}
                        {input("budget", "Planning budget (£) · local only")}
                      </div>
                      <label className="field">
                        Recorded EPC
                        <select
                          value={property.epcRating}
                          onChange={(e) =>
                            setProperty((p) => ({
                              ...p,
                              epcRating: e.target.value,
                            }))
                          }
                        >
                          {["A", "B", "C", "D", "E", "F", "G"].map((r) => (
                            <option key={r}>{r}</option>
                          ))}
                        </select>
                      </label>
                      <p className="note">
                        Your confirmed details and planning budget stay in this
                        browser. The next screen shows a separate sample report
                        until the backend is connected.
                      </p>
                    </>
                  )}

                  {error && (
                    <p className="error" role="alert">
                      {error}
                    </p>
                  )}
                  <div className="actions">
                    {step > 0 && (
                      <button
                        type="button"
                        className="button"
                        onClick={() => {
                          setError("");
                          setStep((s) => s - 1);
                        }}
                      >
                        <ArrowLeft size={16} />
                        Back
                      </button>
                    )}
                    <button className="button primary" type="submit">
                      {step === 2 ? "Show my property plan" : "Keep going"}{" "}
                      <ArrowRight size={17} />
                    </button>
                  </div>
                </motion.form>
              </div>
            ) : (
              <>
                <div className="page-title">
                  <div>
                    <span className="eyebrow">
                      {goalNames[profile.goal]} /{" "}
                      {view === "dashboard"
                        ? "YOUR PROPERTY REPORT"
                        : "YOUR RENOVATION PLAN"}
                    </span>
                    <h1>
                      {view === "dashboard" ? (
                        <>
                          {profile.displayName ? `${name}, here’s` : "Here’s"}{" "}
                          the picture.
                          <br />
                          <em>Let’s find the possibility.</em>
                        </>
                      ) : (
                        <>
                          {profile.displayName ? `${name}, explore` : "Explore"}{" "}
                          a little change.
                          <br />
                          <em>See what follows.</em>
                        </>
                      )}
                    </h1>
                  </div>
                  <div className="actions">
                    <Link className="button" href={pageHref("/home")}>
                      Edit details
                    </Link>
                    <button
                      className="button"
                      onClick={exportResult}
                      disabled={
                        !scenario || !scenarioCurrent || busy || Boolean(error)
                      }
                    >
                      <Download size={15} />
                      Export confirmed plan
                    </button>
                  </div>
                </div>

                <div className="property-strip">
                  <strong>{property.name}</strong>
                  <span>
                    {property.region} · {property.type} · {property.floorArea}{" "}
                    m² · recorded EPC {property.epcRating}
                  </span>
                </div>
                {useSample && (
                  <aside
                    className="gh-sample-subject"
                    aria-label="Sample report subject"
                  >
                    <span className="eyebrow">
                      SAMPLE REPORT · YOUR DETAILS HAVE NOT BEEN CALCULATED
                    </span>
                    <p>
                      The report below belongs to{" "}
                      <strong>{sampleProperty.name}</strong> in{" "}
                      {sampleProperty.region}, a {sampleProperty.floorArea} m²{" "}
                      {sampleProperty.type} with recorded EPC{" "}
                      {sampleProperty.epcRating}.
                    </p>
                    <small>
                      Fixed illustrative results help you explore the interface.
                      Your entered details remain saved in this browser.
                      Personal predictions and LLM explanations will be
                      available after backend integration.
                    </small>
                  </aside>
                )}

                {error && (
                  <div className="error" role="alert">
                    {error}
                  </div>
                )}
                {!scenario ? (
                  <p role="status">Loading the sample report…</p>
                ) : (
                  <>
                    {view === "simulate" && (
                      <section
                        className="gh-plan-controls"
                        aria-label="Choose a renovation package"
                      >
                        <div className="gh-section-title">
                          <span className="eyebrow">YOUR NEXT CHAPTER</span>
                          <h2>Choose the possibilities.</h2>
                          <p>
                            Explore three fixed example plans. Upgrade controls
                            let you draft a selection; loading a matching sample
                            changes the report without calculating predictions.
                          </p>
                        </div>
                        {useSample && (
                          <div className="gh-sample-presets">
                            <span>LOAD A SAMPLE PLAN</span>
                            <button onClick={() => loadSample(sampleBaseline)}>
                              Starting home
                            </button>
                            <button onClick={() => loadSample(samplePackage)}>
                              Insulation + solar
                            </button>
                            <button
                              onClick={() => loadSample(sampleCompletePackage)}
                            >
                              Complete package
                            </button>
                          </div>
                        )}
                        <div className="gh-upgrade-grid">
                          {upgrades.map((upgrade) => {
                            const recommendation =
                              comparisonBase?.recommendations.find(
                                (item) => item.id === upgrade.id,
                              );
                            const reason = !recommendation
                              ? "No feasibility assessment supplied."
                              : !recommendation.feasible
                                ? recommendation.blockedReason ||
                                  "Not feasible for this property."
                                : "";
                            const active = selected.includes(upgrade.id);
                            return (
                              <motion.button
                                key={upgrade.id}
                                layout={!reduced}
                                whileTap={reduced ? {} : { scale: 0.99 }}
                                className={`upgrade ${active ? "active" : ""}`}
                                aria-pressed={active}
                                aria-label={`${active ? "Remove" : "Add"} ${upgrade.label}`}
                                disabled={Boolean(reason)}
                                onClick={() =>
                                  changeSelected(
                                    active
                                      ? selected.filter(
                                          (id) => id !== upgrade.id,
                                        )
                                      : [...selected, upgrade.id],
                                  )
                                }
                              >
                                <div>
                                  <strong>{upgrade.label}</strong>
                                  <p>{upgrade.description}</p>
                                  <small>
                                    {reason ||
                                      `${recommendation?.suitability || "Assessed"} suitability · ${recommendation?.cost == null ? "Cost not supplied" : money(recommendation.cost)}`}
                                  </small>
                                </div>
                                {active ? (
                                  <Check size={18} />
                                ) : (
                                  <Plus size={18} />
                                )}
                              </motion.button>
                            );
                          })}
                        </div>
                        <div className="gh-plan-actions">
                          <span>
                            {scenarioCurrent
                              ? "Your controls match the confirmed package."
                              : "Draft package · changes have not been applied."}
                          </span>
                          <div className="actions">
                            <button
                              className="button"
                              onClick={() => changeSelected([])}
                            >
                              Clear selection
                            </button>
                            <button
                              className="button primary"
                              onClick={() => void applyScenario()}
                              disabled={busy || scenarioCurrent}
                            >
                              Load selected sample
                              <ArrowRight size={16} />
                            </button>
                          </div>
                        </div>
                      </section>
                    )}
                    <p className="gh-confirmed-note" role="status">
                      {!scenarioCurrent
                        ? "Your selection is a draft. Load a matching sample plan to change the preview."
                        : `${scenario.selectedRetrofits.length} improvements in this fixed sample package. The score describes the sample home’s current condition.`}
                    </p>
                    <AssessmentReport
                      scenario={scenario}
                      baseline={comparisonBase}
                      property={reportProperty}
                      displayName={profile.displayName}
                      view={view}
                    />
                    {view === "dashboard" ? (
                      <div className="gh-dashboard-next">
                        <div>
                          <h3>Make the plan your own.</h3>
                          <p>
                            Explore improvements and compare the fixed sample
                            package estimates.
                          </p>
                        </div>
                        <Link
                          className="button primary"
                          href={pageHref("/simulate")}
                        >
                          Explore renovation scenarios{" "}
                          <ArrowUpRight size={16} />
                        </Link>
                      </div>
                    ) : (
                      <div className="gh-conversation">
                        <form
                          className="card"
                          onSubmit={(event) => event.preventDefault()}
                        >
                          <span className="eyebrow">
                            A QUESTION ABOUT YOUR REPORT?
                          </span>
                          <h3>
                            {profile.displayName
                              ? `Let’s look closer, ${profile.displayName}.`
                              : "Let’s look closer."}
                          </h3>
                          <p>
                            The explanation area previews how a structured
                            response will appear beside your results.
                          </p>
                          <label className="field">
                            Your question
                            <textarea
                              disabled
                              placeholder="Why is insulation recommended first?"
                              maxLength={2000}
                            />
                          </label>
                          <div className="actions">
                            <button className="button primary" disabled>
                              Explain this result
                              <Sparkles size={16} />
                            </button>
                          </div>
                          <small>
                            Questions are available after backend integration.
                            The draft and reasons shown above are fixed sample
                            text, not live AI responses.
                          </small>
                        </form>
                        <form
                          className="card"
                          onSubmit={(event) => event.preventDefault()}
                        >
                          <span className="eyebrow">
                            WHAT IF I CHANGE THE PLAN?
                          </span>
                          <h3>
                            A new scenario.
                            <br />
                            <em>A fresh perspective.</em>
                          </h3>
                          <p>
                            In the connected app, a what-if request will rerun
                            the backend models before an explanation describes
                            their confirmed outputs.
                          </p>
                          <label className="field">
                            What-if question
                            <textarea
                              disabled
                              placeholder="What if I add solar to this package?"
                              maxLength={2000}
                            />
                          </label>
                          <div className="actions">
                            <button className="button primary" disabled>
                              Run a what-if
                              <ArrowRight size={16} />
                            </button>
                          </div>
                          <small>
                            This frontend provides three sample plans above.
                            Custom scenarios and new explanations need a backend
                            connection.
                          </small>
                        </form>
                      </div>
                    )}
                  </>
                )}
              </>
            )}
          </div>
        )}
      </main>

      <footer>
        <Link className="brand" href="/">
          greenhome <small>/ twin</small>
        </Link>
        <span>A thoughtful renovation. A clearer next chapter.</span>
        <Link href="/business">
          Business dashboard <ArrowUpRight size={13} />
        </Link>
        <small>Decision support, not a survey or sale guarantee.</small>
      </footer>
    </div>
  );
}
