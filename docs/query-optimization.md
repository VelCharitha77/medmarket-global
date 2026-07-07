# Query Performance Optimization — Before/After Results

## Environment
- Database: PostgreSQL 16 (Docker container)
- Data volume: 28,921 encounters, 1,000 calls, 294 providers, 36,890 date rows
- All fact tables materialized as physical tables (not views)

## Baseline Measurements (no indexes, no materialized views)

| Query | Description | Execution Time |
|---|---|---|
| Q1 | Revenue by region, by month | 43.625 ms |
| Q2 | Provider utilization / no-show rate | 7.567 ms |
| Q3 | Call center performance by region | 0.753 ms |
| Q4 | Credentialing: expiring licenses | 0.089 ms |
| Q5 | Bookings by day of week | 23.196 ms |

## Optimization 1: Composite Indexes

Added indexes on all fact table foreign keys (date_key, region_key, provider_key)
and dimension lookup columns (license_status).

| Query | Before | After Indexes | Improvement |
|---|---|---|---|
| Q1 | 43.625 ms | 22.721 ms | 1.9x faster |
| Q5 | 23.196 ms | 19.516 ms | 1.2x faster |

Note: Q2-Q4 showed minimal change because the tables are small enough
that Postgres correctly prefers sequential scans over index lookups.

## Optimization 2: Materialized Views

Created pre-computed materialized views for the two most expensive queries.

| Query | Before | After Indexes | After Mat. View | Total Speedup |
|---|---|---|---|---|
| Q1 | 43.625 ms | 22.721 ms | 0.076 ms | **574x faster** |
| Q5 | 23.196 ms | 19.516 ms | 0.013 ms | **1784x faster** |

## Why materialized views had a bigger impact than indexes

At our data volume (~29K rows), Postgres often decides a sequential scan is cheaper
than index lookups because the entire table fits in memory. Indexes become more
impactful at larger scales (millions of rows) where the optimizer can skip large
portions of the table.

Materialized views, by contrast, eliminate the join and aggregation work entirely —
the result is pre-computed and stored as a small table (856 rows for Q1, 7 rows for Q5).
Querying them is effectively a sequential scan of a tiny table, which is nearly instant.

## Refresh strategy

Materialized views are refreshed after every pipeline run via `engine/refresh_views.py`,
triggered as a job in the nightly DAG between `dbt_marts` and `dbt_test`.

## Indexes created

- fact_payments: date_key, region_key, provider_key
- fact_bookings: date_key, region_key, provider_key
- fact_calls: date_key, region_key
- dim_date: date_key
- dim_provider: provider_key, license_status
- dim_region: region_key
