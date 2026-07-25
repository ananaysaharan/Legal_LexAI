# Legal LexAI

Legal LexAI is a case-scoped legal research application that turns uploaded PDFs into grounded, citation-backed AI answers and structured legal workflows.

## What is implemented

### Document intelligence

- Supabase-backed authentication and case ownership controls
- Case and PDF document management
- PDF text extraction with page-level storage
- Structure-aware chunking with page, section, and clause metadata
- FastEmbed embedding generation
- PostgreSQL + pgvector semantic similarity search with HNSW indexing

### Grounded RAG chat

- Case-authorized Top-K retrieval
- Versioned prompt construction separated from application code
- Gemini generation through LiteLLM
- Responses constrained to retrieved context
- Structured citations containing document name, page number, and chunk ID
- Citation metadata persisted alongside assistant messages
- PostgreSQL-backed conversations and messages
- Recent conversation-history injection with configurable message and character windows

### Legal task intelligence

- Rule-based intent detection for contract review, document summaries, comparisons, response drafting, risk-clause analysis, and standard Q&A
- Structured `Intent` responses with confidence and execution hints
- Declarative JSON execution plans for each supported intent
- Planner/executor separation: plans describe work but perform no retrieval, generation, or side effects

### Frontend experience

- Next.js + Tailwind + shadcn/UI case workspace
- Polished research chat interface with progressive answer rendering
- Markdown answer display, auto-scroll, typing state, and error handling
- Conversation sidebar for in-session research threads
- Citation cards that open the protected PDF viewer at the cited page

## Architecture

```text
User request
  -> Intent detection
  -> Execution plan (declarative only)
  -> Retrieval (pgvector)
  -> Prompt construction
  -> Gemini via LiteLLM
  -> Grounded answer + citations
  -> PostgreSQL conversation persistence
```

The current RAG chat route uses retrieval, prompt construction, Gemini generation, citations, and conversation persistence directly. Intent detection and planning are separate services, ready for a future execution/orchestration layer.

## Key API endpoints

| Endpoint | Purpose |
| --- | --- |
| `POST /cases/{case_id}/documents` | Upload and process a PDF |
| `POST /cases/{case_id}/search` | Retrieve semantically relevant chunks |
| `POST /cases/{case_id}/chat` | Produce a grounded chat answer with citations |
| `POST /intents/detect` | Classify a high-level legal request |
| `POST /plans` | Produce a non-executing JSON plan from an intent |

## Local development

### Docker development stack

Copy the container environment template, fill the Supabase and Gemini values, then start the hot-reload stack:

```bash
cp .env.example .env
docker compose -f docker-compose.dev.yml up --build
```

This exposes Next.js at `http://localhost:3000`, FastAPI at `http://localhost:8000`, PostgreSQL at `localhost:5432`, and Redis at `localhost:6379`. The development Compose file bind-mounts backend and frontend source while keeping container-local `node_modules` and Next build output in named volumes.

### Docker production stack

```bash
cp .env.example .env
# Replace every placeholder in .env before deployment.
docker compose up --build -d
```

The production build uses multi-stage Dockerfiles: build toolchains and Node dependencies remain in build stages, while final API and web images contain only runtime dependencies and run as non-root users. Public Next.js variables are build arguments because Next.js embeds them in its browser bundle; keep private Supabase and Gemini credentials only in the API/worker environment.

`postgres_data` and `redis_data` are durable named volumes. PostgreSQL runs the pgvector extension initializer on first volume creation. The API and web services share the public network; PostgreSQL, Redis, and Celery worker use the private internal network, with only API and web ports published. Background work is processed with:

```bash
docker compose exec worker celery -A src.api.tasks.celery_app inspect ping
```

Jobs are tracked in PostgreSQL and expose queued, running, succeeded, and failed states. Celery retries transient failures with exponential backoff; permanent failures retain error metadata for recovery or manual retry.

### Backend

```bash
cd backend
uv sync
alembic upgrade head
uv run uvicorn src.api.main:app --reload
```

Set the required database, Supabase, and Gemini environment variables in `backend/.env`. See [backend/README.md](backend/README.md) for details.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set the API and Supabase variables in `frontend/.env.local`. See [frontend/README.md](frontend/README.md) for details.

## Validation

```bash
cd backend && uv run python -m unittest discover -s tests -v
cd frontend && npm run build
```

## Planned next steps

- Planner execution and approval gates
- LLM-backed intent/planning fallback for ambiguous requests
- Long-term memory and conversation summarization
- Advanced hybrid retrieval and reranking
- Per-claim citation alignment and legal review workflows
