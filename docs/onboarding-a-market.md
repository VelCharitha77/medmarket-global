# Onboarding a New Marketplace — Runbook

Demonstrated by onboarding Singapore (APAC-SG) as marketplace #11.

## What was changed

| File | Change |
|---|---|
| `connectors/sg_providers/extract.py` | NEW — 50-line Faker script generating Singapore providers |
| `connectors/sg_providers/requirements.txt` | NEW — `faker` |
| `connectors/sg_providers/Dockerfile` | NEW — standard connector template (identical to all others) |
| `docker-compose.yml` | ADDED 8 lines — new service block for sg-providers-connector |
| `engine/cli.py` | ADDED 2 lines — new extract job + added to load_raw depends_on |
| `engine/loader.py` | ADDED ~15 lines — new raw_sg_providers table + load section |
| `dbt/models/staging/stg_sg_providers.sql` | NEW — standard staging template |
| `dbt/models/staging/sources.yml` | ADDED 2 lines — new source table entry |
| `dbt/models/marts/core/dim_provider.sql` | ADDED 5 lines — UNION ALL with sg_providers |

## What was NOT changed (the proof point)

- Orchestration engine core (`engine/job.py`, `engine/dag.py`, `engine/scheduler.py`) — ZERO changes
- All existing connectors — ZERO changes
- All existing staging models (stg_providers, stg_patients, etc.) — ZERO changes
- All fact models (fact_bookings, fact_payments, fact_calls) — ZERO changes
- All other dimension models (dim_date, dim_region, dim_patient, dim_payment_method) — ZERO changes
- Compliance layer (phi_restricted, reporting_open) — ZERO changes
- Monitoring dashboard — ZERO changes (Singapore appears automatically)
- AI agent — ZERO changes (can query Singapore providers immediately)
- CI/CD workflows — ZERO changes
- All 25 existing dbt tests — STILL PASSING, zero modifications needed

## Total effort

- New files: 4 (connector script, requirements, Dockerfile, staging model)
- Modified files: 4 (docker-compose, cli, loader, dim_provider, sources.yml)
- Lines added to existing files: ~25
- Lines of new code: ~80
- Time: ~15 minutes
- Core platform changes: ZERO

## Verification

```sql
SELECT practice_state, COUNT(*) FROM dim_provider 
GROUP BY practice_state ORDER BY COUNT(*) DESC;
-- Shows Singapore: 50 providers alongside US states
```

```bash
dbt test
-- PASS=25 WARN=0 ERROR=0
```

## To onboard marketplace #12

Repeat this exact process:
1. Create `connectors/<market>_providers/` with extract.py, requirements.txt, Dockerfile
2. Add service to docker-compose.yml
3. Add extract job to engine/cli.py DAG + depends_on
4. Add raw table + load section to engine/loader.py
5. Add staging model + source entry in dbt
6. Add UNION ALL to dim_provider.sql
7. Run pipeline — verify data flows end to end, all tests pass
