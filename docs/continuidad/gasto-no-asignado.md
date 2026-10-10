# Gasto No Asignado — JUP-028

Última verificación: 10/10/2026, Europe/Paris. Origen: encargo «Implementa
JUP-028 — Detectar gasto no asignado» desde el chat
`01a1248a-4e9e-7963-a891-5d8cb49345a6`.
[Tarjeta](https://trello.com/c/RG9O2Ltx), prioridad P1 · Valor FinOps.

## Alcance Y Estado

Implementación técnica de `GET /billing/unallocated-cost` en el worktree aislado
`../tfm-economicon-jup028`, rama `feat/JUP-028-unallocated-cost`, base
`origin/develop` `c2995a118d419dfe725247bac9c6f219a3f0ea77`. El checkout canónico
compartido no es el destino de edición. El usuario autorizó esta implementación
el 10/10; las restricciones históricas de no comenzar código no bloquean el
encargo actual.

Trello se leyó por la integración oficial
`DockerServer:/home/danteadmin/economicon-collaboration`; criterios y roles
seguían sin cambios. No existía una PR de JUP-028 en la consulta inicial.
El registro de partida está en
`../materiales/07-evidencias/hito-mvp-2026-10-09/backlog-dispatch-source.json`
relativo a la raíz del repositorio. Publicación, CI, pairing y reviews humanas
siguen pendientes al redactar este estado. No hay aceptación ni merge acreditados.

## Decisiones Confirmadas

- Detectar **candidatos por metadatos incompletos**. La respuesta declara
  `detection_basis=observed_required_tags` y `allocation_status=not_evaluated`.
  Una regla organizativa externa puede asignar un coste aunque falte owner;
  no equiparar incumplimiento de tagging y asignación contable.
- Reutilizar byte por byte la política `economicon-minimum-v1` de JUP-017 PR #66:
  owner, environment, application, cost_center, project. No integrar toda esa
  PR ni atribuirle validación conjunta. La propuesta antigua del corpus con
  businessunit no sustituye las dimensiones de Trello ni se corrige en silencio.
- Particionar cada registro por su conjunto completo de defectos; un importe
  sólo aparece una vez. `no_owner`, `unclassified` y
  `no_owner_and_unclassified` son motivos de metadatos, no estados financieros.
- Mantener monedas separadas, cargos positivos como denominador, ajustes
  negativos y netos explícitos; Decimal y strings de dos decimales. Aplicar el
  complemento del porcentaje redondeado de metadatos completos como JUP-017.
- Aplicar el ámbito tenant/suscripción/run completado y UTC `[inicio, fin)`.
  Rechazar múltiples ingestas completadas por suscripción/día con 409 sin
  importes; no inventar identidad de cargo por recurso/hash. Exponer registros
  sin fecha excluidos y estado parcial.
- Limitar la entrega a API, pruebas y documentación. No introducir recursos,
  UI, reglas de reparto, catálogos, remediación ni estados shared/excluded.

El contraste local del 10/10 con la taxonomía candidata JUP-015 y el contrato
showback JUP-027 está en [el contrato API](../api/unallocated-cost.md). Coinciden
las reglas mínimas de tags, pero showback agrupa por una dimensión y admite
fallback de columna project. Sus importes no son intercambiables ni sumables
con esta unión de defectos. La integración entre las tarjetas no está probada.

## Evidencia Disponible

La [evidencia por criterio](../evidence/JUP-028-validation.md) contiene comandos,
versiones, casos, límites y el fallo de entorno Windows. La
[especificación activa](../../openspec/changes/jup-028-unallocated-cost/specs/unallocated-cost/spec.md)
y el [diseño](../../openspec/changes/jup-028-unallocated-cost/design.md) describen
el contrato. No duplicar sus tablas en este resumen.

- Python 3.12.13 local, CockroachDB v24.1.11 real exclusivo
  `economicon-jup028-tests`, puerto local 28428 y fixtures sintéticas:
  `python -m pytest tests/test_unallocated_cost.py tests/test_billing_summary.py tests/test_tenant_isolation_api.py -q`
  produjo **55 passed**, 911.22 s, 723 avisos de deprecación SQLite.
- Esa ejecución recogió las 22 pruebas JUP-028 originales. El archivo final
  tiene 23; el caso nuevo de frontera 20000/19999 con neto cero se verificó
  después en Linux. No presentar las 55 como prueba de ese caso añadido.
- Gobernanza de PR/CI/repositorio: **82 passed**. OpenSpec estricto: **56
  elementos correctos**. Trazabilidad JUP, higiene y compileall inicial correctos.
- La regresión completa Windows se interrumpió; un caso existente de salud
  que parchea `socket.connect` falla al interceptar la creación de
  `asyncio.ProactorEventLoop`. Reproducción aislada: **1 failed**, 9.54 s.
  No se modificó producto de salud ni se declara la batería completa aprobada.
- Regresión completa Linux: **934 passed, 21 skipped**, 2436 avisos,
  157.49 s, incluidos los 23 casos finales JUP-028 con Cockroach real. Imagen
  `jup047-review-20261008-6c760562-review-tests:latest`, código exclusivo
  `/tmp/economicon-jup028-985d` de sólo lectura y el mismo Cockroach. Digest,
  comando y versiones efectivos están en la evidencia. Las 21 pruebas
  omitidas no se consideran validadas: dependencias opcionales del cliente
  LiteLLM del processor, RabbitMQ/reinicio y vector store no activadas.
- Control final de gobernanza tras el puntero AGENTS: **13 passed**. La política
  coincide con JUP-017 mediante SHA-256
  `7F95EF43BA5A5EE62392E44E0766CA46AF0D608F182CAC1BCFF3390398FFA039`.
- Entorno retirado: contenedor `economicon-jup028-tests`, túnel SSH 28428 y
  contenedor Linux de regresión terminados. No quedan servicios de prueba
  ejecutándose; se conserva `/tmp/economicon-jup028-985d` para reproducción.

Las pruebas del API usan dobles de clientes de recursos; no acreditan todos los
servicios desplegados. La fuente puede perder tags al agregar y no garantiza
factura completa ni catálogo organizativo. Los resultados son candidatos sobre
datos observados y no prueban la ausencia de etiquetas en Azure.

## Próximos Pasos

1. Finalizar evidencias y tareas OpenSpec; al archivarlo, corregir los enlaces
   activos de esta continuidad, evidencia y documentación relacionada.
2. Preparar/publicar la PR contra develop, registrar CI y enlazarla desde Trello
   exclusivamente mediante la integración oficial.
3. Mantener los roles de Trello: Victor Mendez liderazgo, Alejandro Aguado
   pairing, Lucia Mateo revisión, Paris Arcos Martin validación. Acreditar cada
   participación real y las dos reviews requeridas sin inventarlas. Las pruebas
   propias no sustituyen la validación independiente.

No enviar mensajes Discord sin autorización específica ni cerrar/archivar el
chat por inferencia del estado técnico.
