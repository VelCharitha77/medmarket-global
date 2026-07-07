import logging
import psycopg2
from datetime import datetime
from engine.job import JobStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("engine.scheduler")

class Scheduler:
    """
    The main orchestration loop.
    
    Given a DAG, the scheduler:
    1. Finds jobs that are ready to run (all dependencies satisfied)
    2. Executes them (calling job.execute(), which handles retries internally)
    3. Marks blocked downstream jobs as SKIPPED if a dependency failed
    4. Repeats until every job has reached a terminal state
    5. Logs every job run to a database table for monitoring
    6. Sends alerts on failure/success via the alerting module
    """

    def __init__(self, dag, db_url=None):
        self.dag = dag
        self.db_url = db_url
        self.run_log = []

    def run(self):
        """Execute the full DAG, respecting dependencies."""
        logger.info(f"=== Starting DAG: {self.dag.name} ===")
        start_time = datetime.utcnow()

        while not self.dag.is_complete():
            # Mark any jobs blocked by failed dependencies as SKIPPED
            blocked = self.dag.get_blocked_jobs()
            for job in blocked:
                job.status = JobStatus.SKIPPED
                logger.warning(f"Skipping {job.name} — a dependency failed")
                self.run_log.append(job.to_dict())

            # Find and execute runnable jobs
            runnable = self.dag.get_runnable_jobs()
            if not runnable and not self.dag.is_complete():
                logger.error("Deadlock: no runnable jobs and DAG not complete")
                break

            for job in runnable:
                success = job.execute()
                self.run_log.append(job.to_dict())
                
                # Send alert on failure
                if not success:
                    try:
                        from engine.alerting import alert_on_failure
                        alert_on_failure(self.dag.name, job.name, job.error)
                    except Exception as e:
                        logger.warning(f"Could not send failure alert: {e}")

        # Log results
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        succeeded = sum(1 for j in self.dag.jobs.values() if j.status == JobStatus.SUCCESS)
        failed = sum(1 for j in self.dag.jobs.values() if j.status == JobStatus.FAILED)
        skipped = sum(1 for j in self.dag.jobs.values() if j.status == JobStatus.SKIPPED)
        total = len(self.dag.jobs)

        logger.info(f"=== DAG {self.dag.name} complete ({duration:.1f}s) ===")
        logger.info(f"Results: {succeeded}/{total} succeeded, {failed} failed, {skipped} skipped")
        logger.info(f"\n{self.dag.summary()}")

        # Send completion alert
        try:
            if failed == 0:
                from engine.alerting import alert_on_success
                alert_on_success(self.dag.name, total, duration)
            else:
                from engine.alerting import send_alert
                send_alert(
                    title=f"Pipeline Partial Failure: {self.dag.name}",
                    message=f"{succeeded}/{total} succeeded, {failed} failed, {skipped} skipped in {duration:.1f}s",
                    severity="warning"
                )
        except Exception as e:
            logger.warning(f"Could not send completion alert: {e}")

        # Save to database if connected
        if self.db_url:
            self._save_to_db()

        return failed == 0

    def _save_to_db(self):
        """Write all job run records to the job_runs table."""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS job_runs (
                    id SERIAL PRIMARY KEY,
                    dag_name TEXT NOT NULL,
                    job_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_seconds FLOAT,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            for record in self.run_log:
                cur.execute("""
                    INSERT INTO job_runs (dag_name, job_name, status, start_time, end_time, duration_seconds, error)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    self.dag.name,
                    record["job_name"],
                    record["status"],
                    record["start_time"],
                    record["end_time"],
                    record["duration_seconds"],
                    record["error"]
                ))

            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Saved {len(self.run_log)} job run records to database")
        except Exception as e:
            logger.error(f"Failed to save run log to database: {e}")
