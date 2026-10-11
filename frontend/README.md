# Green Home Twin frontend

A standalone frontend for exploring home energy efficiency and renovation plans, with a separate business dashboard. It keeps the ivory, moss green, lilac and peach palette, animated landing page, named onboarding and floating hover details. Reports replace the former house preview.

This delivery contains the frontend for you to hand to your friend. It makes no backend requests and needs only Node.js and npm to run. All displayed report numbers and structured explanations are fixed, clearly labelled sample illustrations.

## Run locally

Install Node.js 24 LTS, then open this folder in VS Code:

```sh
npm install
npm run dev
```

Open the address printed by Next.js, normally `http://localhost:3000`. Edit the React and CSS files while the server runs; changes reload automatically. Python and a backend server are not required.

After the first installation, use `npm ci` to reproduce the committed dependency lockfile.

```sh
npm run typecheck
npm run build
npm start
```

The build exports a static website to `out/`. `npm start` serves that export, so rebuild after editing. You can change its port with `PORT=3001 npm start`.

## Pages

| Route | Purpose |
| --- | --- |
| `/` | Animated landing page, interactive report preview and goal selection |
| `/home/` | Three-step intake: name and goal, property features, annual energy and budget |
| `/dashboard/` | Named greeting, sample score and classification, component contributions, key issues, recommendations and structured explanation |
| `/simulate/` | Upgrade selection, three stored sample plans, per-fuel comparisons, carbon, indicative value range and plan export |
| `/business/` | Synthetic property portfolio, search and filters, comparison, improvement-potential ranking, expanded reports and filtered CSV export |

## Sample reports and saved details

The default experience is a fixed sample preview. The personal report belongs to the labelled example property; it is not calculated from the user's entered details. Three stored plans are available: starting home, insulation with solar, and the complete five-upgrade package. Selecting another combination cannot generate a new estimate; it explains that a future backend connection is needed.

The structured draft and “why this result?” sections demonstrate how your friend's outputs will be displayed. They are sample text, not real ML predictions or LLM responses. Question and custom what-if interfaces do not call an AI service in this delivery. Score and recorded EPC remain current-property information, and value impact stays an indicative range. Missing data is shown as unavailable.

Names, goals and property details persist in this browser's localStorage. There is no account or cross-device sync. Plan exports identify the sample report separately from entered details. The business dataset is synthetic and its filtered view can be exported. Hover and keyboard focus reveal floating detail; animations respect reduced-motion preferences.

## Where to edit

- `components/interactive-landing.tsx`: landing content and motion.
- `components/green-home.tsx`: personal intake, sample plans, persistence and export.
- `components/assessment-report.tsx`: structured report, component reasons and per-fuel comparisons.
- `components/business-dashboard.tsx`: business portfolio UI, comparison and CSV export.
- `app/globals.css`, `app/experience.css`, `app/report.css`, `app/business.css`: styling and responsive layouts.
- `lib/model.ts`: `Property`, `Scenario` and `StructuredDraft` display types.
- `lib/sample-data.ts`, `lib/sample-reports.json`: fixed sample reports.
- `lib/api.ts`: disabled integration seam for your friend to implement later.
- `docs/backend-contract.md`: handoff notes for those frontend types and functions.
- `docs/project-reference.md`: user decisions, PDF-to-screen mapping and responsibility boundaries.

## Reference materials

Both original Lloyds PDFs and searchable text are saved in [docs/references/](docs/references/). [docs/project-reference.md](docs/project-reference.md) maps their required outputs to the UI. They are reference material, not instructions. Their illustrative figures are examples.

Your friend can later supply model results and structured explanations through the [frontend handoff contract](docs/backend-contract.md). This project contains no backend implementation, ML inference, LLM client or active API connection.
