# Architecture Decision Records

This directory contains the project decision log for durable architecture choices. OpenSpec `design.md` captures the technical design of an individual Trello task; ADRs explain decisions that remain relevant across tasks, modules or project phases.

## Registro para memoria y tutor — JUP-061

Corte inicial: **01/10/2026**, develop `de0d62e`; conservado como historia en
la [auditoría](../evidence/JUP-061-validation.md). Registro vigente verificado
**03/10/2026**, con develop `6410950` incorporado: #51 y #54 integradas el
01/10 UTC; #59 y #53 el 02/10 UTC. Las filas reflejan esta integración y usan
fuentes locales. #65 integrada el 03/10 UTC aporta ADR-0016, Proposed,
incorporado al mismo inventario. Los merges no ratifican los ADR Proposed.

[Tarjeta JUP-061](https://trello.com/c/qXoHFxyy). Liderazgo: Alejandro Aguado;
pairing previsto: Victor Mendez; revisión: Paris Arcos Martin; validación: Lucia
Mateo. El intercambio sustituye las asignaciones del 01/10 y consta en la
[validación de Lucia](https://github.com/EconomiconFinOps/tfm-economicon/pull/60#pullrequestreview-5396865126).
No acredita pairing completado. Los responsables de cada decisión siguen en su
tarjeta de origen.

**Lectura:** el estado es el declarado por el ADR; merge y aprobación son evidencia
separada. Cada documento enlazado contiene contexto, alternativas y consecuencias.
Los resultados citados no se han reejecutado en JUP-061. Las cifras de precios y
benchmarks de ADR-0002 conservan su fecha; no son precios actuales.

| Decisión canónica | Fecha / estado registrado | Motivo y alternativa principal | Fuente responsable y evidencia de aceptación / integración |
| --- | --- | --- | --- |
| [0001 · API Azure simulada](ADR-0001-azure-cost-api-simulation.md) | 25/08 · Accepted | Probar HTTP/paginación sin tenant real; CSV directo no ejercita ese contrato. | JUP-073; [PR #5](https://github.com/EconomiconFinOps/tfm-economicon/pull/5) integrada y [evidencia](../evidence/JUP-073-validation.md). No acredita Azure real. |
| [0002 · LiteLLM/OpenRouter y modelos](ADR-0002-litellm-openrouter.md) | 25/08 · Proposed | Centralizar credenciales/políticas; acceso directo distribuye esa responsabilidad. Sin fallback para preservar evaluación. | JUP-078; [benchmark](../evidence/JUP-078-validation.md), [PR #10](https://github.com/EconomiconFinOps/tfm-economicon/pull/10) y [#21](https://github.com/EconomiconFinOps/tfm-economicon/pull/21) integradas. Aprobación de Alejandro fechada 28/08; las condiciones de aceptación conjunta y clave virtual siguen pendientes en el ADR. |
| [0003 · TypeScript strict](ADR-0003-frontend-typescript.md) | 02/09 · Accepted | Detectar errores de contratos desde el port; strict:false aplaza el coste. | JUP-092; gate de Victor enlazado en ADR, [PR #26](https://github.com/EconomiconFinOps/tfm-economicon/pull/26) integrada. |
| [0004 · Subconjunto shadcn/Radix](ADR-0004-frontend-shadcn-ui.md) | 07/09 · Accepted | Reutilizar primitivos accesibles; no copiar 26 paquetes sin consumidor. | JUP-094; addendum de Victor 07/09 enlazado en ADR; [PR #28](https://github.com/EconomiconFinOps/tfm-economicon/pull/28) integrada. |
| [0005 · Prometheus/Grafana](ADR-0005-prometheus-grafana-metrics.md) | 01/09 · Proposed | Métricas agregables y demo visual; logs solos no ofrecen esa vista. | JUP-043; [review operativo](../../openspec/changes/archive/2026-09-01-jup-043-technical-metrics/review.md), [PR #25](https://github.com/EconomiconFinOps/tfm-economicon/pull/25) integrada, APPROVED Victor 08/09. Ratificación explícita del estado ADR pendiente. |
| [0006 · Secretos de runtime](ADR-0006-runtime-secret-boundaries.md) | 09/09 · Accepted | Configuración externa y diagnóstico saneado; secret manager/TLS completo fuera de alcance. | JUP-053; aceptación de Paris 09/09 en ADR y [evidencia](../evidence/JUP-053-validation.md); [PR #33](https://github.com/EconomiconFinOps/tfm-economicon/pull/33) integrada. |
| [0007 · CORS explícito](ADR-0007-backend-cors-policy.md) | 23/09 · Accepted | Permitir orígenes concretos con middleware existente; proxy no seleccionado. | JUP-085; aceptación de Paris 23/09, [PR #43](https://github.com/EconomiconFinOps/tfm-economicon/pull/43) integrada y [evidencia](../evidence/JUP-085-validation.md). RF-085-002 no se confunde con CORS. |
| [0008 · Fronteras tenant](ADR-0008-tenant-isolation-boundaries.md) | 24/09 · Accepted | Autoridad persistida y membership; envelope/selector solos no autorizan. | JUP-086; aceptación de Paris 24/09 en ADR, [evidencia](../evidence/JUP-086-validation.md), [PR #47](https://github.com/EconomiconFinOps/tfm-economicon/pull/47) integrada. |
| [0009 · Ciclo del publisher RabbitMQ](ADR-0009-rabbitmq-publisher-lifecycle.md) | 25/09 · Accepted | Owner único, confirms y esperas acotadas; un timeout de Future no detiene un publish. | JUP-086; gates de Paris y addendum DNS en ADR; misma [PR #47](https://github.com/EconomiconFinOps/tfm-economicon/pull/47). Riesgo de interfaces internas Pika y ausencia de outbox explícitos. |
| [0010 · Solapamiento de costes](ADR-0010-azure-cost-source-overlap.md) | 27/09; aceptado 28/09 · Accepted | Rechazar sumas ambiguas; latest-wins/deduplicación no prueban identidad del cargo. | JUP-026; gate de Paris y [evidencia](../evidence/JUP-026-validation.md); [PR #52](https://github.com/EconomiconFinOps/tfm-economicon/pull/52) integrada el 30/09. |
| [0011 · Dueño único por tabla](ADR-0011-single-owner-per-table.md) | 30/09 · Accepted | Evitar DDL competidor; retry no elimina doble propiedad. | JUP-096; [PR #51](https://github.com/EconomiconFinOps/tfm-economicon/pull/51) integrada el 01/10 UTC; APPROVED Victor 01/10, revisión de Paris. |
| [0012 · Tokens de color](ADR-0012-frontend-color-tokens.md) | 29/09; aceptado 01/10 · Accepted | Fuente única por función; paleta reducida cambiaría el diseño. | JUP-099; [PR #54](https://github.com/EconomiconFinOps/tfm-economicon/pull/54) integrada el 01/10 UTC; validación APPROVED Alejandro 01/10. |
| [0013 · pgvector y ranking exacto](ADR-0013-pgvector-retrieval-baseline.md) | 01/10 · Proposed | Conservar writer/reader y filtro tenant; ANN/motor externo requieren evaluación propia. | JUP-061 consolida; JUP-021 aporta [PR #53](https://github.com/EconomiconFinOps/tfm-economicon/pull/53) integrada el 02/10 UTC, [evidencia](../evidence/JUP-021-validation.md) y validación APPROVED Victor 02/10 19:56 UTC (la del 01/10 quedó descartada). Ratificación del ADR pendiente. |
| [0014 · Auth propia para demo](ADR-0014-demo-auth-boundary.md) | 01/10 · Proposed | Formalizar sesión existente sin añadir IdP; no acreditar producción. | JUP-061 consolida; contrato JUP-085 integrado. Justificación retrospectiva pendiente de ratificar. |
| [0015 · Compose local](ADR-0015-local-compose-deployment-boundary.md) | 01/10 · Proposed | Repetir topología y builds; orquestador/hosting productivo no seleccionados. | JUP-061 consolida; JUP-049 integrado. JUP-050 [PR #59](https://github.com/EconomiconFinOps/tfm-economicon/pull/59) integrada el 02/10 UTC, [evidencia](../evidence/JUP-050-validation.md). Ratificación y despliegue final pendientes. |
| [0016 · Pin de LiteLLM 1.103.2](ADR-0016-litellm-version-pin.md) | 02/10 · Proposed | Fijar imagen/digest para validación aislada; baseline anterior afectada por avisos, latest no reproducible. | JUP-023; [PR #65](https://github.com/EconomiconFinOps/tfm-economicon/pull/65) integrada el 03/10 UTC y [evidencia](../evidence/JUP-023-validation.md); [diseño archivado](../../openspec/changes/archive/2026-10-04-jup-023-litellm-openrouter/design.md). Decisión operativa de Paris del 02/10 documentada en ADR; no acepta ADR-0002 ni autoriza uso real. |

### Decisiones ya explicadas fuera de un ADR

Estas fuentes se reutilizan; no se copian en registros nuevos ni se atribuye a sus
contratos una implementación que no documentan.

| Tema | Fuente canónica y justificación disponible | Límite para la memoria |
| --- | --- | --- |
| Separación frontend/API/processor y cola | [Arquitectura, §7](../architecture.md#7-por-que-esta-separado-asi): aislar interfaz, acceso y trabajo lento; permite evolucionar/escala independiente. | Posibilidad arquitectónica, no benchmark de escalado. RabbitMQ no implica exactly-once; ADR-0009 detalla el residual. |
| CockroachDB operativo frente a índice vectorial | [Arquitectura, §4](../architecture.md#4-que-papel-tienen-rabbitmq-cockroachdb-y-pgvector) y ADR-0013: separar estado de negocio e índice. | La razón documentable para conservarlo es compatibilidad con esquema y servicios existentes. No se ha localizado comparación original con PostgreSQL ni prueba de necesidad de SQL distribuido; confirmar con autores antes de afirmar superioridad. |
| Corpus y procedencia | [Índice del corpus](../assistant-corpus/README.md): manifiesto y documentos versionados con alcance y fuentes. | Corpus local/dataset simulado; no acredita ingesta completa ni documentos tenant. |
| Normalización FinOps | [Normalización Azure](../architecture/azure-cost-normalization.md): contrato de importes, moneda y dimensiones, separado del formato posicional de la API. | Evidencia de datos normalizados; no prueba cobertura de una factura real. |
| Tools y autoridad | [Contrato de tools](../architecture/finops-agent-tools.md): el modelo propone y la aplicación autoriza/ejecuta, con contexto no controlado por el modelo. | Contrato no equivale a todas las tools implementadas. |
| Respuesta y guardrails | [Contrato FinOps](../architecture/finops-response-guardrails.md) y [evidencia JUP-024](../evidence/JUP-024-validation.md): cifras deterministas, schema y citas verificables frente a texto libre. | No acredita calidad del vertical completo ni ejecución del corpus con LLM real. |

### Uso en memoria y respuestas al tutor

Para cada afirmación, citar la fila y su documento: problema → elección → alternativa
no elegida → consecuencia → evidencia fechada → límite. Para «¿por qué ese modelo?»
usar ADR-0002 y su benchmark, declarando la aceptación pendiente; para «¿por qué
pgvector?», ADR-0013, sin afirmar comparación de rendimiento; para «¿dónde se
despliega?», ADR-0015, distinguiendo demo local de producción.

La memoria editable conserva su fuente establecida por
[JUP-062](../../openspec/changes/jup-062-business-memory/proposal.md); este índice es
material de referencia y no certifica que el contenido ya esté incorporado allí.
[Auditoría y comprobaciones JUP-061](../evidence/JUP-061-validation.md).

### Pendientes documentales antes del freeze

- ADR-0002: completar condiciones de aceptación en su tarjeta de origen; no
  convertir el merge del documento en aprobación de los cuatro miembros.
- ADR-0005 y ADR-0013/14/15: confirmar o rechazar ratificación con evidencia atribuible.
- Confirmar justificación original de CockroachDB si se quiere defender una ventaja
  comparativa, y registrar decisión de despliegue final cuando exista en su tarea.

Integración #51/#53/#54/#59 y enlaces locales reconciliados el 03/10; ese
pendiente queda resuelto sin copiar documentación ni ratificar propuestas.

## Naming And Status

- Store records as `docs/adr/ADR-0001-short-slug.md` and increment numbers sequentially.
- Use `Proposed`, `Accepted`, `Superseded` or `Deprecated` as the record status.
- Link the related Trello card, `JUP-XXX` identifier and OpenSpec change.
- Link replacement records whenever an existing ADR is superseded.

## When An ADR Is Required

Create or update an ADR for durable decisions affecting:

- service or application boundaries;
- persistence, queues, vector stores or synchronization;
- authentication, security, identity, permissions or tenancy;
- critical external providers and integration ownership;
- LLM, RAG, agent or FinOps cost architecture; or
- shared patterns affecting several modules or future tasks.

Local implementation details, small refactors and documentation-only changes without architectural impact do not require an ADR. Record `ADR: not applicable` in the OpenSpec change when appropriate.

## Workflow

1. Decide during OpenSpec proposal/design whether the Trello task requires an ADR.
2. Start from `docs/templates/adr.md` and link the relevant `JUP-XXX` card.
3. Link the ADR from the OpenSpec `design.md` and keep its status `Proposed` during review.
4. Once accepted, preserve the decision in Git-tracked documentation and update `docs/architecture.md` if the current architecture changes.
