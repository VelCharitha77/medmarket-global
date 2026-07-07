import argparse
import logging
import os
import sys

from engine.dag import DAG
from engine.scheduler import Scheduler
from engine.jobs.extract import ExtractJob
from engine.jobs.transform import TransformJob
from engine.jobs.shell import ShellJob

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:devpass123@localhost:5432/medmarket"
)

def build_nightly_dag():
    """
    Build the nightly pipeline DAG:
    
    extract_npi ──┐
    extract_ehr ──┤
    extract_crm ──┼──► load_raw ──► dbt_staging ──► dbt_marts ──► refresh_views ──► dbt_test
    extract_hr ───┤
    extract_calls─┤
    extract_fx ───┘
    """
    dag = DAG("nightly_global")

    # Layer 1: Extract (all run in parallel — no dependencies between them)
    dag.add_job(ExtractJob("extract_npi", service_name="npi-connector"))
    dag.add_job(ExtractJob("extract_ehr", service_name="ehr-connector"))
    dag.add_job(ExtractJob("extract_crm", service_name="hubspot-connector"))
    dag.add_job(ExtractJob("extract_hr", service_name="hr-connector"))
    dag.add_job(ExtractJob("extract_calls", service_name="call-center-connector"))
    dag.add_job(ExtractJob("extract_fx", service_name="region-fx-connector"))

    # Layer 2: Load raw data into Postgres (depends on ALL extracts finishing)
    dag.add_job(
        ShellJob("load_raw", command="python engine/loader.py"),
        depends_on=["extract_npi", "extract_ehr", "extract_crm", "extract_hr", "extract_calls", "extract_fx"]
    )

    # Layer 3: dbt staging models (depends on raw data being loaded)
    dag.add_job(
        TransformJob("dbt_staging", dbt_command="run --select staging"),
        depends_on=["load_raw"]
    )

    # Layer 4: dbt mart models (depends on staging)
    dag.add_job(
        TransformJob("dbt_marts", dbt_command="run --select marts"),
        depends_on=["dbt_staging"]
    )

    # Layer 4.5: Refresh materialized views (depends on marts)
    dag.add_job(
        ShellJob("refresh_views", command="python engine/refresh_views.py"),
        depends_on=["dbt_marts"]
    )

    # Layer 5: dbt tests (depends on marts AND view refresh)
    dag.add_job(
        TransformJob("dbt_test", dbt_command="test"),
        depends_on=["dbt_marts", "refresh_views"]
    )

    return dag


def cmd_run(args):
    """Run a named DAG."""
    logging.info(f"Building DAG: {args.dag_name}")

    if args.dag_name == "nightly_global":
        dag = build_nightly_dag()
    else:
        logging.error(f"Unknown DAG: {args.dag_name}")
        sys.exit(1)

    scheduler = Scheduler(dag, db_url=DB_URL if not args.no_db else None)
    success = scheduler.run()
    sys.exit(0 if success else 1)


def cmd_status(args):
    """Show the status of the most recent runs from the database."""
    import psycopg2

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT dag_name, job_name, status, start_time, duration_seconds, error
            FROM job_runs
            ORDER BY created_at DESC
            LIMIT %s
        """, (args.limit,))

        rows = cur.fetchall()
        if not rows:
            print("No job runs found.")
            return

        print(f"\n{'DAG':<20} {'Job':<25} {'Status':<10} {'Started':<22} {'Duration':<10} {'Error'}")
        print("-" * 110)
        for row in rows:
            dag, job, status, started, duration, error = row
            started_str = started.strftime("%Y-%m-%d %H:%M:%S") if started else "N/A"
            duration_str = f"{duration:.1f}s" if duration else "N/A"
            error_str = (error[:40] + "...") if error and len(error) > 40 else (error or "")
            print(f"{dag:<20} {job:<25} {status:<10} {started_str:<22} {duration_str:<10} {error_str}")

        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Could not connect to database: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="MedMarket Global — Pipeline Orchestration Engine")
    subparsers = parser.add_subparsers(dest="command")

    # 'run' command
    run_parser = subparsers.add_parser("run", help="Execute a named DAG")
    run_parser.add_argument("dag_name", help="Name of the DAG to run (e.g., nightly_global)")
    run_parser.add_argument("--no-db", action="store_true", help="Skip saving run log to database")

    # 'status' command
    status_parser = subparsers.add_parser("status", help="Show recent job run history")
    status_parser.add_argument("--limit", type=int, default=20, help="Number of records to show")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
