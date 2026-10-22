JUP: JUP-138 · Trello: https://trello.com/c/WvzuP74W/130-jup-138

# Review — poner docs/architecture.md al día

Cambio solo documental: se omiten tester, coder y mutación (no hay código de producto). Excepción
registrada según el flujo del repositorio.

## 1. Inventario en la SHA del corte (tareas 1.1 a 1.4)

Corte: **`03e97ce6`** (develop, 22/10/2026, `feat(JUP-089)`). `origin/develop` no se había movido al empezar
el apply.

### 1.1 Compose (D2)

Comandos, con un archivo de entorno de valores ficticios guardado fuera del repositorio (la salida de
`docker compose config` con valores reales contiene secretos y no se copia aquí):

```
docker compose --env-file <ficticio> config --services | --volumes
docker compose --env-file <ficticio> --profile demo config --services | --volumes
docker compose --env-file <ficticio> -f docker-compose.yml -f infra/litellm/compose.ai.yml --profile ai config --services | --volumes
docker compose --env-file <ficticio> config --format json   # redes, secretos, depends_on y puertos
```

| Combinación | Larga ejecución | Un solo uso | Volúmenes |
| --- | --- | --- | --- |
| Por defecto | 10: azure-cost-api, backend, cockroachdb, frontend, grafana, minio, postgres-pgvector, processor, prometheus, rabbitmq | 2: backend-migrate, minio-init | 6: cockroach-data, document-artifacts, grafana-data, pgvector-data, prometheus-data, rabbitmq-data |
| `--profile demo` | +1: azure-cost-api-demo | +1: demo-data | 6 (los mismos) |
| `--profile ai` (con el overlay `compose.ai.yml`) | +2: litellm, litellm-db | 2 | 7 (+ gateway-data) |

- El overlay `compose.ai.yml` no añade servicios: hace que backend y processor esperen a `litellm` sano y monta
  el secreto `summary-api-key` en el processor.
- Redes: `default` y `chat-private` (interna). Secretos: `chat-hmac` (más `summary-api-key` con el overlay).
- Dependencias de arranque: backend espera a `backend-migrate`, `minio-init`, cockroachdb, pgvector y rabbitmq;
  processor espera además a `azure-cost-api` y a `backend`; frontend a backend; prometheus a backend y
  processor; grafana a prometheus; `minio-init` a `minio`; `backend-migrate` a cockroachdb.
- Puertos de las apps (backend, processor, frontend, azure-cost-api): sin dirección loopback por defecto.
  Con loopback: minio, cockroachdb, rabbitmq, pgvector, prometheus, grafana y litellm.
- Corrección sobre mi recuento inicial a mano (propuesta y tarjeta): son **10** servicios de larga ejecución en
  el perfil por defecto, no 11. Los recuentos de este review son los que valen.

### 1.2 Rutas, migraciones y tablas

- **Backend** (`app/main.py`): metrics, health, auth, tenants, billing (`/billing`), jobs (`/jobs`), documents
  (`/jobs`), assistant (`/assistant`) y chat (también bajo `/assistant`).
  - `jobs`: `POST /jobs/ingest`.
  - `documents`: `POST /jobs/uploads`, `POST /jobs/uploads/{id}/confirm`, `GET` y `DELETE /jobs/uploads/{id}`
    y `GET /jobs/documents/{job_id}`.
  - `assistant`: conversaciones, `POST /assistant/conversations/{id}/messages` (ruta determinista y
    documental).
  - `chat`: `GET /assistant/capabilities`, `GET /assistant/requests`, generaciones
    (`POST …/generations`, estado, `/events`, `/stop`, `/resume`, recursos) y `…/summary` (+ `/retry`).
- **Processor**: API pública solo `GET /health`; superficie privada de chat y resumen en el puerto 8003 de la
  red `chat-private`, con firma HMAC (`chat-v2`) y activa solo con `CHAT_ENABLED=true`.
- **Migraciones y tablas** (`CREATE TABLE`):
  - backend, 7 migraciones (`001` a `006`, con dos `002`): `users`, `tenants`, `user_tenants`, `jobs`,
    `conversations`, `messages`, `anomaly_episodes`, `anomaly_detection_state`, `chat_operations`,
    `document_uploads`, `document_upload_slots`, `document_content_claims`, `document_execution_claims`,
    `extracted_documents`, `extracted_document_parts` (**15 tablas**; el documento dice ocho).
  - processor (CockroachDB), 4 migraciones: `azure_cost_ingestion_runs`, `azure_cost_records` (2 tablas,
    coincide con el documento).
  - pgvector (índice, lo migra el processor): `knowledge_documents`, `document_chunks`, `chunk_embeddings`,
    `embedding_spaces`, `embedding_cache`, `rag_chunk_vectors`, `rag_document_revisions`,
    `rag_generations`, `rag_generation_members`, `rag_revision_chunks`, `tenant_rag_head`.

### 1.3 Flags y valores por defecto

- `CHAT_ENABLED` (por defecto `false`) en backend y processor; sin él `/assistant/capabilities` devuelve
  `chat_enabled=false`, las generaciones responden 503 y el frontend no muestra el panel de chat.
- `RAG_VERIFIED_ENABLED`, `RAG_CONTEXTUAL_ENABLED`, `RAG_HYBRID_ENABLED` (por defecto `false`); contextual e
  híbrido exigen verificado.
- Modos de JUP-131 en el backend (`core/config.py`): `AUTH_PROVIDER` `local` (por defecto) o `cognito`;
  `EMBEDDING_PROVIDER` `mock` (por defecto), `litellm` o `bedrock` (Titan V2, dimensiones 256, 512 o 1024,
  región `eu-west-1`). Compose no activa ninguno de los modos AWS. ADR-0027 sigue en estado Proposed y la
  documentación de JUP-131 declara que no hay despliegue.
- `DOCUMENT_UPLOADS_ENABLED=true` fijado en Compose para backend y processor.
- `SUMMARY_ENABLED` por defecto `true`.
- El chat generativo recibe el resumen de costes verificado por el servidor como evidencia y tiene una única
  herramienta, la búsqueda documental del servidor (`server-documentation-v4`). Las consultas de
  ownership, anomalías y gasto **no** se exponen al modelo como herramientas.

## 2. Tabla de desfases

Sección, afirmación del documento, fuente y cambio previsto. El estado «aplicado» se completa en los grupos 2 y 3.

| # | Sección | Afirmación actual | Fuente | Cambio | Estado |
| --- | --- | --- | --- | --- | --- |
| 1 | Cabecera | Corte `a0e9a56`, 11/10 | `git` | Nuevo corte `03e97ce6`, 22/10 | aplicado |
| 2 | §1 | El processor «no compone todavía el vertical conversacional» | 1.2, 1.3 | Distinguir chat determinista, chat generativo integrado bajo `CHAT_ENABLED` y objetivo | aplicado |
| 3 | §2 | Sin MinIO, landing ni red privada del chat | 1.1 | Añadirlos a diagrama y tabla | aplicado |
| 4 | §2 | Backend: sin subidas, chat generativo ni `cost_query` | 1.2 | Ampliar responsabilidades | aplicado |
| 5 | §2 | Processor: sin extracción aislada ni superficie privada de chat | 1.2 | Ampliar | aplicado |
| 6 | §3.1 | `cost_query` (JUP-036) no aparece junto a `ownership_query` y `anomaly_query` | `schemas/assistant.py`, `assistant.py` | Añadir rama a la secuencia | aplicado |
| 7 | §3.1 | «el chat con modelo generativo es JUP-035» | 1.2 | Describir `/assistant/…/generations` y resumen | aplicado |
| 8 | §3.1 | Recuperación solo con `top_k` y umbral | `config.py`, `assistant.py` | Plan de recuperación con flags RAG | aplicado |
| 9 | §3.2 | `text_content` obligatorio; `artifact_uri` sin descarga ni extracción de archivos | 1.2, ADR-0022 | Subida por URL firmada a MinIO y extracción aislada | aplicado |
| 10 | §3.2 | Sin chunking estructural | ADR-0023 | Añadirlo con enlace | aplicado |
| 11 | §3.4 | Todo el vertical es objetivo | 1.3 | Integrado: contexto verificado y búsqueda documental. Objetivo: tools de ownership, anomalías y gasto | aplicado |
| 12 | §4 | «backend migra sus ocho tablas» | 1.2 | 15 tablas; añadir almacén de objetos | aplicado |
| 13 | §5 | Sin Cognito | JUP-131 | Una frase sobre el modo Cognito para AWS | aplicado |
| 14 | §6.1 | «9 servicios base y 5 volúmenes»; ai «11 y 6» | 1.1 | 10 + 2 y 6; con ai 12 + 2 y 7; demo +1 y +1 | aplicado |
| 15 | §6.1 | Figura sin MinIO, redes ni perfil demo | 1.1 | Rehacerla | aplicado |
| 16 | §6.1 | Tabla de versiones sin MinIO | `infra/minio/Dockerfile` | Añadir fila | aplicado |
| 17 | §6.1 | Orden de arranque sin MinIO ni `backend-migrate` | 1.1 | Corregir | aplicado |
| 18 | §6.3 | «no se desplegará» (AWS) | JUP-131, ADR-0027 | Código para modos AWS y pipeline, sin despliegue a la fecha | aplicado |
| 19 | §7 | Sin ADR-0022 a 0027 | `docs/adr/` | Citar por archivo | aplicado |
| 20 | §8 | «nueve servicios» en el CD | `dockerserver-cd.md`, 1.1 | Referirse al Compose general | aplicado |

## 4. Desfases nuevos descubiertos al editar

| # | Sección | Hallazgo | Cambio |
| --- | --- | --- | --- |
| 21 | §8 | La frase de CI no incluía los jobs de JUP-131 (contrato PostgreSQL y demo AWS offline) ni la política JUP y la landing | Reescrita con los jobs de `ci.yml` |
| 22 | §6.1 | `chat-private` es interna y el puerto 8003 no se publica; la frase «la red base no restringe egress» podía leerse como aplicable a ella | Aclarado |
| 23 | §3.1 | El router de chat cuelga de `/assistant`, no de `/chat` (corrige mi nota inicial) | El documento usa las rutas reales |
| 24 | §6.2 | La fila de JUP-050 dice «nueve servicios»: es evidencia histórica fechada del 01/10 | Se conserva sin cambios |

## 3. Hallazgos fuera de alcance

- `docs/deployment/dockerserver-cd.md` **no** contradice el Compose actual: habla del «Compose general» y ya
  cubre MinIO y `chat-private`. Sin cambios.
- Por confirmar durante el apply: `docs/assistant-corpus/product-architecture/economicon-product-context.md`
  puede arrastrar el mismo desfase (corpus del asistente); se anota, no se edita.
- Propuesta futura: una comprobación automática de los servicios de Compose frente a `architecture.md`.
