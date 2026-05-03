# SCALE TO 1 BILLION
**The Complete Developer Reference**
*Java • Python/FastAPI • SQL • MongoDB • Kafka • Redis • Kubernetes*

## PRE-CODING CHECKLIST — Ask Before Every Feature
1. What is the Big O of my algorithm? Avoid O(n²) or worse.
2. Am I querying a database inside a loop? Always batch.
3. Should this response be cached in Redis?
4. Should this be async via Kafka instead of blocking the thread?
5. What happens if this service fails? Do I have a fallback?
6. Am I loading more data than needed? Use SELECT columns, LIMIT.
7. Is there a connection pool configured for DB and HTTP clients?
8. Am I validating and sanitizing ALL incoming input?
9. Are ALL secrets in environment variables, not in code?
10. Do I have proper error handling and timeouts everywhere?
11. Will this code still work with 1 billion rows in the database?
12. Am I logging enough context to debug a production issue?

*(Full guidelines from Section 1 to 14, including Algorithms, Database Optimization, Caching Strategy, Java/Python Best Practices, Event-Driven Kafka, API Design, Security, Code Structure, Performance, Monitoring, Deployment, and Testing for Scale are applied across this codebase).*

## FINAL MASTER CHECKLIST
| Category | What to Verify |
| :--- | :--- |
| Algorithm | Big O is O(n) or better for all hot paths |
| Database | All search columns indexed, no SELECT *, no loop inserts |
| Cache | Hot data cached in Redis with TTL set |
| Async | Heavy/slow work pushed to Kafka or background task |
| Failures | Circuit breaker + fallback on every external call |
| Timeouts | Every HTTP call and DB query has explicit timeout |
| Validation | All user input validated and sanitized |
| Secrets | Zero secrets in code — all in environment variables |
| Logging | Errors logged with context, trace ID attached |
| Health Check | /health endpoint returns DB, Kafka, Redis status |
| Load Test | k6 test run — p99 < 1s under 10x expected traffic |
| Pagination | No endpoint returns unbounded list of results |
| Connection Pool | DB and HTTP clients use connection pooling |
| Graceful Shutdown | Service finishes in-flight requests before stopping |
| Idempotency | All payment and critical operations are idempotent |
