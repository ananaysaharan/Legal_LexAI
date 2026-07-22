# Legal LexAI Backend

FastAPI backend for Legal LexAI's document-grounded research workflow.

## Capabilities

- Case-scoped document storage, PDF parsing, chunking, embeddings, and pgvector retrieval
- Grounded Gemini chat through LiteLLM with structured citations
- PostgreSQL conversation persistence and bounded recent-history injection
- Rule-based intent detection for high-level legal requests
- Declarative execution-plan generation with no execution side effects

## Setup

Create `backend/.env` with application, database, Supabase, and Gemini settings:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_saas
SUPABASE_URL=your-supabase-url
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
SUPABASE_KEY=your-supabase-service-role-key
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini/gemini-2.0-flash
```

Install dependencies, migrate, and run:

```bash
uv sync
alembic upgrade head
uv run uvicorn src.api.main:app --reload
```

## Core endpoints

- `POST /cases/{case_id}/search` — semantic retrieval
- `POST /cases/{case_id}/chat` — grounded RAG chat
- `POST /intents/detect` — task classification
- `POST /plans` — non-executing JSON execution plan

## Validation

```bash
uv run python -m unittest discover -s tests -v
```
