import subprocess
import os
from engine.job import Job

class ExtractJob(Job):
    """
    Runs a connector container to extract data from a source.
    
    Uses 'docker compose run' to execute a specific service
    defined in docker-compose.yml, checks the exit code,
    and raises an exception if it failed.
    """

    def __init__(self, name, service_name, max_retries=3):
        super().__init__(name, max_retries=max_retries)
        self.service_name = service_name
        self.project_dir = os.environ.get(
            "PROJECT_DIR", 
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )

    def run(self):
        self.logger.info(f"Running connector: {self.service_name}")

        result = subprocess.run(
            ["docker", "compose", "run", "--rm", self.service_name],
            cwd=self.project_dir,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                self.logger.info(f"  [{self.service_name}] {line}")

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            self.logger.error(f"  [{self.service_name}] STDERR: {error_msg}")
            raise RuntimeError(f"Connector {self.service_name} exited with code {result.returncode}")

        self.logger.info(f"Connector {self.service_name} completed successfully")
        return True
