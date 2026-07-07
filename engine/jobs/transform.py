import subprocess
import os
from engine.job import Job

class TransformJob(Job):
    """
    Runs a dbt command (e.g., 'dbt run', 'dbt test') as a pipeline step.
    """

    def __init__(self, name, dbt_command="run", dbt_project_dir=None, max_retries=2):
        super().__init__(name, max_retries=max_retries)
        self.dbt_command = dbt_command
        self.dbt_project_dir = dbt_project_dir or os.path.join(
            os.environ.get(
                "PROJECT_DIR",
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            ),
            "dbt"
        )

    def run(self):
        self.logger.info(f"Running: dbt {self.dbt_command}")

        cmd = ["dbt"] + self.dbt_command.split()

        result = subprocess.run(
            cmd,
            cwd=self.dbt_project_dir,
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                self.logger.info(f"  [dbt] {line}")

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else result.stdout[-500:] if result.stdout else "Unknown error"
            raise RuntimeError(f"dbt {self.dbt_command} failed: {error_msg}")

        self.logger.info(f"dbt {self.dbt_command} completed successfully")
        return True
