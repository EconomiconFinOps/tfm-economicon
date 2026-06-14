from app.graphs.pipeline import PipelineRunner
from app.repositories.jobs import JobRepository


class IngestTask:
    def __init__(self, repository: JobRepository, pipeline: PipelineRunner):
        self.repository = repository
        self.pipeline = pipeline

    def execute(self, job: dict) -> dict:
        job_id = job["id"]
        self.repository.mark_running(job_id)
        try:
            result = self.pipeline.run(job)
            self.repository.mark_completed(job_id, result)
            return result
        except Exception as exc:
            self.repository.mark_failed(job_id, str(exc))
            raise

