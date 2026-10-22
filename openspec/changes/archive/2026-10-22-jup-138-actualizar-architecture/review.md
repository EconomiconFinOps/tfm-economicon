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
- Redes: `default`, `chat-private` (interna) y `gateway` (solo con el perfil `ai`: `litellm` y `litellm-db`;
  `litellm` está además en `default`). Secretos: `chat-hmac` (backend y processor) y, con el overlay `ai`,
  `summary-api-key` (solo el processor). Corregido tras la review de Paris: la lista inicial omitía `gateway`.
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
- El chat generativo recibe el resumen de costes verificado por el servidor como evidencia. El servidor
  prepara una única búsqueda documental por intento (`server-documentation-v4`) a partir de la pregunta
  (`retrieval_control`, hasta 2048 caracteres): el processor emite el `tool_call`, el backend la ejecuta y el
  resultado llega **antes** del primer borrador. El modelo no decide si se busca ni qué. Las consultas de
  ownership, anomalías y gasto **no** se exponen al modelo como herramientas. Corregido tras la review de
  Paris: la primera redacción atribuía la petición de búsqueda al modelo.

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

## 3. Desfases nuevos descubiertos al editar

| # | Sección | Hallazgo | Cambio |
| --- | --- | --- | --- |
| 21 | §8 | La frase de CI no incluía los jobs de JUP-131 (contrato PostgreSQL y demo AWS offline) ni la política JUP y la landing | Reescrita con los jobs de `ci.yml` |
| 22 | §6.1 | `chat-private` es interna y el puerto 8003 no se publica; la frase «la red base no restringe egress» podía leerse como aplicable a ella | Aclarado |
| 23 | §3.1 | El router de chat cuelga de `/assistant`, no de `/chat` (corrige mi nota inicial) | El documento usa las rutas reales |
| 24 | §6.2 | La fila de JUP-050 dice «nueve servicios»: es evidencia histórica fechada del 01/10 | Se conserva sin cambios |

## 4. Hallazgos fuera de alcance

- `docs/deployment/dockerserver-cd.md` **no** contradice el Compose actual: habla del «Compose general» y ya
  cubre MinIO y `chat-private`. Sin cambios.
- `docs/assistant-corpus/product-architecture/economicon-product-context.md` **no** está desfasado: por diseño
  no describe la arquitectura interna (sospecha inicial descartada).
- `apps/backend/README.md` y `apps/processor/README.md` no mencionan MinIO, las subidas de archivos ni
  `CHAT_ENABLED` (el README raíz sí cubre MinIO). Probable desfase; es de otra tarjeta y no se edita aquí.
- `docs/architecture-aws.md` mantiene su cabecera de alcance «exclusivamente documental» del 10/10 con la
  ampliación de JUP-131 como nota; no se ha revisado el resto (fuera de alcance, lo mantiene JUP-131).
- Propuesta futura: una comprobación automática de los servicios, redes y volúmenes de Compose frente a
  `docs/architecture.md`, porque nada lo valida hoy y ya se desfasó una vez.

## 5. Resultado y comprobaciones

Contraste con los escenarios del requisito añadido a `technical-architecture-deliverable`:

| Escenario | Evidencia |
| --- | --- |
| Un servicio de Compose aparece en la topología | Los 12 servicios por defecto, los 2 del perfil `demo` y los 2 de `ai` figuran en la figura de §6.1 o en la tabla de §2; las tres redes y los dos secretos, en la tabla de §6.1; los recuentos del texto coinciden con el inventario 1.1 |
| Capacidad integrada y desactivada por defecto | §1, §3.1 y §3.4 dan `CHAT_ENABLED=false` y los tres flags `RAG_*` en `false`, y rotulan como objetivo solo las tools de ownership, gasto y anomalías |
| Código cloud sin despliegue | §5 y §6.3 separan los modos `cognito`, `bedrock` y PostgreSQL del despliegue y remiten el estado al runbook y a la nota de continuidad |
| El corte declara la SHA | Cabecera: `develop 03e97ce6`, 22/10/2026, con el corte anterior |

Comprobaciones ejecutadas:

- Enlaces relativos de `docs/architecture.md`: 109 comprobados, 0 rotos (script local).
- Anclas entrantes (`docs/adr/README.md`): `#4-que-papel-tienen-rabbitmq-cockroachdb-y-pgvector` y
  `#7-por-que-esta-separado-asi`; los dos títulos no han cambiado.
- Diagramas Mermaid: los 10 se analizan y renderizan sin error con Mermaid 10.9.1 en Chrome headless. No se
  ha comparado la maquetación visual con la vista previa de GitHub.
- `develop` al cierre sigue en `03e97ce6`: el corte no se ha movido (tarea 4.4).
- `corepack pnpm openspec:validate`, `jup:check` y `jup:cleanup:check`: ver el cierre de la tarea 4.6.
- CI de GitHub: el job «AWS demo offline» (paso «Test CI/CD controller without AWS», error `Release evidence
  application tree differs`) falla **también en `develop`**: estaba en verde en `f224226d` (#153) y falla desde
  el merge de JUP-131 (`7f6c8d56`) y en `03e97ce6`, antes de abrir esta PR. Esta PR no toca `apps/`, `tools/`,
  `infra/` ni `.github/` (0 archivos), así que el resultado es el mismo por construcción. Reproducido en local
  (69 pruebas, 1 error, 1 omitida). El digest cubre todo `apps/`; no se ha identificado la causa y no se
  corrige aquí: la receta `infra/aws-cicd/release.json` es evidencia de JUP-131.

No verificado:

- No se ha levantado el stack: los recuentos y las dependencias salen de `docker compose config`, no de
  contenedores en marcha.
- Las 15 tablas del backend salen de las sentencias `CREATE TABLE` de las migraciones, no de ejecutarlas.
- No se ha ejecutado el chat generativo ni se ha comprobado su calidad; el documento lo declara integrado,
  desactivado por defecto y sin calidad acreditada.

## 6. ADR

No aplica: consolidación documental de decisiones ya registradas (ADR-0022 a ADR-0027, sin cambiar sus
estados). Se enlazan por archivo porque los números 0013, 0022 y 0023 están repetidos.

## Human Approval

- Change: jup-138-actualizar-architecture
- Approval type: post-review
- Decision: approved
- Approver: Victor
- Date: 2026-10-22
- Adversarial review: no ejecutada; cambio solo documental, sin código de producto, y sin ciclo tester, coder, mutación ni QA. La comprobación independiente fue contrastar cada afirmación con su fuente en la SHA `03e97ce6` (tabla de desfases, secciones 1 a 3)
- Accepted findings: README del backend y del processor sin MinIO, subidas ni `CHAT_ENABLED` (otra tarjeta); sin comprobación automática de `architecture.md` frente a Compose (propuesta futura); maquetación de los diagramas no comparada con la vista previa de GitHub
- Archive decision: archive
- Notes: aprobación registrada por Victor el 2026-10-22 a petición propia. No se levantó el stack ni se ejecutó el chat generativo: los recuentos salen de `docker compose config` y las tablas de las migraciones. Quedan fuera de esta aprobación y pendientes en Trello: las reviews `Revision JUP-138` y `Validacion JUP-138` y la CI en GitHub. El PR no está abierto.
