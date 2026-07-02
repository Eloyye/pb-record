# Local monolith: FastAPI + React + Postgres + background GPU worker

The system is a single **local** application on the machine with the RTX 5080, structured as a monorepo: a **FastAPI** backend (SQLAlchemy + Alembic), a **React** SPA, and a **background worker** that runs the GPU pipeline off a job queue. Data lives in a local **Postgres**. There is no auth and no multi-tenancy — it serves one user on localhost.

We chose this because the GPU, the multi-GB video files, and the single user are all local, which removes cloud infra, auth, and upload/egress concerns. And because processing a match is a minutes-to-hours job, it must run **asynchronously** via the worker, never in a request handler.

## Consequences

- The worker (writes) and the API (reads, plus review corrections) share one Postgres — the reason SQLite was passed over.
- "Monolith" here means one app / one deploy, not one language: the React SPA is a deliberate second language + build step, accepted for the review/labeling UX.
- Postgres adds one local service (a container), accepted for analytics SQL and to avoid a later migration.
