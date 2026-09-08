## 1. Backend: propagar request_id al job publicado

- [x] 1.1 En `apps/backend/app/api/routes/jobs.py`, leer `structlog.contextvars.get_contextvars().get("request_id")` y añadirlo a `job["request_id"]` antes de `queue.publish(job)`.

## 2. Processor: correlacionar logs del pipeline de ingesta

- [x] 2.1 En `apps/processor/app/workers/runner.py` (`ProcessorWorker._process_message`), extraer `message.payload.get("request_id")`, generando `uuid4()` como fallback si falta.
- [x] 2.2 Envolver el procesamiento del job con `structlog.contextvars.clear_contextvars()` seguido de `bind_contextvars(request_id=...)`, antes de `self.task.execute(job)`.

## 3. Pruebas

- [x] 3.1 Test de backend: `POST /jobs/ingest` exitoso publica un mensaje cuyo `request_id` coincide con el de la petición HTTP en curso. (`test_ingest_tracing.py`)
- [x] 3.2 Test de processor: procesar un mensaje con `request_id` deja ese mismo `request_id` en los logs emitidos durante el procesamiento del job. (`test_worker_tracing.py`)
- [x] 3.3 Test de processor: procesar un mensaje sin `request_id` genera uno propio y lo usa consistentemente en los logs del job. (`test_worker_tracing.py`)
- [x] 3.4 Test de processor: procesar dos mensajes consecutivos con `request_id` distintos no filtra el primero en los logs del segundo. (`test_worker_tracing.py`)

## 4. Documentación y cierre

- [ ] 4.1 Documentar la convención de trazabilidad extremo a extremo en `docs/manuals/python-service-conventions.md`.
- [ ] 4.2 Ejecutar la batería de checks del carril (`openspec:validate`, `jup:check`, tests de backend/processor) y registrar el resultado en `review.md`.
- [ ] 4.3 Verificar manualmente con `docker compose up`: publicar una ingesta real y confirmar en los logs (JSON) de backend y processor que comparten el mismo `request_id`.
