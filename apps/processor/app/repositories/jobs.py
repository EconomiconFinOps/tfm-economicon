from app.core.metrics import ingest_jobs_failed_total
from app.db.database import Database


class JobRepository:
    def __init__(self, database: Database):
        self.database = database

    @property
    def json_stored_as_text(self) -> bool:
        """Indica si el JSON de `jobs.result` llega como TEXTO serializado o ya decodificado.

        SQLite (solo pruebas) guarda el objeto serializado como texto; CockroachDB/psycopg
        (JSONB) lo entrega ya decodificado. Es la capa de datos quien sabe cual de las dos
        representaciones recibe, asi que la decision vive aqui y no en `IngestTask`, que solo
        la consume. Es propiedad de solo lectura (sin setter) a proposito: un valor impuesto
        desde fuera sobre CockroachDB reabriria la doble decodificacion de cadenas JSONB.
        """
        return self.database.engine.dialect.name == "sqlite"

    def fetch_authorized_job(self, job_id: str, *, tenant_id: str, created_by: str) -> dict | None:
        return self.database.fetch_authorized_job(job_id, tenant_id=tenant_id, created_by=created_by)

    def mark_running(self, job_id: str, *, tenant_id: str, created_by: str) -> None:
        self.database.update_job_status(job_id, "running", tenant_id=tenant_id, created_by=created_by)

    def mark_completed(self, job_id: str, result: dict, *, tenant_id: str, created_by: str, document_owner: str | None = None) -> None:
        owner = {'document_owner': document_owner} if document_owner is not None else {}
        self.database.update_job_status(job_id, "completed", result=result, tenant_id=tenant_id, created_by=created_by, **owner)

    def mark_failed(self, job_id: str, error_message: str, *, tenant_id: str, created_by: str) -> None:
        self.database.update_job_status(job_id, "failed", result={"error": error_message}, tenant_id=tenant_id, created_by=created_by)
        ingest_jobs_failed_total.inc()
