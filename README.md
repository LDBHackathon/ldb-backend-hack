# LDB DVA Backend

API backend for the LDB × Nomba hackathon. It lets merchants onboard, provision **dedicated virtual accounts (DVAs)** for their end customers via Nomba, reconcile inbound transfers, and receive outbound webhook events.

## What it does

- **Merchant portal** — registration, session auth, KYB onboarding, dashboard, settings
- **Developer API** — create customers, issue DVAs, read statements and transactions
- **Nomba integration** — per-customer sub-accounts, virtual account provisioning, inbound webhooks
- **Reconciliation** — match transfers to customers, handle partial/over/misdirected payments
- **Outbound webhooks** — notify merchant systems (`wallet.credited`, `payment.partial`, etc.)
- **File storage** — KYB document uploads via Cloudinary

## Tech stack   

- Python 3.14, FastAPI, Tortoise ORM (PostgreSQL)
- Redis (rate limiting, Nomba token cache)
- Nomba sandbox/live API, Cloudinary
- Docker + GitHub Actions → DigitalOcean

## Project structure

```
app/
  api/          # Routes, controllers, auth
  services/     # Business logic
  integrations/ # Nomba, Cloudinary, Redis
  models/       # Database models
  migrations/   # Aerich migrations
tests/
```

## Getting started

```bash
uv sync
cp .env.template .env            # local uvicorn
cp .env-hack.template .env-hack  # docker compose

make run          # http://localhost:8070
make run-docker   # docker compose
make migrate-up   # apply migrations
make test-pytest  # run tests
```

| Environment | Host port | Env file |
|-------------|-----------|----------|
| Local / dev | 8070 | `.env` or `.env-hack` (Docker) |
| Production | 8080 | `.env-hack` on server |

Interactive API docs: http://localhost:8070/docs

## Documentation

- **[API Flow Guide](API_FLOW.md)** — step-by-step integration flow (auth → KYB → customers → payments → webhooks)

## Deployment

Pushes to `dev` and `main` trigger GitHub Actions: test → Docker build → deploy to DigitalOcean.

- `dev` branch → port **8070**, image `ldb-dva-be-dev`
- `main` branch → port **8080**, image `ldb-dva-be`

See `.github/workflows/build.yml` and `.env-hack.template` / `.env-dev.template` for server setup.
