import subprocess
import os
from engine.job import Job

class ShellJob(Job):
    """
    Runs an arbitrary shell command as a pipeline step.
    Useful for: loading raw data, running custom scripts, refreshing caches.
    """

    def __init__(self, name, command, working_dir=None, max_retries=2):
        super().__init__(name, max_retries=max_retries)
        self.command = command
        self.working_dir = working_dir or os.environ.get(
            "PROJECT_DIR",
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )

    def run(self):
        self.logger.info(f"Running command: {self.command}")

        result = subprocess.run(
            self.command,
            shell=True,
            cwd=self.working_dir,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                self.logger.info(f"  [shell] {line}")

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            raise RuntimeError(f"Command failed (exit {result.returncode}): {error_msg}")

        return True
