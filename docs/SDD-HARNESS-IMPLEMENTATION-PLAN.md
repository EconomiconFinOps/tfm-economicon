# Plan de implementación del harness SDD

**Estado:** activo

**Objetivo:** construir un harness SDD determinista, trazable y gobernado por el backbone técnico

**Método de seguimiento:** marcar cada checkbox como `[x]` únicamente cuando cumpla su criterio de finalización

## 1. Archivos de referencia

### 1.1. Fuentes de verdad obligatorias

Estos documentos deben consultarse antes de diseñar o ejecutar cualquier fase:

| Archivo | Rol |
|---|---|
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | Backbone técnico normativo. Sus invariantes `ARCH-*` son bloqueantes. |
| [`architecture-status.md`](./architecture-status.md) | Registro vigente de gaps, evidencias y orden de remediación. |
| [`SYSTEM-OVERVIEW.md`](./SYSTEM-OVERVIEW.md) | Contexto funcional y relación general entre componentes. |
| [`../sdd-planing.md`](../sdd-planing.md) | Propuesta inicial del workflow, skills, agentes y contratos. Es referencia de diseño, no prevalece sobre `ARCHITECTURE.md`. |
| [`../README.md`](../README.md) | Stack, comandos principales y estado general del repositorio. |
| [`turborepo_use.md`](./turborepo_use.md) | Convenciones operativas del monorepo. |

### 1.2. Configuración y código que deben verificarse

| Ruta | Información que aporta |
|---|---|
| `package.json` | Comandos raíz disponibles. |
| `turbo.json` | Pipeline actual de build, lint y test. |
| `pnpm-workspace.yaml` | Workspaces administrados por pnpm. |
| `docker-compose.yml` | Topología y configuración del entorno local. |
| `apps/frontend/package.json` | Checks disponibles para frontend. |
| `apps/backend/package.json` y `requirements-dev.txt` | Checks y dependencias de desarrollo del backend. |
| `apps/processor/package.json` y `requirements-dev.txt` | Checks y dependencias de desarrollo del processor. |
| `docs/rejected/` | Historial de alternativas descartadas. Nunca es fuente de verdad vigente. |

### 1.3. Precedencia

En caso de contradicción se aplicará este orden:

1. `docs/ARCHITECTURE.md` y ADRs aprobadas.
2. PRD y TDR aprobados de la HU activa.
3. Contratos versionados del harness.
4. Este plan de implementación.
5. Código y configuración existentes.
6. Documentación histórica o rechazada.

## 2. Reglas para actualizar este plan

- Un ítem solo pasa a `[x]` cuando su criterio de finalización es verificable.
- El cierre debe añadir una referencia a la HU, commit, PR o evidencia correspondiente.
- Un ítem parcialmente implementado permanece en `[ ]` y puede incluir una nota de progreso.
- Los cambios de alcance deben registrarse en la sección `Decisiones del plan`.
- No se puede marcar una fase completa si alguno de sus entregables obligatorios sigue abierto.
- Los gaps de arquitectura se cierran únicamente en `architecture-status.md`; este plan solo refleja el progreso del harness.

## 3. Fase 0 — Contrato del workflow

**Objetivo:** convertir el flujo SDD en una máquina de estados no ambigua.

**Referencias:** `sdd-planing.md`, `ARCHITECTURE.md`, `architecture-status.md`.

- [x] Definir los tipos de cambio iniciales: `feature`, `remediation` y `harness-docs`.
- [x] Definir las etapas: `INTAKE`, `PRD`, `TDR`, `PLAN`, `EXECUTION`, `VERIFICATION`, `REVIEW` y `COMPLETED`.
- [x] Definir estados de artefacto: `DRAFT`, `CHANGES_REQUESTED`, `APPROVED` y `REJECTED`.
- [x] Definir estados de ejecución: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` y `BLOCKED`.
- [x] Documentar todas las transiciones válidas y los retornos a etapas anteriores.
- [x] Definir qué aprobación humana requiere cada transición.
- [x] Definir qué cambios invalidan PRD, TDR, plan o review ya aprobados.
- [x] Asociar toda aprobación a versión, hash, identidad del aprobador y fecha.
- [x] Definir cómo se aplican los gaps bloqueantes según el tipo y alcance de la HU.
- [x] Revisar y aprobar humanamente `docs/SDD-WORKFLOW.md` y `.sdd/policies/workflow.yaml`.

**Done cuando:** existe un contrato único del workflow, revisado humanamente, sin transiciones implícitas ni estados sin salida.

## 4. Fase 1 — Estructura y manifiesto de una HU

**Objetivo:** establecer la estructura persistente y la fuente de verdad del estado.

**Estructura objetivo:**

```text
.sdd/
├── README.md
├── config.yaml
├── schemas/
├── templates/
├── policies/
└── commands/

SPEC/
└── examples/
    └── HU-000-fixture/
        ├── manifest.yaml
        ├── user-story.md
        └── journal.ndjson

packages/
└── sdd-harness/
    ├── src/
    └── tests/
```

- [x] Crear la estructura base `.sdd/` y `SPEC/`.
- [x] Definir el schema inicial de `manifest.yaml`.
- [x] Incluir `story_id`, `change_type`, `correlation_id`, etapa y estado actuales.
- [x] Incluir versiones, hashes y aprobaciones de artefactos.
- [x] Incluir `ARCH-*`, gaps y ADRs aplicables.
- [x] Incluir tareas, checks requeridos y resultados.
- [x] Definir la convención de IDs para HU, requisitos, decisiones, tareas, tests y hallazgos.
- [x] Crear una HU mínima de ejemplo que valide el schema.

**Done cuando:** `manifest.yaml` permite reconstruir el estado de una HU sin interpretar texto libre ni consultar memoria externa.

## 5. Fase 2 — Orquestador determinista

**Objetivo:** impedir que agentes o humanos salten etapas o consuman artefactos obsoletos.

**Comandos mínimos objetivo:**

```text
sdd init
sdd validate
sdd status
sdd approve
sdd next
sdd run
sdd review
```

- [x] Seleccionar y documentar el runtime del CLI.
- [x] Implementar carga y validación de configuración y manifiesto.
- [x] Implementar `sdd init` sin sobrescribir artefactos existentes.
- [x] Implementar `sdd validate` con errores estructurados y exit codes estables.
- [x] Implementar `sdd status` mostrando etapa, bloqueos y siguiente acción permitida.
- [x] Implementar aprobaciones ligadas al hash del artefacto.
- [x] Implementar invalidación automática de artefactos dependientes.
- [x] Implementar validación de transiciones mediante la máquina de estados.
- [x] Implementar journal append-only de acciones del harness.
- [x] Detectar, bloquear e invalidar cambios fuera del alcance; la prevención física corresponde a permisos de agentes en Fase 5.
- [x] Añadir tests unitarios y de integración del orquestador.

**Done cuando:** ninguna transición inválida, aprobación obsoleta o payload fuera de schema puede ser aceptado por el CLI.

### Fase 2.1 — Hardening del orquestador

- [x] Centralizar las mutaciones en preflight, reconciliación aislada, staging, validación y commit transaccional.
- [x] Validar el estado actual y el estado staged antes de persistir manifest, journal, snapshots o evidencias.
- [x] Confinar paths al repositorio y estado interno al directorio canónico de la HU.
- [x] Validar contexto, hashes, journal head y escrituras de intents de recuperación.
- [x] Recuperar explícitamente locks locales obsoletos sin eliminar locks de procesos vivos.
- [x] Publicar schemas Draft 2020-12 de inputs normalizados y envelope de salida.
- [x] Rechazar flags desconocidos, duplicados, enums inválidos y enteros mal formados.
- [x] Aplicar `EX-001`–`EX-007`, checks requeridos, executor explícito, evidencias y retry humano.
- [x] Probar el CLI como subprocess real en JSON/text y exit codes `0/1/2`.
- [x] Mantener intactos los contratos aprobados de Fase 0.

**Done cuando:** todo comando mutante produce un estado aceptado por `sdd validate`, todos los paths quedan confinados y la suite pública verifica gates, transacciones y proceso real.

## 6. Fase 3 — Schemas y plantillas

**Objetivo:** normalizar entradas, salidas y artefactos sin duplicar su contenido.

- [x] Versionar schemas con JSON Schema Draft 2020-12 y catálogo SemVer.
- [x] Definir el contrato común de entrada de skills.
- [x] Definir el contrato común de salida y errores.
- [x] Referenciar artefactos y documentación por ruta, versión y SHA-256.
- [x] Crear templates para `user-story`, PRD, TDR, roadmap, task, execution summary, verification evidence y review.
- [x] Exigir `Documentación consultada` y `ARCH-* aplicables` en los artefactos técnicos.
- [x] Definir hallazgos con severidad, evidencia, trazabilidad contractual, resolución y estado.
- [x] Añadir fixtures válidos e inválidos para cada schema de artefacto y skill.
- [x] Añadir contract tests de compatibilidad y validación pública por CLI.

**Done cuando:** todos los payloads y artefactos estructurados pueden validarse automáticamente y los ejemplos inválidos son rechazados.

## 7. Fase 4 — Skills

**Objetivo:** implementar procedimientos especializados sin delegarles el control del workflow.

Orden obligatorio:

- [x] Crear `spec-intake`.
- [x] Crear `prd-generator`.
- [x] Crear `tdr-generator`.
- [x] Crear `task-planner`.
- [x] Crear `plan-executor`.
- [x] Crear `verifier`.
- [x] Crear `reviewer`.

Cada skill debe completar este checklist:

- [x] Declara schema y versiones de entrada/salida.
- [x] Declara documentación obligatoria y reglas de precedencia.
- [x] Declara archivos de lectura y escritura permitidos.
- [x] Declara estados, errores y prohibiciones.
- [x] No cambia la etapa ni autoaprueba su salida.
- [x] Registra artefactos, documentos consultados, conflictos y trazabilidad.
- [x] Incluye casos de prueba positivos, negativos y de bloqueo.

**Done cuando:** cada skill puede ejecutarse aisladamente con fixtures y el orquestador rechaza cualquier salida que incumpla su contrato.

## 8. Fase 5 — Agentes y permisos

**Objetivo:** asignar responsabilidades sin solapamientos ni autoaprobación.

- [x] Crear `product-analyst` para intake y PRD.
- [x] Crear `technical-architect` para TDR y cumplimiento `ARCH-*`.
- [x] Crear `delivery-planner` para roadmap y tareas.
- [x] Crear `implementation-agent` limitado al alcance aprobado.
- [x] Crear `verification-agent` independiente para la etapa de verificación.
- [x] Crear `review-agent` independiente del implementador y del verificador.
- [x] Definir contratos declarativos de permisos por agente.
- [x] Incorporar un runner controlado de `codex exec` con sandbox dinámico, red deshabilitada y approval policy `never`.
- [x] Impedir que un agente apruebe su propio trabajo.
- [x] Impedir que implementation-agent modifique PRD, TDR o backbone.
- [x] Registrar agente, skill, inputs, outputs, permisos, runtime y resultado de cada ejecución.
- [x] Probar intentos de acceso y modificación no autorizados, incluida una prueba real del sandbox.

**Done cuando:** los límites de cada rol se validan automáticamente antes y después de su ejecución.

## 9. Fase 6 — Integración arquitectónica

**Objetivo:** convertir `ARCHITECTURE.md` y `architecture-status.md` en gates ejecutables.

- [ ] Exigir matriz `ARCH-*` en cada TDR.
- [ ] Relacionar invariantes con requisitos, tareas y tests.
- [ ] Detectar gaps aplicables según componentes, datos y flujos afectados.
- [ ] Aplicar las reglas diferentes para `feature`, `remediation` y `harness-docs`.
- [ ] Exigir ADR aprobada para excepciones.
- [ ] Bloquear referencias a decisiones de `docs/rejected/` como solución vigente.
- [ ] Exigir actualización de `architecture-status.md` al cerrar un gap.
- [ ] Crear tests del gate con HUs de los tres tipos.

**Done cuando:** el reviewer puede justificar cada aprobación o bloqueo con invariantes, gaps y evidencias concretas.

## 10. Fase 7 — Verificación determinista

**Objetivo:** seleccionar y ejecutar checks reproducibles según el alcance del cambio.

- [ ] Crear un registro central de checks por workspace y tipo de archivo.
- [ ] Integrar lint, build y tests de frontend.
- [ ] Integrar tests de backend.
- [ ] Integrar tests de processor.
- [ ] Registrar comando, directorio, exit code, duración, commit y salida resumida.
- [ ] Impedir que una ejecución fallida sea presentada como válida.
- [ ] Añadir timeouts y clasificación de fallos del entorno.
- [ ] Diferenciar evidencia determinista de opinión del reviewer LLM.
- [ ] Añadir tests de selección de checks por alcance.

**Done cuando:** el mismo commit y configuración producen una selección de checks estable y resultados auditables.

## 11. Fase 8 — Integración CI

**Objetivo:** aplicar los gates fuera de la sesión interactiva del agente.

- [ ] Elegir y documentar la plataforma CI.
- [ ] Validar manifiesto, schemas y hashes.
- [ ] Validar etapa, aprobaciones y trazabilidad.
- [ ] Ejecutar checks técnicos aplicables.
- [ ] Ejecutar gates arquitectónicos y de gaps.
- [ ] Verificar que el review pertenece al commit evaluado.
- [ ] Bloquear hallazgos críticos y altos no resueltos.
- [ ] Publicar evidencias y resumen legible del fallo.
- [ ] Proteger secretos y limitar permisos del runner.
- [ ] Añadir una prueba end-to-end del pipeline CI.

**Done cuando:** un cambio inválido no puede integrarse aunque omita el harness local.

## 12. Fase 9 — Validación con el backlog real

**Objetivo:** utilizar los gaps como prueba real del harness.

Orden inicial recomendado:

- [ ] Ejecutar una HU para `GAP-001` y `GAP-002`.
- [ ] Ejecutar una HU para `GAP-003`.
- [ ] Ejecutar una HU para `GAP-004`.
- [ ] Ejecutar una HU para `GAP-005` y `GAP-006`.
- [ ] Registrar tiempo, interacciones humanas, regeneraciones y bloqueos por HU.
- [ ] Registrar coste/contexto de agentes y falsos positivos del reviewer.
- [ ] Ajustar templates y gates sin relajar invariantes.
- [ ] Validar que los gaps cerrados quedan trazados en `architecture-status.md`.

**Done cuando:** al menos cuatro HUs reales han atravesado el flujo completo y el harness ha demostrado trazabilidad, bloqueo y reanudación correctos.

## 13. Fase 10 — Capacidades avanzadas

Esta fase solo comienza después de cerrar la Fase 9.

- [ ] Añadir carril SDD light.
- [ ] Añadir protocolo de hotfix y normalización posterior.
- [ ] Añadir ejecución paralela con scopes de escritura aislados.
- [ ] Añadir auditores especializados donde exista evidencia de necesidad.
- [ ] Añadir memoria persistente secundaria sin sustituir documentos.
- [ ] Añadir evaluaciones de outputs LLM y regresión de prompts.
- [ ] Añadir métricas del propio harness y budgets de coste.
- [ ] Evaluar `role-guardian` según incumplimientos observados.

**Done cuando:** cada capacidad avanzada responde a una necesidad medida y conserva compatibilidad con contratos anteriores.

## 14. Definition of Done del harness completo

- [ ] El workflow es determinista y no permite saltos de etapa.
- [ ] Las aprobaciones están ligadas a versiones y hashes.
- [ ] Los agentes tienen permisos verificables y separados.
- [ ] Skills, inputs y outputs están versionados y validados.
- [ ] Existe trazabilidad `HU -> AC -> REQ -> ARCH -> DEC -> TASK -> TEST -> RESULT -> FINDING`.
- [ ] El backbone y los gaps producen gates ejecutables.
- [ ] Los checks técnicos son reproducibles y auditables.
- [ ] CI impide el bypass del workflow local.
- [ ] El flujo ha sido validado con HUs reales de remediación.
- [ ] Existe documentación suficiente para operar, diagnosticar y evolucionar el harness.

## 15. Decisiones del plan

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-06-19 | Construir primero el harness y usar los gaps como backlog inicial | La aplicación está en desarrollo y no existen usuarios ni datos reales afectados. |
| 2026-06-19 | El orquestador será determinista; los agentes no controlarán transiciones | Evita depender del comportamiento probabilístico del LLM para enforcement. |
| 2026-06-19 | Las remediaciones pueden aprobarse incrementalmente | Evita el bloqueo circular causado por gaps globales abiertos. |
| 2026-06-19 | Las capacidades avanzadas se aplazan hasta validar cuatro HUs reales | Reduce sobreingeniería y permite ajustar el proceso con evidencia. |

## 16. Registro de progreso

| Fecha | Fase | Cambio | Evidencia |
|---|---|---|---|
| 2026-06-19 | Fase 0 | Contrato humano y machine-readable implementado; pendiente de aprobación humana | `docs/SDD-WORKFLOW.md`, `.sdd/policies/workflow.yaml` |
| 2026-06-20 | Fase 0 | Contrato aprobado y Fase 0 cerrada | `.sdd/policies/workflow.approval.yaml` |
| 2026-06-20 | Fase 1 | Estructura, schema, validador determinista y fixture implementados | `.sdd/schemas/manifest.schema.json`, `packages/sdd-harness/`, `SPEC/examples/HU-000-fixture/`; lint, 15 tests, build y validación CLI |
| 2026-06-20 | Fase 2 | Orquestador determinista, persistencia transaccional, gates, scope y CLI implementados | `.sdd/commands/orchestrator.yaml`, manifest `1.1.0`, `packages/sdd-harness/src/orchestrator/`; lint, 36 tests, build y fixture válido |
| 2026-06-21 | Fase 2.1 | Hardening de preflight, transacciones, paths, locks, CLI y contrato `EX-*`; Fase 2 revalidada | `.sdd/schemas/command-*.schema.json`, `packages/sdd-harness/src/`; lint, 47 tests, build, CLI subprocess, fixture y hashes de Fase 0 |
| 2026-06-21 | Fase 3 | Manifest `2.0.0`, catálogo Draft 2020-12, artefactos Markdown tipados, contratos de siete skills, templates, reconciliación documental y CLI `contract validate` | `.sdd/schemas/catalog.yaml`, `.sdd/schemas/artifacts/`, `.sdd/schemas/skills/`, `.sdd/templates/`, `packages/sdd-harness/src/contracts/`; lint, 64 tests, build, fixture HU-000, CLI subprocess y hashes de Fase 0 |
| 2026-06-22 | Fase 4 | Siete skills de proyecto y protocolo transaccional `prepare -> validate -> submit` implementados sin ejecución de agentes | `.agents/skills/`, `.sdd/skills/catalog.yaml`, `packages/sdd-harness/src/skills/`; lint, 83 tests, build, ciclo completo, CLI subprocess, fixture HU-000 y hashes de Fase 0 |
| 2026-06-22 | Fase 5 | Seis agentes Codex, catálogo de permisos, runner no interactivo, leases, identidad ligada y auditoría implementados | `.codex/agents/`, `.sdd/agents/catalog.yaml`, `packages/sdd-harness/src/agents/`; lint, 92 tests, build, CLI subprocess, fixture HU-000, smoke real de sandbox y hashes de Fase 0 |
