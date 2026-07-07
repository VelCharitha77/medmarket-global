"""Refreshes all materialized views after a pipeline run."""
import psycopg2
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("engine.refresh_views")

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:devpass123@localhost:5432/medmarket"
)

MATERIALIZED_VIEWS = [
    "mv_revenue_by_region_month",
    "mv_bookings_by_day_of_week",
]

def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    for view in MATERIALIZED_VIEWS:
        try:
            logger.info(f"Refreshing {view}...")
            cur.execute(f"REFRESH MATERIALIZED VIEW {view}")
            conn.commit()
            logger.info(f"  {view} refreshed successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"  Failed to refresh {view}: {e}")
            raise

    cur.close()
    conn.close()
    logger.info("All materialized views refreshed")

if __name__ == "__main__":
    main()
