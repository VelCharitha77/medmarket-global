import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime

class JobStatus:
    """Possible states a job can be in."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class Job(ABC):
    """
    Base class for all job types (extract, transform, agent, etc.).
    
    Every job has:
    - A name (unique identifier within a DAG)
    - A run() method (the actual work — subclasses implement this)
    - Retry logic (how many times to retry on failure, with backoff)
    - Logging (structured, consistent across all job types)
    - Status tracking (pending/running/success/failed/skipped)
    """

    def __init__(self, name, max_retries=3, backoff_base=2):
        self.name = name
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.status = JobStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.error = None
        self.logger = logging.getLogger(f"engine.job.{name}")

    @abstractmethod
    def run(self):
        """
        Subclasses implement this with the actual work.
        Should return True on success, raise an exception on failure.
        """
        raise NotImplementedError

    def execute(self):
        """
        Run the job with retry logic. This is what the scheduler calls —
        not run() directly.
        """
        self.start_time = datetime.utcnow()
        self.status = JobStatus.RUNNING
        self.logger.info(f"Starting job: {self.name}")

        for attempt in range(1, self.max_retries + 1):
            try:
                self.run()
                self.status = JobStatus.SUCCESS
                self.end_time = datetime.utcnow()
                duration = (self.end_time - self.start_time).total_seconds()
                self.logger.info(f"Job {self.name} succeeded (attempt {attempt}, {duration:.1f}s)")
                return True
            except Exception as e:
                self.error = str(e)
                self.logger.warning(f"Job {self.name} failed attempt {attempt}/{self.max_retries}: {e}")
                if attempt < self.max_retries:
                    wait = self.backoff_base ** (attempt - 1)
                    self.logger.info(f"Retrying in {wait}s...")
                    time.sleep(wait)

        self.status = JobStatus.FAILED
        self.end_time = datetime.utcnow()
        self.logger.error(f"Job {self.name} failed after {self.max_retries} attempts. Last error: {self.error}")
        return False

    def to_dict(self):
        """Return job run metadata as a dictionary (for logging to the database)."""
        return {
            "job_name": self.name,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else None,
            "error": self.error
        }
