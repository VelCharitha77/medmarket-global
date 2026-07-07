"""Basic tests for the orchestration engine core classes."""
from engine.job import Job, JobStatus
from engine.dag import DAG

class SuccessJob(Job):
    def run(self):
        return True

class FailJob(Job):
    def run(self):
        raise RuntimeError("I always fail")

def test_job_success():
    job = SuccessJob("test_success")
    assert job.status == JobStatus.PENDING
    result = job.execute()
    assert result == True
    assert job.status == JobStatus.SUCCESS
    assert job.start_time is not None
    assert job.end_time is not None
    print("PASS: test_job_success")

def test_job_failure_and_retry():
    job = FailJob("test_fail", max_retries=2, backoff_base=0)
    result = job.execute()
    assert result == False
    assert job.status == JobStatus.FAILED
    assert job.error is not None
    print("PASS: test_job_failure_and_retry")

def test_dag_dependency_order():
    dag = DAG("test_dag")
    dag.add_job(SuccessJob("a"))
    dag.add_job(SuccessJob("b"), depends_on=["a"])

    runnable = dag.get_runnable_jobs()
    assert len(runnable) == 1
    assert runnable[0].name == "a"
    print("PASS: test_dag_dependency_order")

def test_dag_parallel_jobs():
    dag = DAG("test_parallel")
    dag.add_job(SuccessJob("a"))
    dag.add_job(SuccessJob("b"))
    dag.add_job(SuccessJob("c"), depends_on=["a", "b"])

    runnable = dag.get_runnable_jobs()
    assert len(runnable) == 2
    names = {j.name for j in runnable}
    assert names == {"a", "b"}
    print("PASS: test_dag_parallel_jobs")

def test_dag_skip_on_failure():
    dag = DAG("test_skip")
    dag.add_job(FailJob("a", max_retries=1, backoff_base=0))
    dag.add_job(SuccessJob("b"), depends_on=["a"])

    dag.jobs["a"].execute()
    blocked = dag.get_blocked_jobs()
    assert len(blocked) == 1
    assert blocked[0].name == "b"
    print("PASS: test_dag_skip_on_failure")

if __name__ == "__main__":
    test_job_success()
    test_job_failure_and_retry()
    test_dag_dependency_order()
    test_dag_parallel_jobs()
    test_dag_skip_on_failure()
    print("\nAll tests passed!")
