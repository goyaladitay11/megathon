# Reliable local development

Run **both** Green Home Twin servers using one command from the repository root:

```bash
git checkout main
git pull origin main
cd ~/Downloads/megathon
python3 scripts/dev.py
```

Prerequisites (once, only if dependencies are missing):

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cd ../frontend
npm ci
cd ..
```

The launcher:
- Selects currently free ports, preferring **8766** for FastAPI and **3020** for Next.js. It does not kill or reuse unrelated processes.
- Passes the actual backend URL to Next.js as `NEXT_PUBLIC_API_URL`, overriding stale `.env.local` API addresses for this process.
- Configures CORS only for the frontend address it launches.
- Waits for backend health, runs a real assessment and retrofit simulation, and verifies CORS preflight **before** launching Next.js.
- Prints the actual browser URL once ready and stops only the processes it started when you press Ctrl+C.

**Always open the READY address printed in Terminal**, not an old bookmarked port. Keep the terminal open during your demo. Do not launch another `uvicorn` or `npm run dev` concurrently.

The frontend also cancels stale assessment requests when input details change, and shows a retry action when a request fails.

The optional Gemini API key lives in `backend/.env`, never in the frontend. `gemini_active: false` means deterministic explanation fallback is used.

If the startup smoke check fails, inspect the error printed by this command rather than retrying random ports. If your project is in a different folder (such as `megathon-green-clean`), run the launcher from **that same repository clone** after pulling main.

## Regression check

With backend dependencies installed:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_frontend_contract.py -q
```

Frontend type check:

```bash
cd frontend && npm run typecheck
```

These checks are not substitutes for an end-to-end browser check on your Mac.
