# Deployment architecture

## Service layout

```text
Browser
  -> Vercel (Next.js)
  -> Render API (FastAPI)
       -> Supabase PostgreSQL + pgvector
       -> Supabase Storage
       -> Upstash Redis
  -> Render worker (Celery)
       -> Supabase PostgreSQL + Storage
       -> Upstash Redis
```

Vercel serves only the Next.js app. Render runs two services from the backend Dockerfile: the FastAPI HTTP API and Celery worker. Supabase provides Auth, Storage, and PostgreSQL; pgvector must be enabled in the target database. Upstash Redis is shared by API and worker as the Celery broker and result backend.

## Provisioning

1. Create a Supabase project, enable the `vector` extension, and create the `documents` storage bucket.
2. Create an Upstash Redis database. Use its TLS `rediss://` URL for both Celery variables.
3. Create a Render Blueprint from `render.yaml`, or create equivalent API and worker services manually.
4. Import `frontend` into Vercel. Set its Root Directory to `frontend`.
5. Point `app.example.com` at Vercel and `api.example.com` at Render. Set `NEXT_PUBLIC_API_URL=https://api.example.com` in Vercel, then redeploy.
6. Set `CORS_ORIGINS=https://app.example.com` on the API. Add Vercel/custom domains to Supabase Auth redirect URLs and allowed origins.

## Secrets and environment variables

Never commit these values. Configure them in Render and Vercel dashboards.

| Service | Required variables |
| --- | --- |
| Render API | `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `SUPABASE_KEY`, `GEMINI_API_KEY`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `CORS_ORIGINS` |
| Render worker | `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `SUPABASE_KEY`, `GEMINI_API_KEY`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` |
| Vercel | `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` |

`SUPABASE_KEY` and `SUPABASE_SERVICE_ROLE_KEY` are privileged secrets. They must never be exposed in `NEXT_PUBLIC_*` values.

## Production settings

- Use a pooled Supabase connection URL compatible with SQLAlchemy asyncpg.
- Set `APP_ENV=production` and an explicit HTTPS `CORS_ORIGINS` value.
- Run `alembic upgrade head` as part of the API release command (configured in `render.yaml`).
- Configure Render health checks for `/health/`, worker-failure alerting, and log retention.
- Use separate production and preview projects/databases where legal-data isolation requires it.
