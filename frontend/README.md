# Legal LexAI Frontend

The Next.js interface for Legal LexAI's case-scoped, evidence-grounded RAG workflow.

## Features

- Secure case and PDF document management
- AI research chat with progressive response rendering
- Markdown-formatted answers and evidence citation cards
- Citation links that open the cited PDF at the relevant page
- In-session conversation sidebar with local browser persistence
- Loading, typing, empty, and error states for the RAG demonstration flow

## Run locally

Create `frontend/.env.local` with the API and Supabase settings used by your environment:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
```

Install dependencies and start the app:

```bash
npm install
npm run dev
```

The application is available at [http://localhost:3000](http://localhost:3000).

## Validation

```bash
npm run build
```

## API integration

The case chat UI calls `POST /cases/{case_id}/chat`. It renders the returned answer, source chunks, and structured citations without changing the backend API contract.
