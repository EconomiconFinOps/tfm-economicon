# Evidencia técnica — JUP-054

Fecha: 2026-10-10. Tarjeta: https://trello.com/c/ZsxwmagI.
Base auditada: `c2995a118d419dfe725247bac9c6f219a3f0ea77` (`origin/develop`).
Rama propia: `test/JUP-054-critical-flows`.

## Alcance y atribución

Contribución técnica preparada a petición del usuario en copia aislada
`C:/Users/DanteInferno/Documents/Economicon/tfm-economicon-jup054`.
No se modifica el checkout compartido ni una rama de implementación ajena.

Roles confirmados por integración oficial Trello de DockerServer el 10/10:
Lucia Mateo, liderazgo; Paris Arcos Martin, pairing/coautoría; Victor Mendez,
revisión; Alejandro Aguado, validación/pruebas/documentación. Se conserva ese
reparto. Esta rama aporta pruebas para su adopción por la responsable y no es
una validación independiente de los propios cambios. Pairing, aceptación y
dictámenes humanos no se infieren de la ejecución automatizada.

## Cambios comprobables

- [Matriz de riesgos, suites y reproducción](../testing/critical-flows.md).
- OpenSpec `jup-054-test-strategy-and-critical-flows` con escenarios y límites.
- AgentRuntime → LangGraph → IngestTask → repositorio SQLite: salida validada y
  dos rutas de rechazo antes de embeddings/vector. Proveedor/vector doblados.
- API Azure local por HTTP → cliente/normalizador → SQL SQLite: paginación,
  reejecución, tenant y 401/403/404. Sin consultas a Azure cloud.
- Recorrido existente Cockroach/RabbitMQ/pgvector: lectura GET, metadata JSONB,
  mensajes/citas persistidos y denegación de acceso cruzado.
- CI ejecuta Vitest directamente en el job existente; pytest ya era directo.

## Resultados

El registro final se completa con los resultados de las ejecuciones en curso.
No se consideran acreditadas las filas pendientes.

| Verificación | Resultado observado |
| --- | --- |
| Azure Cost API, suite completa | 59 passed |
| Nueva integración agente/ingesta | 3 passed; 18 avisos existentes de datetime SQLite |
| Nueva integración productor/consumidor Azure | 4 passed; 474 avisos existentes de adaptadores SQLite |
| Backend, suite completa | En ejecución |
| Processor, suite completa offline | En ejecución |
| Recorrido real de tenant, 3 casos | Windows: 3 fallos (timeout de subprocess y 503); contraste Linux pendiente |
| Frontend Vitest | En ejecución |
| Frontend lint, tipos y build | Exit 0 en los tres; aviso de bundle grande existente |
| `node --test tools/ci-workflow.test.mjs tools/pr-policy.test.mjs tools/repository-governance.test.mjs` | 82 passed |
| `corepack pnpm jup:check:all` | Exit 0 |
| `corepack pnpm openspec:validate` | 56 passed, 0 failed |

## Entorno y comandos

Windows; Node `24.14.1`, pnpm `9.0.0`, Vitest `3.2.7`; Python `3.12.13`.
Entorno virtual nuevo dentro de esta copia, instalando los requirements-dev de
los tres servicios. CI usa Node 22 y entornos Python separados; ese matiz se
conserva para no equiparar entornos distintos.

Desde cada servicio se usó `../../.venv/Scripts/python.exe -m pytest tests -q -ra
--junitxml=../../.artifacts/jup054/<servicio>.xml`, con `--basetemp` propio cuando
procedía. Backend/Azure/processor se ejecutan en procesos distintos.
Frontend: `corepack pnpm --filter @finops/frontend exec vitest run --maxWorkers=1`,
seguido de comandos directos de lint, typecheck y build. Ningún resultado procede
de un hit de caché Turbo.

El recorrido real usa sólo los contenedores efímeros `economicon-jup054-crdb`,
`economicon-jup054-vector`, `economicon-jup054-rabbit` con imágenes Cockroach
`v24.1.11`, pgvector `pg17` y RabbitMQ `3.13-management`. Docker apunta a
DockerServer; puertos loopback 46454/45454/45654 y túnel SSH propio. Límites de
memoria y CPU; ningún volumen compartido ni servicio existente se reutiliza.
Comando: desde processor, variables de la [guía](../testing/critical-flows.md),
`python -m pytest tests/test_tenant_isolation_integration.py -q -ra` con XML y
temporal propios. El ciclo de vida/limpieza se registra al finalizar.

Logs, XML y versiones resueltas están en `.artifacts/jup054/` de la copia local,
excluidos de Git. No se guardan secretos. Los avisos de permisos de temporales
del sandbox requirieron ejecuciones autorizadas fuera de él; esos intentos
fallidos no cuentan como fallos funcionales ni como pruebas superadas.

## Criterios y pendientes

| Criterio de Trello | Evidencia / situación |
| --- | --- |
| Resultado funcional verificable | Nuevas aserciones sobre contratos, persistencia y errores; matriz enlazada |
| Pruebas necesarias añadidas y en verde | Casos nuevos identificados; ejecución completa pendiente según tabla |
| Documentación y decisiones actualizadas | Matriz, OpenSpec y continuidad de esta copia |
| Pull request revisado y vinculado | Contribución preparada; publicación/enlace y revisión humana pendientes |
| Validación funcional y evidencia enlazadas | Este informe es evidencia técnica propia; aceptación independiente pendiente |

No acredita Azure cloud, modelos externos, gateway LiteLLM real, reinicio de
RabbitMQ, todas las migraciones, todo Docker Compose ni navegador real. Las
suites opt-in omitidas conservan sus skips; RF-096-004 (infraestructura en CI)
sigue separado. No se cierra la tarjeta ni se altera su prioridad/roles/fecha.
