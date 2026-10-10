# Megathon Starter

A reusable full-stack starter for a hackathon: Next.js App Router + Tailwind CSS frontend, FastAPI backend, and optional Supabase persistence. Do not use until the event rules permit prebuilt starter code.

## Local setup

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Visit http://localhost:3000. Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` (default http://localhost:8000).

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

Visit http://localhost:8000/docs and http://localhost:8000/health.

## Deployment

- **Frontend**: Import this repository into Vercel; set root directory `frontend`, framework Next.js, and `NEXT_PUBLIC_API_URL` to deployed backend URL.
- **Backend**: Create Render Python web service; root directory `backend`; build command `pip install -r requirements.txt`; start command `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- **Backend env**: Configure `FRONTEND_ORIGIN` to your Vercel domain. Configure `GEMINI_API_KEY`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY` only when actually needed. Never expose service-role credentials to the client.
- **Database**: Paste `database/migrations/001_initial.sql` into Supabase SQL editor when needed; table is protected by RLS. Backend can write using the service role when authorized, but client reads/writes require explicit policies.

## Architecture

Frontend --> FastAPI --> optional Gemini / external data / Supabase.

Avoid putting secrets in `NEXT_PUBLIC_` variables. Start with a `/health` check and one end-to-end feature, then expand.

## GitHub

Create an empty GitHub repository named `megathon-starter` (do not initialize with README), then from the project folder:

```bash
git init
git add .
git commit -m "chore: scaffold hackathon starter"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/megathon-starter.git
git push -u origin main
```
# megathon26-4bits
