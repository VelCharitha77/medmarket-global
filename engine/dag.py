from engine.job import JobStatus

class DAG:
    """
    A Directed Acyclic Graph of jobs.
    
    Holds jobs and their dependencies. The scheduler uses this to determine:
    - Which jobs are ready to run (all dependencies satisfied)
    - Which jobs are blocked (waiting on an unfinished dependency)
    - Which jobs should be skipped (a dependency failed, so downstream is unreachable)
    """

    def __init__(self, name):
        self.name = name
        self.jobs = {}          # name -> Job instance
        self.dependencies = {}  # name -> set of dependency job names

    def add_job(self, job, depends_on=None):
        """
        Add a job to the DAG, optionally specifying which other jobs
        it depends on (by name).
        """
        if job.name in self.jobs:
            raise ValueError(f"Job '{job.name}' already exists in DAG '{self.name}'")

        self.jobs[job.name] = job
        self.dependencies[job.name] = set()

        if depends_on:
            for dep_name in depends_on:
                if dep_name not in self.jobs:
                    raise ValueError(
                        f"Dependency '{dep_name}' not found in DAG. "
                        f"Add it before adding '{job.name}'."
                    )
                self.dependencies[job.name].add(dep_name)

    def get_runnable_jobs(self):
        """
        Return a list of jobs that are ready to run right now:
        - Status is PENDING (hasn't started yet)
        - All dependencies have status SUCCESS
        """
        runnable = []
        for name, job in self.jobs.items():
            if job.status != JobStatus.PENDING:
                continue

            deps = self.dependencies[name]
            if not deps:
                # No dependencies — always runnable if pending
                runnable.append(job)
            elif all(self.jobs[d].status == JobStatus.SUCCESS for d in deps):
                # All dependencies succeeded — ready to go
                runnable.append(job)

        return runnable

    def get_blocked_jobs(self):
        """
        Return jobs that should be SKIPPED because a dependency failed.
        If extract_nextgen fails, everything downstream of it can't run.
        """
        blocked = []
        for name, job in self.jobs.items():
            if job.status != JobStatus.PENDING:
                continue

            deps = self.dependencies[name]
            if any(self.jobs[d].status == JobStatus.FAILED for d in deps):
                blocked.append(job)

        return blocked

    def is_complete(self):
        """
        Return True if every job has reached a terminal state
        (SUCCESS, FAILED, or SKIPPED) — meaning there's nothing left to do.
        """
        terminal = {JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.SKIPPED}
        return all(job.status in terminal for job in self.jobs.values())

    def summary(self):
        """Return a human-readable summary of all jobs and their statuses."""
        lines = [f"DAG: {self.name}"]
        for name, job in self.jobs.items():
            deps = self.dependencies[name]
            dep_str = f" (depends on: {', '.join(deps)})" if deps else ""
            lines.append(f"  {name}: {job.status}{dep_str}")
        return "\n".join(lines)
