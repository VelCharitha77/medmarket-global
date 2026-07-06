# Connector Contract

Every connector in this folder is a standalone Docker container following this contract:

## Environment variables (input)
- `SOURCE_NAME` - identifies the source (e.g. "npi_registry")
- `OUTPUT_PATH` - local folder path (or S3 path in production) where raw output is written
- Source-specific variables as needed (API keys, base URLs, etc.)

## Behavior
- Runs once per invocation, extracts data from the source, writes raw output
  (JSON or CSV) to `OUTPUT_PATH`, then exits.
- Does NOT transform or clean data - that happens later, in dbt (Phase 6).
- Does NOT handle scheduling or retries itself - that's the orchestration
  engine's job (Phase 5). A connector just does one run and reports success/failure.

## Exit codes
- `0` - success
- non-zero - failure (the orchestration engine will retry based on this)

## Adding a new connector
1. Create a new folder under `connectors/<source_name>/`
2. Write `extract.py` following this contract
3. Write `requirements.txt` and `Dockerfile`
4. Add it to `docker-compose.yml` at the repo root
