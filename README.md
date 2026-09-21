# AI Parent Tutor — Production-Oriented Reference Implementation

A secure, scalable learning platform architecture: parents upload textbook chapters; the system extracts and indexes content, uses RAG + LLMs to build concept-first lessons, generates narrated educational video asynchronously, and evaluates student answers.

## Important production note
This repository is a strong engineering foundation/reference implementation, not a claim of compliance with every child-safety/privacy law. Before public launch, complete legal review, consent/age-verification requirements, data-retention rules, vendor DPAs, security testing, abuse testing, and a formal threat model.

## Stack
- FastAPI, SQLAlchemy 2, PostgreSQL + pgvector
- Redis + Celery workers
- Groq via LangChain provider adapter
- Sentence Transformers embeddings
- LangGraph can be added around the AI service as the orchestration boundary
- S3-compatible object storage
- FFmpeg + TTS adapter for narrated video
- Prometheus metrics
- Docker
- Flutter client skeleton

## Run locally
1. Copy `.env.example` to `.env` and fill `GROQ_API_KEY` and `SECRET_KEY`.
2. `docker compose up --build`
3. In another shell: `docker compose exec api alembic upgrade head`
4. Open `http://localhost:8000/health`.
5. Development OpenAPI: `http://localhost:8000/docs`.

## API flow
1. `POST /api/v1/auth/register`
2. `POST /api/v1/children`
3. `POST /api/v1/chapters` with multipart PDF
4. `POST /api/v1/lessons/generate?chapter_id=...`
5. Poll the returned Celery job through your job-status endpoint (recommended production addition) or query lesson records.
6. `GET /api/v1/lessons/{lesson_id}`
7. `POST /api/v1/learning/answer`

## Production hardening checklist
- Managed PostgreSQL with backups/PITR and pgvector.
- Private S3 bucket, KMS encryption, short-lived signed URLs.
- WAF, CDN, TLS, rate limits, bot protection.
- OIDC provider/MFA for parents and admins; short-lived access tokens and refresh-token rotation.
- Separate parent/child authorization; never trust IDs supplied by clients.
- Per-family tenant checks on every resource query.
- Malware scanning/quarantine before processing uploads.
- Content moderation and prompt-injection-resistant document handling.
- Secret manager instead of `.env` in production.
- OpenTelemetry traces, Prometheus/Grafana metrics, structured logs, alerting.
- Dead-letter queue and idempotent workers.
- Automated tests, dependency scanning, SAST, container scanning.
- Formal privacy policy, parental consent flows where required, deletion/export workflows and documented retention.
- Human review process for safety incidents.

## Video architecture
The included renderer creates simple narrated educational slides with FFmpeg. The `VideoRenderer` class is intentionally an adapter boundary: plug in a commercial TTS/image/video provider without changing the lesson domain model.

## Scaling
Run API and workers separately. Scale workers horizontally by queue type: document indexing, lesson generation, video rendering. Cache reusable curriculum assets and avoid regenerating identical videos.
