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
            # The queue carries Database.create_job's envelope; the graph takes
            # document fields and a job_id. Keep envelope identity authoritative.
            payload = job["payload"]
            pipeline_input = {
                "job_id": job_id,
                "tenant_id": job["tenant_id"],
                "source": job["source"],
                "artifact_uri": job.get("artifact_uri"),
                "text_content": payload["text_content"],
                "metadata": payload.get("metadata", {}),
            }
            result = self.pipeline.run(pipeline_input)
            self.repository.mark_completed(job_id, result)
            return result
        except Exception as exc:
            self.repository.mark_failed(job_id, "ingestion_failed")
            # Preserve the cause for the worker's final redacted exception rendering.
            raise RuntimeError("ingestion_failed") from exc
