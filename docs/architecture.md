# Architecture

## Request path
Flutter/Web -> HTTPS Load Balancer/WAF -> FastAPI -> PostgreSQL/Redis/S3/AI providers.

## Asynchronous path
Upload -> object storage -> queue -> document worker -> embeddings -> PostgreSQL/pgvector.
Lesson request -> queue -> lesson worker -> RAG -> LangGraph -> LLM -> lesson JSON -> video worker -> TTS/visuals/FFmpeg -> private S3 -> signed URL.

## Data boundaries
PostgreSQL stores metadata and learning state. Object storage stores large binary assets. pgvector stores embeddings beside tenant-scoped chunks. Redis stores queues/cache only; do not use it as the source of truth.

## RAG
Retriever always filters by chapter/tenant ownership before similarity search. Retrieved text is untrusted context and must never be treated as instructions.

## Model gateway
All LLM calls go through a provider abstraction so models can be changed without changing domain code. Track provider/model/latency/token metadata for observability and cost controls.
