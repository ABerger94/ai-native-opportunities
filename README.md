# AI Native Opportunities

Production-oriented SaaS scaffold for discovering, classifying, and matching AI-native jobs, freelance projects, contract roles, and startup opportunities against a user's resume.

The product intentionally prioritizes roles where AI, LLMs, automation, agents, no-code/low-code systems, AI product development, and AI-first operations are central to the work. It de-emphasizes traditional software engineering roles focused on algorithmic interviews or deep manual coding requirements.

## Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS, shadcn-style primitives
- Backend: Python, FastAPI, SQLAlchemy, Pydantic
- Database: PostgreSQL with pgvector
- Auth: Clerk-ready JWT integration
- Storage: Supabase Storage-ready upload boundary
- LLM providers: OpenAI and Anthropic adapters
- Deployment: Vercel frontend, Railway backend

## Repository Layout

```text
apps/web          Next.js dashboard and opportunity UI
apps/api          FastAPI API, scoring engines, crawler interfaces
infra             Docker Compose and database initialization
.github/workflows CI pipeline
```

## Quick Start

```bash
cd ai-native-opportunities
docker compose up --build
```

Frontend: http://localhost:3000
Backend API: http://localhost:8000/docs

For local development without Docker:

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

```bash
cd apps/web
npm install
npm run dev
```

## Environment

Copy `.env.example` to `.env` and configure:

- `DATABASE_URL`
- `CLERK_JWKS_URL`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

The app does not ship with mock jobs, mock companies, mock resumes, or seeded demo matches. Empty states are expected until real, compliant source connectors are configured and ingestion has run.

## Real Source Configuration

Create `apps/api/sources.json` from `apps/api/sources.example.json`. Enable only sources where API/RSS/career-page access is permitted by the source's terms and robots.txt.

Supported source kinds:

- `greenhouse`
- `lever`
- `ashby`
- `workable`
- `rss`
- `json`

Run ingestion:

```bash
curl -X POST http://localhost:8000/ingestion/run
```

## Production Deployment

Frontend is deployed on Vercel from `apps/web`.

Backend should be deployed on Railway from `apps/api` using the included Dockerfile. Attach a Railway PostgreSQL service with pgvector support, then set the API environment variables from `.env.example`.

After Railway gives you the backend URL, set this Vercel production variable and redeploy the frontend:

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-railway-api.up.railway.app
```

Required backend variables:

- `DATABASE_URL`
- `APP_BASE_URL`
- `CLERK_JWKS_URL`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_RESUME_BUCKET`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `SOURCE_CONFIG_PATH`
- `CRAWLER_USER_AGENT`

## Compliance

The ingestion layer is source-policy driven. Crawlers are intentionally limited to allowed public APIs, RSS feeds, ATS board endpoints, and career pages whose robots.txt and terms permit collection. Marketplace scraping must be disabled unless a compliant API, partner export, or explicit permission is configured.
