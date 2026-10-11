# Green Home Twin: project reference

The current frontend is based on the user's product request and the two supplied Lloyds PDFs. The PDFs describe the wider system, including backend modelling and evaluation; they are reference material, not instructions to implement a new ML service in this repository.

## Source documents

| Supplied file | Saved original | Searchable text | Role |
| --- | --- | --- | --- |
| `ps2 lloyds.pdf` | [Display brief](references/ps2-lloyds.pdf) | [Extracted text](references/ps2-lloyds.txt) | Slide-style presentation of the sections and outputs to show in the UI |
| `LLOYDS-ps2.pdf` | [Full scenario](references/lloyds-ps2.pdf) | [Extracted text](references/lloyds-ps2.txt) | Detailed requirements and context for frontend/backend integration |

Extraction preserves the source wording but may contain PDF layout artifacts. Refer to the originals for visual layout. Figures labelled illustrative in these documents are examples, not estimates for a user's property.

## Product decisions and this delivery

- Keep the cozy ivory, moss green, lilac and peach palette, motion, and interactive landing-page feel.
- Remove the house model and all frontend 3D visualisation. Use report cards, comparisons, charts and explanations to make the results understandable.
- Collect the user's name, goal and property information, then use their name in the personal journey.
- Prepare sections for model outputs and the backend LLM's structured explanation, including separate reasons for why a score or recommendation was returned. This delivery shows clearly labelled static illustrations in those sections.
- Keep this handoff frontend-only, with no active API connection or bundled backend. The user's friend will connect their backend later.
- What-if choices propose a scenario. Once integrated, the backend must rerun the relevant models and calculations, then the LLM explains the confirmed result. Changing a control alone must not manufacture a new estimate in the browser.
- Keep a separate business view for finding poorly performing homes and prioritising feasible improvements.
- Cards and hover details can lift or float out, with keyboard focus equivalents and reduced-motion support.

## Screen-to-reference mapping

Slide numbers below refer to the numbered sections inside the first PDF, not the PDF page index. The table maps intended system outputs to the frontend sections; this standalone delivery fills them with labelled static samples.

| Frontend area | Required display | Display brief | Full scenario |
| --- | --- | --- | --- |
| Landing and intake | Explain the four customer questions; collect property characteristics, annual electricity and gas, current features, goal and constraints | 01, 09 | 1, 8–9 |
| Assessment overview | Green Home Score out of 100, classification, key issues, report status and available/missing data | 03 | 2–3, 8 |
| Why this score? | All seven component sub-scores, fixed weights, contribution and reasons, with the backend LLM's explanation | 02–03 | 1–2, 8 |
| Retrofit recommendations | Prioritised feasible improvements, High/Medium/Low suitability, estimated savings and the reason/ordering for each | 05 | 4 |
| Scenario comparison | Baseline versus confirmed post-retrofit package; show the selected scope and per-fuel changes; preserve unavailable results | 04, 06 | 3, 5, 8 |
| Energy report | Electricity and gas in kWh/year separately, baseline and after, individual retrofit estimates and package estimates; consumption increases remain negative savings | 06 | 5 |
| Carbon report | Estimated annual reduction in kg or tonnes CO₂e/year and source/method notes from the backend | 07 | 6 |
| Property-value report | Current baseline, indicative low–high potential value and uplift range, consistent comparison, limitations and assumptions | 08 | 7 |
| LLM report and questions | Structured explanation, evidence-linked reasons, missing-data notes and a separate “why?” response grounded in the confirmed result | 02, 09 | 1, 8, 11 |
| Business dashboard | Poor/Very poor flags, key issues, filters, property comparison, ranking by returned improvement potential and export | 04–06 | 3–5, 8 |

## Display rules for future real outputs

The fixed score weights are Energy efficiency 25%, Energy consumption intensity 20%, Insulation 15%, Heating system 15%, Windows and glazing 10%, Renewable energy 10%, and Smart energy management 5%. Display the backend's component contribution; do not present a browser-side score as a model result.

Classifications are Highly efficient (80–100), Good (65–79), Moderate (50–64), Poor (30–49), and Very poor (0–29). The backend owns reported score/classification. A large home must not be described as inefficient merely because its total energy use is larger; use the returned intensity and property context.

Improvement potential describes estimated reduction in purchased energy: grid electricity imports plus gas. If the backend cannot establish a valid baseline, display “Unavailable” with its reason. Solar reduces grid imports, not underlying demand. A heat pump may increase electricity consumption while reducing gas; display both signs clearly.

Show savings as estimates, not guarantees. Package results come from the backend's combined scenario, rather than adding individual retrofit estimates. Carbon results must retain the backend's per-fuel methodology, units and documented factor sources. Missing factors or insufficient data must be visible rather than silently replaced with zero.

Property-value impact is always an indicative range, never a guaranteed increase or a single predicted uplift. Preserve location, property-size, type and market limitations supplied by the backend. The PDFs' example of £350,000 and 2–5% is illustrative, not a universal retrofit rule.

## Responsibility boundary

| Frontend | Friend's future backend integration |
| --- | --- |
| Intake, accessible interactions, named greetings, layout and visualisation | Input preparation, feature engineering and missing/conflicting-data handling |
| Send property/scenario data and show request status/errors | Green Home Score and component contributions |
| Display confirmed outputs with units, provenance and limitations | Efficiency detection, feasible retrofit ranking, individual and package estimates |
| Present the LLM's structured report and grounded “why?” answers | Per-fuel energy, carbon with sourced factors and indicative value-range estimation |
| Track selected upgrades separately from confirmed report results | Rerun relevant models for a what-if, then invoke the LLM using computed outputs |
| Local browser persistence and export of the visible report/portfolio | Authentication, secure secrets, model/LLM execution and persistent customer memory if supported |

The frontend defaults to a fixed, labelled sample illustration for a synthetic property. Three stored personal plans are available: starting home, insulation with solar, and the complete five-upgrade package. Other selections explain that the future backend is needed; they make no network request. The frontend does not run ML, call an LLM or estimate outcomes from personal inputs. Browser localStorage stores the user's name, goal and property details, while exports distinguish those details from the sample report. The business dashboard uses a synthetic sample portfolio. Local persistence is not the optional backend customer-memory system described in the references.

## Future backend handoff

`lib/model.ts` supplies `Property`, `Scenario` and `StructuredDraft` display types. `lib/api.ts` is a disabled seam for the user's friend to implement. The current handoff has no server endpoint dependency, backend setup requirement or live response.

The sample UI keeps the current Green Home Score separate from package energy/carbon/value illustrations. It does not infer an after-score, projected EPC or missing package cost. Value stays an indicative range. The structured report and reasons are fixed sample text, not real ML or LLM outputs.

[backend-contract.md](backend-contract.md) describes the frontend functions and types to map to the friend's API later. A future connection must provide confirmed scenario outputs before the LLM explains them, preserve missing values, and tie explanations to the right property/scenario. The current frontend does not establish backend compatibility or model quality.

## Scope of this repository

This task updates the existing frontend. The references' dataset generation, model training, held-out evaluation, LLM evaluation targets and hackathon submission requirements describe the full system and remain backend/team responsibilities. Their inclusion here provides durable project context; it does not make those deliverables part of the frontend or imply they have been completed.
