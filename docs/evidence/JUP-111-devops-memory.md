# JUP-111 — Evidencia del apartado f de la memoria

Fecha de contraste: 10/10/2026 (Europe/Paris). [Trello](https://trello.com/c/mnqNDpC0). [Contrato](../../openspec/changes/jup-111-devops-memory/proposal.md). Fuente canónica y reglas: [JUP-062](../memoria/README.md).

[PR #87](https://github.com/EconomiconFinOps/tfm-economicon/pull/87), draft contra
develop. CI [38034787702](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38034787702)
SUCCESS sobre entrega `1eaa36f15785dc8ad8e1c8c15594d09ce19903a3`;
`PR reviews` 38034787828 no satisfecho, dictámenes humanos pendientes.
Los cambios posteriores de esta entrega sólo añaden estos enlaces y el recibo
Trello; no se atribuye el run anterior a otro SHA.

## Estado de entrega

Propuesta completa de nueve párrafos y lista de cobertura preparada fuera de Git en `materiales/06-entregables/JUP-111-propuesta-2026-10-10/`, relativa al workspace padre del clon. No es copia de la memoria ni exportación del Google Doc. El manifiesto de esa carpeta identifica `apartado-f.md` y `cobertura-y-entrega.md`. Su publicación queda pendiente de revisión humana y reconciliación con el fragmento existente; no se acredita incorporación, formato final, máximo de páginas o aceptación.

Se leyó íntegro el `Guion_PJ.md` enlazado en la tarjeta de coordinación: descripción de f, requisitos técnicos/funcionales y evaluación de ejecución. La cobertura externa apunta a P1–P9 y conserva los pendientes. No se leyó la memoria completa; no se verificó el PDF original del guion.

## Corte reproducible de las fuentes

- Código: `c2995a118d419dfe725247bac9c6f219a3f0ea77` (origin/develop al preparar el clon). No se toma el checkout compartido, situado en otra rama con cambios ajenos, como fuente de implementación.
- Trello: integración exclusiva DockerServer, snapshot `snapshot-20261010T071023Z.json`; JUP-111 `6ac8aac590839c9137dc8ef7`, lista Backlog al leer; roles sin cambios. Registro filtrado externo `trello-source.json`.
- CD: [PR #73](https://github.com/EconomiconFinOps/tfm-economicon/pull/73), OPEN/no merge; head `a75472d9e83af56e4ecc4ae1f3acc50d5178e55e`. [Validación Paris](https://github.com/EconomiconFinOps/tfm-economicon/pull/73#pullrequestreview-5470395430), 09/10/2026 13:05:25Z, leída completa. La relectura del PR no es ejecución del stack.
- Se consultó `docs/continuidad/cd-dockerserver.md` del espacio compartido y se contrastaron sus conclusiones con el PR y la review actual; no se copia ni cambia ese tema desde esta tarjeta.

## Matriz de afirmaciones y límites

| Propuesta | Fuente técnica o evidencia | Lo acreditado y límite |
| --- | --- | --- |
| P1 | [CONTRIBUTING](../../CONTRIBUTING.md), [ADR / JUP-061](../adr/README.md) | Trazabilidad y separación de roles; no acredita participación realizada |
| P2–P3 | [CI](../../.github/workflows/ci.yml), [JUP-051](JUP-051-validation.md) | Push/PR/manual, Node 22/Python 3.12; compilación Python es sintaxis. CI no ejecuta build/up Docker |
| P3 | Runs [37303424060](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37303424060) y [37303417458](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37303417458) | Jobs reconsultados el 10/10: PR 7 success; push 6 success/policy skipped. Ejecuciones históricas del 05/10 sobre entrega `1a83c1d`, no pruebas nuevas de `c2995a1` |
| P4 | [Compose](../../docker-compose.yml), [JUP-049](JUP-049-validation.md), [JUP-050](JUP-050-validation.md) | Cuatro imágenes, configuración y runtime aislado. DockerServer JUP-049: Docker 29.6.2/Compose 5.3.1, tree `1d05259b2db193bded864d7491a238d89e0f524c`; JUP-050: Docker Desktop Engine 29.7.2. No promoción automática ni producción |
| P5 | [Convenciones](../manuals/python-service-conventions.md), [JUP-044](../../openspec/changes/archive/2026-09-08-jup-044-e2e-tracing/review.md) | JSON stdout y request_id API/RabbitMQ/worker con reintentos; no cobertura total batch ni spans distribuidos |
| P6 | [Prometheus](../../apps/monitoring/prometheus/prometheus.yml), [alerta](../../apps/monitoring/grafana/provisioning/alerting/ingest-failures.yml), [JUP-045](JUP-045-validation.md) | Scrape 15 s; fallos persistidos, incluidos reintentos, no jobs únicos; regla >2 en 5 min durante 2 min; sin receptor externo acreditado ni SLO medido |
| P7–P8 | [Guía CD del SHA auditado](https://github.com/EconomiconFinOps/tfm-economicon/blob/a75472d9e83af56e4ecc4ae1f3acc50d5178e55e/docs/deployment/dockerserver-cd.md) y review Paris citada arriba | Ubuntu WSL/Python 3.12.3/Docker 28.0.4/Compose 2.34.0; cuatro builds, mock y smoke 5/5. `current=a75472d`, `run_id=null`: ensayo local, no timer/promoción integrada/reboot; UI sólo HTTP |
| P9 | [ADR-0005](../adr/ADR-0005-prometheus-grafana-metrics.md), [ADR-0018 en PR73](https://github.com/EconomiconFinOps/tfm-economicon/blob/a75472d9e83af56e4ecc4ae1f3acc50d5178e55e/docs/adr/ADR-0018-private-dockerserver-cd.md), [memoria](../memoria/README.md) | Ambos Proposed en las fuentes; revisar/exportar con hash pendiente, sin aceptación editorial inferida |

Las fuentes de código se fijan por SHA en la propuesta externa. Los enlaces relativos de esta matriz son referencias mantenibles del repositorio; los resultados históricos permanecen atribuidos a sus versiones originales. No se reejecutaron Docker, inferencias, servicios compartidos o despliegues por esta tarea documental.

## Aceptación de la tarjeta

| Criterio original | Entrega verificable | Pendiente |
| --- | --- | --- |
| Resultado funcional verificable | Propuesta externa f, cobertura del guion y fuentes fechadas | Revisión humana e incorporación a la memoria canónica |
| Pruebas necesarias añadidas y en verde | Controles documentales, trazabilidad y OpenSpec; no se añaden tests de producto para prosa | Formato/paginación tras incorporación; resultados de controles propios debajo |
| Documentación y decisiones actualizadas | Matriz, contrato y continuidad; sin ratificar ADR ajenos | Actualizar evidencia al exportar |
| Pull request revisado y vinculado | PR documental para revisar el contrato y la evidencia | Reviews humanas y merge; no sustituyen revisión del contenido externo |
| Validación funcional y evidencia enlazadas | Fuentes de cada afirmación y manifiesto externo | Validación de Víctor y review de Lucía del entregable por fecha/hash; pairing Paris no acreditado |

## Verificación propia

Entorno: Windows, Node `24.14.1`, pnpm `9.0.0`, OpenSpec declarado `1.8.0`. No se equipara este entorno con el runner Ubuntu/Node 22 de CI. Logs y recibos quedan en `materiales/07-evidencias/JUP-111-devops-2026-10-10/` fuera de Git.

| Comprobación ejecutada | Resultado |
| --- | --- |
| `node --test tools/jup-check.test.mjs tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs tools/jup-cleanup-check.test.mjs` | 95/95, sin omisiones |
| `node tools/jup-check.mjs --all` | Correcto, incluido JUP-111 |
| `node tools/jup-cleanup-check.mjs` | 980 archivos correctos |
| `corepack pnpm openspec:validate` | 56/56, estricto, sin fallos |
| `node materiales/07-evidencias/JUP-111-devops-2026-10-10/validate-documents.mjs` desde el workspace padre | 9 párrafos, 40 enlaces, 16 fuentes fijadas por SHA, 2 hashes de propuesta correctos, 9 archivos en alcance |
| Control negativo de integridad, sin alterar archivos | 2/2 copias en memoria con bytes añadidos rechazadas por hash |
| `git diff --check` | Correcto |

La primera invocación de tests/higiene falló por EPERM al crear subprocesos
Node/Git en el sandbox; el reintento autorizado pasó. Se conservan los logs
iniciales y los `*-final.log`, sin presentar el error de entorno como prueba
funcional fallida. No fue necesario cambiar dependencias o código de producto.

Auditoría documental interna independiente: acotó request_id a
`POST /jobs/ingest`, precisó ventana/persistencia de la alerta y rollback con
volúmenes propios; se incorporaron las tres precisiones y se trasladó el control
editorial fuera de la prosa académica. No equivale a revisión humana de Lucía
ni validación de Víctor.

Identidad de la propuesta revisable (SHA-256 de los bytes):

- `apartado-f.md`: `e67bed4cad881d9b7a103093329594e8e2a595c5bb6518068b296dfc1f5367d2`.
- `cobertura-y-entrega.md`: `4a85f3d73a8a97362df5a5828c8891df68c1b6426ef8b36c0b9ae867e0a20bab`.

Estos hashes identifican propuestas externas, no una exportación canónica ni
un dictamen aceptado. El control documental y los hashes de fuentes están
conservados en `document-checks.json` y `pinned-source-hashes.json` externos.

Sin escritura de memoria/Discord, cambios de prioridades o roles, despliegue, merge o declaración Hecho. El change sigue activo hasta la publicación y aceptación, según las tareas explícitamente pendientes.

Enlace operativo publicado mediante integración DockerServer: comentario
`6ac9eb23166e2ecab90fd85d`, 10/10/2026 07:37:07Z; tarjeta situada en
`30 — En curso`, sin marcar los criterios como aceptados. Se mantiene P0 y los
cuatro roles. Recibo externo `trello-readback.json`. El conector GitHub rechazó
la creación con 403; la CLI autenticada como `Iber1to` creó la PR, sin cambiar
atribuciones.
