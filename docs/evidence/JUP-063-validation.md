# JUP-063 — Evidencia de redacción de IA

Fecha: 10/10/2026. [Tarjeta](https://trello.com/c/sRKGpYEy).
[PR #95](https://github.com/EconomiconFinOps/tfm-economicon/pull/95), borrador contra develop.
Base de las afirmaciones: `c2995a118d419dfe725247bac9c6f219a3f0ea77`.
Esta es evidencia de una contribución preparada para Paris, no el dictamen
independiente `Validacion JUP-063`, ni la memoria, ni aceptación del MVP.

## Entrega y autoridad

La propuesta e/g vive fuera del repositorio en el workspace de coordinación:
`materiales/06-entregables/JUP-063-2026-10-10/propuesta-ia-e-g.md`.
Incluye 14 párrafos identificados, referencias al commit y cobertura del guion.
No se ha escrito en Google Docs. No se guardan cuerpo de memoria ni exports en Git.

Trello vivo, leído por `TrelloClient` desplegado en
`DockerServer:/home/danteadmin/economicon-collaboration`, conserva el alcance del
snapshot de despacho: P0, sin fecha ni dependencias refinadas. Roles: Paris
liderazgo, Victor pairing, Alejandro revisión y Lucia validación. No se ha
acreditado participación de esos roles durante este encargo ni se han reasignado.
La contribución propia no podrá revisarse o validarse independientemente con la
misma identidad que la publica; se entrega al responsable para resolverlo según
CONTRIBUTING, sin atribuciones ficticias.

## Evidencia por criterio de tarjeta

| Criterio original | Evidencia propia | Estado y límite |
| --- | --- | --- |
| Resultado funcional verificable | Propuesta e/g, revisión contra código y matriz del guion | Preparado; incorporación canónica y aceptación del contenido pendientes |
| Pruebas necesarias añadidas y en verde | Controles documentales y gateway correctos; suites focalizadas: 353 PASS, 11 FAIL, 6 SKIP | No satisfecho globalmente: fallos de timing/subprocesos pendientes de reproducción; no se añaden tests que repliquen prosa |
| Documentación y decisiones actualizadas | Contrato OpenSpec, esta evidencia y continuidad | Preparado; conserva gobernanza y decisiones existentes |
| Pull request revisado y vinculado | PR #95 de soporte, en borrador contra develop | Publicada y enlazada; revisión humana pendiente, criterio no completado |
| Validación funcional y evidencia enlazadas | Referencias verificables y logs externos | Evidencia técnica local; validación independiente y export revisado pendientes |

## Mapa de afirmaciones verificadas

Rutas relativas a la raíz. El fragmento indicado permite revisar cada afirmación;
la propuesta externa incluye enlaces permanentes al commit completo.

| Párrafos | Evidencia | Alcance comprobado |
| --- | --- | --- |
| E1, E5 | `apps/backend/app/api/routes/assistant.py:115`; `apps/backend/app/services/assistant.py:1` | Embedding/retrieval, respuesta de plantilla y citas; sin LLM del chat |
| E2 | `apps/processor/app/tasks/ingest.py:53`; `app/graphs/pipeline.py:29` dentro del processor | Trabajo persistido autorizado, secuencia fija de nodos |
| E2–E3 | `apps/processor/app/embeddings/chunker.py:13`; `providers.py:8` en el mismo directorio; `app/core/config.py:24` | Corte por caracteres 500/50, mock SHA-256 y 1536 dimensiones reales configuradas |
| E3 | `apps/processor/app/vector_store/pgvector_store.py:47`; `migrations/001_initial.py:6` en el mismo directorio | Transacción, dimensión/proveedor; no identidad semántica del modelo por vector |
| E4 | `apps/backend/app/services/vector_store.py:28`; `apps/backend/app/core/config.py:15` | Coseno exacto, filtro tenant/proveedor, umbral antes del límite, top_k 4 y 0,6 |
| E4 | [Calibración JUP-022](../spikes/JUP-022-retrieval-calibration.md) | Histórico 03/10, cálculo en memoria, 28 preguntas/52 fragmentos; no ejecución nueva |
| E5 | `apps/backend/app/services/citations.py:21` | Origen del fragmento, validación de tenant y localización Markdown, sin garantía de verdad |
| E6 | `apps/processor/app/agents/service.py:28`; `providers.py:45`; `prompts.py:1` en ese directorio | Metadata saneada, sin chunks; roles concatenados a un mensaje user |
| E7 | `apps/processor/app/agents/guardrails.py:88`; `schemas.py:98` en ese directorio | Límites del saneamiento y contrato FinOpsResponse v1.0; coherencia interna |
| E8, G5 | [Procedimiento JUP-070](../validation/JUP-070-evaluation.md) y [run 2](JUP-070-run-2-report.json) | Chat medido con plantilla, incluso con embeddings reales; resultados en h/JUP-109 |
| E9 | [Corpus](../assistant-corpus/README.md) | Seguimiento de integración de manifest y ámbitos, sin declarar implementado el contrato completo |
| G1–G4 | [ADR-0002](../adr/ADR-0002-litellm-openrouter.md); [configuración](../../infra/litellm/config.example.yaml) | Uso preentrenado y selección declarada; evidencia histórica, no catálogo/precio vigente |
| G3 | [Imagen gateway](../../infra/litellm/docker-compose.yml); `apps/processor/app/clients/litellm.py:94` | Digest/versión declarados, política configurada y límite DNS |

## Guion, documento y fronteras

El enlace de `Guion_PJ.md` se obtuvo de la tarjeta de enlaces y se leyó directamente;
metadata: modificado el 09/10/2026. No se enumeró la carpeta ni se leyó el cuerpo
de la memoria. Sólo metadata de Google Docs confirmó una pestaña `t.0`.
Se pidió el fragmento e/g y su estilo porque leer esa pestaña devolvería todas las
secciones. No se exportó ni se alteró contenido de otros responsables.

La propuesta contrasta lista de apartados, requisitos técnicos/funcionales y
desglose de evaluación. Señala en cada fila cobertura, pendiente o dependencia
de otra sección, incluida paginación global. La fidelidad de la transcripción
del guion al PDF original queda sin verificar.

## Comprobaciones de esta entrega

Los logs originales están fuera de Git en
`materiales/07-evidencias/JUP-063-2026-10-10/` del workspace de coordinación.
No se lanzaron Docker, consultas SQL reales, OpenRouter ni llamadas pagadas.

### Controles documentales y de configuración

- `check-delivery.py` (helper fuera de Git): 28 archivos fuente contrastados
  byte a byte, normalizando CRLF/LF, contra la base; 14 párrafos, 14 referencias
  y 19 enlaces locales resueltos. Manifiesto externo `delivery-manifest.json`.
- SHA-256 de la propuesta: `dfa97ccef7bdba8ed0183e229f554ac35683b06991504d99d0b97c772a0d1497`.
- OpenSpec 1.8.0, `openspec validate --all --strict --no-interactive`: **56 PASS**.
  Se reutilizó el ejecutable ya instalado sin modificar dependencias compartidas.
- `node tools/jup-check.mjs --all`: **9 changes correctos**. No significa que
  sus tareas estén terminadas, sólo que cumplen la estructura y trazabilidad.
- `node tools/jup-cleanup-check.mjs`: **980 archivos correctos** en el control
  final; el tema de continuidad ignorado localmente se añadió explícitamente.
- `git diff --check` y `git diff --cached --check`: sin errores de espacios.
- `node --test --test-isolation=none tools/llm-gateway-config.test.mjs`:
  **7 PASS**, 0 fallos/skips. Se copió yaml ya disponible a los `node_modules`
  de esta copia aislada; no se alteró el checkout compartido.
- Segunda auditoría automatizada de exactitud: no encontró errores materiales
  en E1–E9/G1–G5; no ejecutó pruebas ni constituye dictamen humano.

### Pruebas del processor: ejecución con fallos, no aceptación

Desde `apps/processor`, con `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` y
`PYTHONDONTWRITEBYTECODE=1`:

```text
python -B -m pytest -p no:cacheprovider --basetemp=<temporal-exclusivo-jup063> tests/test_embedding_pipeline.py tests/test_agent_runtime.py tests/test_ai_settings.py tests/test_ingest_task.py -q
```

**79 PASS, 10 FAIL, 6 SKIP**, 21 avisos, 287,68 s. Log `processor-tests-2.txt`.
Los seis casos CockroachDB se omiten por falta de opt-in a infraestructura.
Fallos observados, sin atribuir una causa no probada:

- Cinco tests `test_jup023_attempt_deadline_*`: los plazos de 50 ms expiran;
  los casos de trickle ven menos intentos en el servidor local de los esperados
  y el caso de respuesta completa termina en timeout.
- Cinco casos SQLite de `test_ingest_task`: `_backend_message` agota los 30 s
  del subproceso auxiliar, antes de verificar el comportamiento de ingesta.

El log no establece si son regresión de producto, efecto de carga o del entorno;
queda pendiente reproducir esos diez casos en el entorno soportado. No se han
cambiado código, límites o tests para obtener un resultado favorable.

Entorno local identificado: Python **3.14.4**, pytest **9.0.3**, Pydantic **2.12.5**,
pydantic-settings **2.13.1**, FastAPI **0.115.12**, SQLAlchemy **2.0.52**,
langchain-core **1.6.0**, LangGraph **1.2.11**; Node **24.14.1**, pnpm **9.0.0**.
El proyecto usa Python 3.12 como referencia de CI. LangChain avisó de
incompatibilidad del soporte Pydantic V1 con Python 3.14; el aviso no demuestra
ser la causa de los diez fallos. No se certifica equivalencia con CI.

### Pruebas del backend

Desde `apps/backend`, mismas variables y temporal exclusivo diferente:

```text
python -B -m pytest -p no:cacheprovider --basetemp=<temporal-backend-jup063> tests/test_assistant_service.py tests/test_citations.py tests/test_retrieval_contract.py tests/test_retrieval_failures.py tests/test_retrieval_traceability.py tests/test_embedding_parity.py tests/test_embedding_settings.py tests/test_litellm_embedding_provider.py -q
```

**274 PASS, 1 FAIL**, 0 skips, 5 avisos, 344,53 s. Log `backend-tests-2.txt`.
Falla `test_slow_headers_are_cut_by_the_overall_deadline_of_each_attempt[0.1-2-1.6]`:
la categoría y el límite temporal cumplen, pero el servidor local cuenta una
petición atendida frente a tres esperadas. No se demuestra con ello ni pérdida
de reintentos ni causa raíz; el contador se observa desde otro hilo.

Las pruebas usan transportes/almacenes dobles y servidores HTTP de loopback;
el contrato SQL se verifica con un motor registrador, no ejecutando pgvector.
Resumen Python de esta contribución: **353 PASS / 11 FAIL / 6 SKIP**. Los once
fallos requieren reproducción en un entorno controlado compatible con CI antes
de afirmar verde global. El entorno temporal Python 3.12 citado por evidencias
históricas ya no estaba disponible en la ruta consultada; no se reconstruyó ni
se instaló otro entorno para este cambio documental.

### Incidencias del entorno

El primer intento del processor produjo **95 errores de setup**, todos por
acceso denegado al temporal general de pytest; no ejercitó los casos.
El primer intento de backend se detuvo tras confirmar el mismo impedimento.
Se conservaron logs y se repitió con temporales exclusivos y permisos locales.
El runner Node inicialmente no pudo crear procesos (`EPERM`); la ejecución en
el mismo proceso detectó después la dependencia yaml ausente. El control de
configuración pasó tras resolver sólo esa preparación. El checker de higiene
necesitó permiso local para su lectura de `git ls-files`.

## Pendientes para aceptación

- Revisión humana de la propuesta, fragmentos actuales e/g y guía de estilo.
- Incorporación autorizada, ajuste al máximo global de páginas y export fechado
  con SHA-256; dictámenes del contenido sobre esa versión.
- Participación efectiva y revisión/validación de la PR según CONTRIBUTING.
- El comportamiento generativo integrado, calidad del modelo, aislamiento SQL
  en vivo, coste/latencia actuales y despliegue quedan fuera de esta verificación.
- No cerrar tarjeta ni archivar el change por disponer de una propuesta.
