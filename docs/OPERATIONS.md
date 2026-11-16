# Backend Operations Contract

## Health and readiness

`GET /health` is authenticated when `AUTH_SECRET` is configured. It returns `ok` when the default agent and persistence initialized successfully, and `degraded` with a list of optional agents when non-critical capabilities failed.

The process must not be considered ready until the FastAPI lifespan has completed. A failure to initialize the checkpointer, store, or default `portfolio-agent` prevents startup.

## Observability

Every request should be correlated using the LangGraph `run_id`, logical `user_id`, and logical `thread_id`. Do not log bearer tokens, provider API keys, prompts containing secrets, or raw uploaded audio.

Monitor:

- request count, 4xx/5xx rate, and p50/p95/p99 latency;
- stream disconnects, terminal `[DONE]` completion, and token latency;
- agent load failures, provider failures, MCP failures, and degraded-agent count;
- checkpoint/store latency and connection-pool exhaustion;
- voice upload rejection rate and synthesis/transcription latency;
- LLM token usage and estimated cost where provider metadata is available.

## Deployment and rollback

Use a rolling or blue/green deployment with readiness checks. Deploy dependency and schema changes before application changes when migrations are required. Keep the previous image available for immediate rollback and verify `/health`, `/info`, invoke, stream, history, and AG-UI smoke checks after deployment.

## Data protection and recovery

Checkpoint databases require automated backups and tested restores. The target initial service objective is RPO of 1 hour and RTO of 30 minutes unless deployment-specific requirements are stricter. Thread deletion is user-scoped and must be verified against the configured persistence backend.

## Capacity assumptions

Start with measured limits rather than premature sharding: one API replica plus one standby, bounded database pools, a 25 MiB voice upload limit, and request/provider timeouts. Revisit caching, queue workers, and horizontal partitioning when metrics show sustained CPU, latency, connection, or queue-depth pressure.
