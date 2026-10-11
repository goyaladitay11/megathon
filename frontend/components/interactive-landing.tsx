"use client";

import Link from "next/link";
import { useId, useRef, useState, type KeyboardEvent } from "react";
import {
  motion,
  useReducedMotion,
  useScroll,
  useTransform,
} from "motion/react";
import {
  ArrowUpRight,
  ArrowDown,
  MoveUpRight,
  Check,
  Sparkles,
  Leaf,
  FileText,
  ChevronRight,
  BarChart3,
} from "lucide-react";
import { money, number, upgrades, type Scenario } from "@/lib/model";
import {
  sampleBaseline,
  samplePackage,
  sampleProperty,
} from "@/lib/sample-data";

const steps = [
  [
    "01",
    "A little about you.",
    "Your name, your property, and what you want to change.",
  ],
  [
    "02",
    "See the whole picture.",
    "Your green score, seven component contributions and the reasons behind them.",
  ],
  [
    "03",
    "Ask a better “what if?”.",
    "Explore example plans. Your backend can reassess changed details once connected.",
  ],
  [
    "04",
    "Leave with a clear plan.",
    "A structured explanation, energy by fuel, carbon and an indicative value range.",
  ],
];

const reportTabs = ["Score", "Plan", "Why"] as const;
type ReportTab = (typeof reportTabs)[number];

function ReportPreview({
  scenario,
  compact = false,
}: {
  scenario: Scenario;
  compact?: boolean;
}) {
  const [tab, setTab] = useState<ReportTab>("Score");
  const id = useId();
  const feasible = scenario.recommendations.filter((item) => item.feasible);
  const onTabKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    const position = reportTabs.indexOf(tab);
    let next: number | undefined;
    if (event.key === "ArrowRight") next = (position + 1) % reportTabs.length;
    if (event.key === "ArrowLeft")
      next = (position + reportTabs.length - 1) % reportTabs.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = reportTabs.length - 1;
    if (next === undefined) return;
    event.preventDefault();
    setTab(reportTabs[next]);
    document.getElementById(`${id}-${reportTabs[next]}-tab`)?.focus();
  };

  return (
    <div className={`j-paper-report ${compact ? "j-paper-compact" : ""}`}>
      <div className="j-paper-heading">
        <span className="eyebrow">
          <Leaf size={13} aria-hidden /> GREEN HOME REPORT
        </span>
        <span className="j-report-label">Example</span>
      </div>
      <div className="j-paper-property">
        <div>
          <h3>A brighter next chapter.</h3>
          <p>
            {sampleProperty.region} · {sampleProperty.bedrooms}-bed{" "}
            {sampleProperty.type}
          </p>
        </div>
        <FileText size={25} aria-hidden />
      </div>
      <div
        className="j-report-tabs"
        role="tablist"
        aria-label="Explore this example report"
      >
        {reportTabs.map((item) => (
          <button
            type="button"
            key={item}
            role="tab"
            id={`${id}-${item}-tab`}
            aria-controls={`${id}-${item}-panel`}
            aria-selected={tab === item}
            tabIndex={tab === item ? 0 : -1}
            onClick={() => setTab(item)}
            onKeyDown={onTabKeyDown}
          >
            {item}
            <ArrowUpRight size={13} aria-hidden />
          </button>
        ))}
      </div>
      {reportTabs.map((item) => (
        <div
          role="tabpanel"
          id={`${id}-${item}-panel`}
          aria-labelledby={`${id}-${item}-tab`}
          hidden={tab !== item}
          tabIndex={0}
          className="j-report-panel"
          key={item}
        >
          {item === "Score" ? (
            <>
              <div className="j-paper-score">
                <div>
                  <span className="eyebrow">GREEN SCORE</span>
                  <strong>
                    {scenario.score}
                    <small>/100</small>
                  </strong>
                </div>
                <span className="j-paper-classification">
                  <span className="j-dot" /> {scenario.classification}
                </span>
              </div>
              <div className="j-component-preview">
                {scenario.components
                  .slice(0, compact ? 3 : 7)
                  .map((component) => (
                    <details key={component.id} className="j-component-line">
                      <summary>
                        <span>{component.label}</span>
                        <strong>
                          {component.score}
                          <small>/100</small>
                        </strong>
                        <ChevronRight size={12} aria-hidden />
                      </summary>
                      <div className="j-preview-bar" aria-hidden>
                        <span style={{ width: `${component.score}%` }} />
                      </div>
                      <p>
                        {component.contribution !== undefined &&
                          component.contribution !== null && (
                            <>
                              <strong>
                                {component.contribution.toLocaleString(
                                  "en-GB",
                                  { maximumFractionDigits: 1 },
                                )}{" "}
                                points contributed to the overall score.
                              </strong>{" "}
                            </>
                          )}
                        {component.reason}
                      </p>
                    </details>
                  ))}
              </div>
              <p className="j-paper-footnote">
                {compact
                  ? "Seven components. One clearer picture. Open a row to see why."
                  : "Open each component to read the explanation supplied with this example report."}
              </p>
            </>
          ) : item === "Plan" ? (
            <div className="j-plan-preview">
              <span className="eyebrow">FEASIBLE NEXT STEPS</span>
              {feasible
                .slice(0, compact ? 2 : 3)
                .map((recommendation, index) => (
                  <details
                    className="j-preview-recommendation"
                    key={recommendation.id}
                  >
                    <summary>
                      <span className="j-plan-order">0{index + 1}</span>
                      <span>
                        {upgrades.find(
                          (upgrade) => upgrade.id === recommendation.id,
                        )?.label ?? recommendation.id}
                        <small>
                          {recommendation.suitability
                            ? `${recommendation.suitability} suitability`
                            : "Feasible in this example"}
                        </small>
                      </span>
                      <ChevronRight size={14} aria-hidden />
                    </summary>
                    <p>
                      {recommendation.reason ||
                        "A recommendation from the example report; suitability for your property needs a backend assessment."}
                    </p>
                  </details>
                ))}
              <p className="j-paper-footnote">
                Your recommendations will include feasibility, priority and a
                reason for each improvement.
              </p>
            </div>
          ) : (
            <div className="j-why-preview">
              <span className="j-explanation-icon">
                <Sparkles size={19} aria-hidden />
              </span>
              <span className="eyebrow">THE STORY BEHIND THE SCORE</span>
              <h4>Clear answers. With reasons.</h4>
              <p>{scenario.draft?.summary || scenario.explanation}</p>
              {scenario.draft?.why.slice(0, 1).map((answer) => (
                <details className="j-draft-why" key={answer.title}>
                  <summary>
                    {answer.title}
                    <ChevronRight size={12} aria-hidden />
                  </summary>
                  <p>{answer.body}</p>
                </details>
              ))}
              <div className="j-example-boundary">
                <FileText size={14} aria-hidden />
                <span>
                  Example explanation. Your report and follow-up answers come
                  from a backend once your friend connects it.
                </span>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default function InteractiveLanding() {
  const [packagePreview, setPackagePreview] = useState(false);
  const [purpose, setPurpose] = useState("Prepare to sell");
  const scenario = packagePreview ? samplePackage : sampleBaseline;
  const ref = useRef<HTMLElement>(null);
  const reduced = useReducedMotion();
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start center", "end center"],
  });
  const scaleX = useTransform(scrollYProgress, [0, 1], [0, 1]);
  const reveal = {
    initial: { opacity: reduced ? 1 : 0, y: reduced ? 0 : 22 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true, amount: 0.12 },
    transition: { duration: reduced ? 0 : 0.5 },
  };

  return (
    <div className="interactive-landing">
      <section className="j-hero">
        <motion.div {...reveal}>
          <span className="j-kicker">
            <span /> A NEW CHAPTER FOR YOUR PROPERTY
          </span>
          <h1>
            A little change.
            <br />A whole lot of
            <br />
            <span className="j-serif">possibility.</span>
            <motion.span
              className="j-spark"
              aria-hidden
              animate={reduced ? {} : { rotate: [0, 18, 0] }}
              transition={{ duration: 4, repeat: Infinity }}
            >
              ✳
            </motion.span>
          </h1>
          <p>
            Renovate for the way you live.
            <br />
            Plan for the day you sell.
          </p>
          <div className="actions">
            <Link className="button primary" href="/home">
              Make it yours <ArrowUpRight size={19} />
            </Link>
            <a className="j-text-link" href="#playground">
              Explore an example report <ArrowDown size={15} />
            </a>
          </div>
          <small>
            Start with your name. Leave with a clearer property plan.
          </small>
        </motion.div>
        <motion.div {...reveal} className="j-hero-stack j-report-stack">
          <div className="j-mini-title">
            <span>YOUR HOME. THE WHOLE PICTURE.</span>
            <span>↗</span>
          </div>
          <ReportPreview scenario={sampleBaseline} compact />
          <div className="j-floating-detail j-floating-peach" aria-hidden>
            <span>STEP BY STEP</span>
            <strong>A plan that fits.</strong>
            <ArrowUpRight size={17} />
          </div>
          <div className="j-floating-detail j-floating-green" aria-hidden>
            <Leaf size={17} />
            <span>
              Small changes.
              <br />
              <strong>Lasting possibilities.</strong>
            </span>
          </div>
          <div className="j-preview-caption">
            <span>
              <span className="j-dot" /> STATIC EXAMPLE REPORT
            </span>
            <span>Try the tabs above ↑</span>
          </div>
        </motion.div>
      </section>

      <div className="j-ticker">
        <span>MADE FOR THE HOME YOU ALREADY OWN</span>
        <span>Comfort ✳ Energy ✳ Renovation ✳ Sale preparation</span>
        <span>EXPLORE BELOW ↓</span>
      </div>

      <section className="j-playground" id="playground">
        <motion.div {...reveal} className="j-section-heading">
          <div>
            <span className="eyebrow">
              A CLEARER PICTURE OF WHAT COMES NEXT
            </span>
            <h2>
              Your property,
              <br />
              <em>beautifully explained.</em>
            </h2>
          </div>
          <p>
            A score is only the beginning.
            <br />
            Explore the components, practical next steps and reasons behind this
            example.
          </p>
        </motion.div>
        <div className="j-play-grid">
          <div className="j-live-demo j-example-report">
            <div
              className="j-example-selector"
              role="group"
              aria-label="Choose a static example report"
            >
              <button
                type="button"
                aria-pressed={!packagePreview}
                onClick={() => setPackagePreview(false)}
              >
                Current home
              </button>
              <button
                type="button"
                aria-pressed={packagePreview}
                onClick={() => setPackagePreview(true)}
              >
                Example improvement plan <ArrowUpRight size={13} aria-hidden />
              </button>
            </div>
            <ReportPreview scenario={scenario} />
            <div className="j-demo-summary">
              <span>Two fixed examples to explore the report layout.</span>
              <Link href="/dashboard/?preview=sample">
                Open the full example ↗
              </Link>
            </div>
          </div>
          <div className="j-impact-stack">
            <article className="j-impact-card j-impact-moss j-float-card">
              <span className="eyebrow">THE STARTING POINT</span>
              <strong>
                {scenario.score}
                <small>/100 green score</small>
              </strong>
              <span>
                {scenario.classification} · explained across seven components
              </span>
              <p>
                A future backend will supply the score, component contributions and
                classification. Your report makes each part easy to understand.
              </p>
            </article>
            <article className="j-impact-card peach j-float-card">
              <span className="eyebrow">THE EVERYDAY IMPACT</span>
              <div className="j-landing-fuels">
                <div>
                  <span>Electricity</span>
                  <strong>
                    {number(scenario.electricityKwh)}
                    <small>kWh/year</small>
                  </strong>
                </div>
                <div>
                  <span>Gas</span>
                  <strong>
                    {number(scenario.gasKwh)}
                    <small>kWh/year</small>
                  </strong>
                </div>
              </div>
              <span>
                {scenario.carbonReductionKg === null
                  ? "Carbon reduction not provided"
                  : `${number(scenario.carbonReductionKg)} kg CO₂e/year · example reduction`}
              </span>
            </article>
            <article className="j-impact-card lavender j-float-card">
              <span className="eyebrow">A PLAN WITH PERSPECTIVE</span>
              <strong className="j-value-preview">
                {scenario.valueLow !== null && scenario.valueHigh !== null
                  ? `${money(scenario.valueLow)} – ${money(scenario.valueHigh)}`
                  : "Value range pending"}
              </strong>
              <span>
                Indicative property value ·{" "}
                {scenario.cost !== null
                  ? `${money(scenario.cost)} example improvement cost`
                  : "installation cost not provided"}
              </span>
            </article>
            <div className="j-demo-note">
              <Sparkles size={17} aria-hidden />
              <p>
                These are fixed examples, not predictions for your home or live
                AI responses. Your assessment, what-if results and structured
                explanations will be supplied after backend integration.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="j-purpose">
        <motion.div {...reveal}>
          <span className="eyebrow">
            WHAT DOES YOUR NEXT CHAPTER LOOK LIKE?
          </span>
          <h2>
            Make room for
            <br />
            <em>what matters to you.</em>
          </h2>
        </motion.div>
        <div
          className="j-purpose-tabs"
          role="group"
          aria-label="Choose your renovation purpose"
        >
          {["Feel more comfortable", "Use less energy", "Prepare to sell"].map(
            (item, i) => (
              <button
                type="button"
                key={item}
                aria-pressed={purpose === item}
                onClick={() => setPurpose(item)}
                className={purpose === item ? "chosen" : ""}
              >
                <span>0{i + 1}</span>
                {item}
                <MoveUpRight size={21} aria-hidden />
              </button>
            ),
          )}
        </div>
        <motion.div
          className="j-purpose-answer"
          key={purpose}
          initial={{ opacity: reduced ? 1 : 0, y: reduced ? 0 : 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Leaf size={22} aria-hidden />
          <p>
            {purpose === "Prepare to sell"
              ? "Explore feasible renovation options, compare improvement costs with an indicative value range, and bring an informed plan to your estate agent."
              : purpose === "Use less energy"
                ? "See electricity and gas changes separately, alongside carbon impact and the reasons behind each recommendation."
                : "Explore the fabric and heating improvements that suit your property, with practical reasons for each next step."}
          </p>
          <Link
            href={`/home/?goal=${purpose === "Prepare to sell" ? "sell" : purpose === "Use less energy" ? "efficiency" : "comfort"}`}
          >
            Start with this goal ↗
          </Link>
        </motion.div>
      </section>

      <section className="j-workflow" id="journey" ref={ref}>
        <motion.div {...reveal}>
          <span className="eyebrow">FROM A FIRST NAME TO A FIRST PLAN</span>
          <h2>
            It starts with you.
            <br />
            <em>Then comes the possibility.</em>
          </h2>
        </motion.div>
        <div className="j-workflow-line">
          <motion.div style={{ scaleX: reduced ? 1 : scaleX }} />
        </div>
        <div className="j-step-grid">
          {steps.map(([n, title, text]) => (
            <motion.article {...reveal} key={n} className="j-float-card">
              <span key="number" className="j-step-num">
                {n}
              </span>
              <h3 key="title">{title}</h3>
              <p key="description">{text}</p>
            </motion.article>
          ))}
        </div>
      </section>

      <section className="j-business-teaser">
        <div>
          <span className="eyebrow">FOR THE BIGGER PICTURE</span>
          <h2>
            One property is a start.
            <br />
            <em>A portfolio is a perspective.</em>
          </h2>
          <p>
            Find poorly performing homes, compare feasible improvement potential
            and prioritise the next assessment.
          </p>
          <Link className="button" href="/business">
            Explore the business dashboard <ArrowUpRight size={17} />
          </Link>
        </div>
        <div className="j-portfolio-preview j-float-card">
          <div>
            <span>PORTFOLIO / EXAMPLE VIEW</span>
            <BarChart3 size={16} aria-hidden />
          </div>
          {[
            "Find homes that need attention",
            "Rank feasible improvement potential",
            "Compare energy, carbon and value",
          ].map((text, index) => (
            <div className="j-preview-row" key={text}>
              <span className="j-list-num">0{index + 1}</span>
              <span>{text}</span>
              <Check size={16} aria-hidden />
            </div>
          ))}
        </div>
      </section>

      <section className="j-cta">
        <span className="eyebrow">YOUR PROPERTY. YOUR NEXT CHAPTER.</span>
        <h2>
          Let’s make
          <br />
          <em>something better.</em>
        </h2>
        <Link className="button primary" href="/home">
          Start my property plan <ArrowUpRight size={19} />
        </Link>
        <small>Your name, your details, a plan with reasons.</small>
      </section>
    </div>
  );
}
