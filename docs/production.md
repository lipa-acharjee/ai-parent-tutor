# Production runbook

## Deploy
1. Build/test container in CI.
2. Push immutable image tag to ECR/registry.
3. Run database migrations as a one-off deployment job.
4. Deploy API and worker separately.
5. Wait for health checks.
6. Verify `/health`, metrics and queue depth.

## Scale
- API: horizontal autoscaling on CPU/request latency.
- Document workers: scale on indexing queue depth.
- Lesson workers: scale on AI job queue depth.
- Video workers: scale separately because FFmpeg is CPU/memory intensive.

## Reliability
- Idempotency keys for expensive generation requests.
- Retry transient AI/storage errors with exponential backoff.
- Dead-letter failed jobs.
- Timeouts around external providers.
- Circuit breaker/fallback provider for critical AI paths.
- Database backups + point-in-time recovery.

## Cost controls
- Cache embeddings.
- Deduplicate identical uploads by checksum.
- Reuse curriculum video assets.
- Limit maximum chapter pages and generation frequency.
- Track tokens and provider cost per family/tenant.
- Add quotas by subscription tier.
