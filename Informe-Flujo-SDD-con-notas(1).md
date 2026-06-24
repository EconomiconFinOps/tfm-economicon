# Informe — Flujo SDD de isEazy Expert Studio

**Proyecto:** oNext SaaS Core / isEazy Expert Studio  
**Fecha:** 2026-06-19  
**Autor:** generado para París Arcos  
**Versión:** Flujo SDD actual + notas de mejora

---

## 0. Qué es y dónde está documentado

El proyecto aplica **SDD (Spec-Driven Development)** con quality gates cuantificados, agentes especializados, subagentes auditores, hooks de Claude Code y enforcement en CI.

La fuente de verdad operativa es:

| Documento | Rol |
|---|---|
| `docs/DEVELOPMENT-WORKFLOW.md` | Carta de navegación end-to-end (v2.0, dual-track). El mapa rápido. |
| `docs/WORKFLOW.md` | Manual del nivel módulo (Provider vs Feature, descomposición en HUs). |
| `docs/README.md` | Mapa de `docs/` + detalle paso a paso de cada skill. |
| `docs/QUALITY-GATES.md` | Thresholds numéricos que bloquean cada gate. |

**Nota de drift documental:** hay dos versiones del flujo conviviendo. `DEVELOPMENT-WORKFLOW.md` v2.0 describe un modelo dual-track:

```txt
Discovery: docs/02_discovery/
Delivery:  docs/03_delivery/hu/
```

Las skills realmente instaladas lo confirman (`feature-shaping`, `cerrar-sprint`). En cambio, `README.md` y `CLAUDE.md` aún describen el modelo anterior por feature:

```txt
docs/{AREA}/feature-{AREA}-{NN}/
```

Este informe refleja v2.0 como vigente y marca las diferencias donde importan.

> **Nota de mejora — prioridad alta**  
> El drift documental debería corregirse antes de escalar el flujo. En un sistema SDD, la documentación no es documentación secundaria: es parte del sistema operativo. Si existen dos modelos activos, cada agente, skill o desarrollador puede interpretar el proceso de forma distinta.
>
> Propuesta:
>
> ```txt
> docs/DEVELOPMENT-WORKFLOW.md → fuente de verdad principal
> docs/WORKFLOW.md             → detalle operativo alineado con v2.0
> docs/README.md               → índice y navegación, sin flujo alternativo
> CLAUDE.md                    → resumen operativo, sin duplicar versiones antiguas
> ```

---

## 1. Flujo de acciones

El flujo es **dual-track**: discovery (idea → feature shaped) y delivery (feature → HU → SDD por HU), más el cierre de sprint.

```txt
DISCOVERY (product-owner)
 idea (docs/02_discovery/ideas/NNN-slug.md)
 -> /feature-shaping -> feature shaped (FEAT-NN)
 -> priorización (prioritization.md)
 -> descomposición en Historias de Usuario (HU)

DELIVERY · SDD POR HU (docs/03_delivery/hu/HU-NN-slug/)
 1. /prd-writer -> specs/PRD.md (Ready, 0 Open Questions)
 2. /tech-design -> plans/TECHNICAL_DOC.md (0 Open Decisions)
 3. /task-planner -> tasks/TASK-NN.md + ROADMAP.md (<=15 tasks)
 4. implementación + tests (el dev escribe código)
 5. /reviewer -> review/REVIEW.md (VERDICT: ...)
 6. /module-sync -> docs/05_modules/{módulo}/ + STATUS + MVP-STATUS
 7. PR -> CI pr-quality-gate -> merge -> deploy

CIERRE (product-owner)
 /cerrar-sprint NN -> mueve idea/feature/HU entregadas a completadas/
```

Cada etapa tiene un **Definition of Done** y un **gate bloqueante**:

- El PRD no avanza con Open Questions abiertas.
- El `TECHNICAL_DOC` no cierra con Open Decisions.
- El reviewer bloquea el merge si emite `Requiere cambios`.

La unidad del flujo SDD es la **HU**, no la feature: specs, plans, tasks, código, review y sync corren dentro de la carpeta de cada HU.

> **Nota de mejora — muy buena decisión**  
> Que la unidad sea la HU es una de las mejores decisiones del flujo. Evita specs gigantes, reduce ambigüedad y permite revisar vertical slices más pequeños.
>
> **Riesgo:** si las HUs no están bien cortadas, el flujo se vuelve pesado igualmente. Conviene añadir un gate de shaping que valide que cada HU es entregable, testeable y revisable de forma independiente.

> **Nota de mejora — añadir loops explícitos**  
> El flujo actual se lee lineal. En la práctica, un fallo del reviewer puede venir de diferentes sitios: mala implementación, mala task, mal diseño técnico o mal scope de producto.
>
> Sería útil documentar este retorno:
>
> ```txt
> /reviewer
>   ├── si falla implementación → /improver
>   ├── si falla diseño         → vuelve a /tech-design
>   ├── si falla producto       → vuelve a /prd-writer
>   └── si falla scope          → vuelve a product-owner / feature-shaping
> ```
>
> Esto evita que `/improver` se convierta en un parcheador de síntomas.

> **Nota de mejora — carriles por tipo de cambio**  
> El flujo completo es potente, pero puede ser excesivo para cambios pequeños. Se recomienda formalizar tres carriles:
>
> | Tipo de cambio | Flujo recomendado |
> |---|---|
> | Nuevo comportamiento, riesgo alto o cambio transversal | SDD completo |
> | Cambio pequeño, acotado y sin impacto arquitectónico | SDD light |
> | Incidencia urgente en producción | Hotfix bypass + post-mortem documental |
>
> El bypass ya existe parcialmente, pero debería estar documentado como camino oficial y no solo como excepción técnica del CI.

---

## 2. Flujo de comandos

Comandos en orden de ejecución. Todos invocan skills:

| Orden | Comando | Produce |
|---|---|---|
| Discovery | `/feature-shaping NNN` | `feature.md` shaped |
| Discovery | manual `product-owner` | priorización + HUs |
| 1 | `/prd-writer HU-NN` | `specs/PRD.md` |
| 2 | `/tech-design HU-NN` | `plans/TECHNICAL_DOC.md` |
| 3 | `/task-planner HU-NN` | `tasks/TASK-NN.md` + `ROADMAP.md` |
| 4 | implementación humana | código + tests |
| 5 | `/reviewer HU-NN` | `review/REVIEW.md` |
| 5b | `/improver HU-NN` opcional | `IMPROVE-NN.md` |
| 6 | `/module-sync HU-NN` | `CLAUDE.md` del módulo actualizado |
| Cierre | `/cerrar-sprint NN` | artefactos a `completadas/` |

En el modelo anterior (`README`) el paso 0 era:

```txt
/req-capture AREA "título"
```

Generaba:

```txt
reqs/INTAKE.md
```

Esa skill sigue instalada.

Gates humanos obligatorios, donde el skill se detiene y pide `aprobado`:

- `prd-writer`
- `tech-design`
- `task-planner`
- `module-sync`

Sin gate por diseño:

- `req-capture`, porque es captura.
- `reviewer`, porque ya es human-driven.

> **Nota de mejora — reducir cuello de botella humano**  
> Hay varios gates humanos. Esto da control, pero puede provocar bloqueo si todo requiere aprobación manual.
>
> Se recomienda distinguir:
>
> | Gate | Responsable sugerido | ¿Siempre humano? |
> |---|---|---|
> | PRD Ready | Product Owner / responsable funcional | Sí |
> | Technical Doc cerrado | Tech Lead / Architect | Sí en cambios relevantes |
> | Task Plan | Tech Lead o dev owner | Solo si hay riesgo o ambigüedad |
> | Module Sync | Module owner | Sí, pero puede ser revisión rápida |
> | Reviewer | CI + responsable humano | Bloqueante solo para P0/P1 |

> **Nota de mejora — definir SDD light**  
> Para cambios pequeños podría bastar con:
>
> ```txt
> mini-PRD → task-plan reducido → implementación → reviewer limitado → PR
> ```
>
> Esto mantendría disciplina sin convertir cada ajuste en una ceremonia completa.

---

## 3. Archivos `.md` en los que se apoya

### Canónicos vivos del backbone

Referenciados por skills/agentes en cada feature:

| Archivo | Función |
|---|---|
| `docs/ARCHITECTURE.md` | Backbone técnico, 11 principios invariantes PT1–PT11. Auto-cargado. |
| `docs/DECISIONS.md` | Bitácora de ADs. Auto-cargado. |
| `docs/QUALITY-GATES.md` | Thresholds cuantificados que enforcen los gates. |
| `docs/DEVELOPMENT-WORKFLOW.md` | Flujo end-to-end vigente. |
| `docs/WORKFLOW.md` | Flujo a nivel módulo. |
| `docs/README.md` | Mapa de documentación. |
| `docs/EVENT-CATALOG.md` | Catálogo del bus AD-23. Cross-check del `event-bus-auditor`. |
| `docs/RUNBOOK-INCIDENT.md` | Runbook de incidentes. |
| `docs/PLAN-ALIGNMENT-ENTERPRISE.md` | Alineamiento enterprise. |
| `docs/PRD.md` | PRD general/base. |

### Estado auto-mantenido por skills

Ubicación:

```txt
docs/state/
```

| Archivo | Función |
|---|---|
| `AD-ARCHITECTURE-MAP.md` | Matriz AD ↔ ARCHITECTURE ↔ código ↔ tests. Lo refresca `/reviewer`. |
| `QUALITY-GATES-COVERAGE.md` | Trazabilidad hallazgo × mecanismo. Lo actualiza `/reviewer` en cada review. |

### Plantillas

Ubicación:

```txt
docs/_templates/
```

Plantillas principales:

- `INTAKE`
- `PRD`
- `TECHNICAL_DOC`
- `TASK`
- `ROADMAP`
- `CHANGELOG`
- `REVIEW`
- `MODULE_CLAUDE`
- `HU_MASTER`
- `SPRINT`

### Por feature/HU

Secuencia documental:

```txt
INTAKE.md / feature.md
 -> PRD.md
 -> TECHNICAL_DOC.md
 -> TASK-NN.md + ROADMAP.md
 -> REVIEW.md
 -> CLAUDE.md del módulo
```

### Contexto de área

Cada archivo:

```txt
docs/{AREA}/CLAUDE.md
```

se auto-actualiza vía:

```txt
/module-sync
```

El archivo:

```txt
docs/_modules.md
```

funciona como índice maestro, con una línea por área.

> **Nota de mejora — separar documentación normativa de documentación generada**  
> Conviene diferenciar claramente:
>
> - Documentos normativos: arquitectura, workflow, quality gates, decisiones.
> - Documentos generados por HU: PRD, technical doc, tasks, review.
> - Documentos de estado: mapas, coverage, status, MVP status.
>
> Esto reduce confusión sobre qué puede tocar un agente y qué requiere revisión humana.

> **Nota de mejora — ownership documental**  
> Añadir una tabla de ownership ayudaría:
>
> | Documento | Owner | Quién puede modificarlo | Revisión requerida |
> |---|---|---|---|
> | `ARCHITECTURE.md` | System/Tech Architect | humano + agente asistido | Sí |
> | `DECISIONS.md` | Tech Lead / Architect | humano | Sí |
> | `QUALITY-GATES.md` | Tech Lead + QA | humano | Sí |
> | `PRD.md` por HU | Product Owner | skill + PO | Sí |
> | `TECHNICAL_DOC.md` | Architect | skill + architect | Sí |
> | `REVIEW.md` | Reviewer | skill | No, salvo disputa |

---

## 4. Skills que intervienen

Instaladas en:

```txt
.claude/skills/
```

Todas usan modelo `sonnet`.

| Skill | Rol | Gate humano |
|---|---|---|
| `feature-shaping` | Idea → feature shaped. Delega en `feature-analyst`. | Sí |
| `prd-writer` | PRD curado, resuelve Open Questions, 5 gates: paths, RNF numéricos, ADs, >=3 edge cases/RF Must. | Sí, antes de Ready |
| `tech-design` | Orquestador. Despacha a los architects en paralelo y valida secciones obligatorias del `TECHNICAL_DOC`. | Sí, antes de cerrar |
| `task-planner` | Descompone PLANS en tasks atómicas: <=15, <=4h, vertical slices, task adversarial por RF Must. | Sí, antes de persistir |
| `reviewer` | Auditoría final. Lanza auditores en paralelo real y emite `VERDICT:` parseable. | No, human-driven |
| `module-sync` + `improver` | Sincroniza el `CLAUDE.md` del módulo con lo entregado. | Sí, antes de aplicar el diff |
| `req-capture` | Captura cruda → `INTAKE.md`. Modelo previo. | No |
| `cerrar-sprint` | Cierra el sprint y mueve los 3 niveles a `completadas/`. | — |

> **Nota de mejora — explicitar cuándo usar `req-capture`**  
> Como `req-capture` pertenece al modelo previo pero sigue instalado, conviene documentar si está:
>
> - deprecated,
> - permitido solo para intake rápido,
> - sustituido por `feature-shaping`,
> - o mantenido como entrada alternativa.
>
> Si no se aclara, puede reintroducir el flujo antiguo de forma accidental.

> **Nota de mejora — separar skill de responsabilidad**  
> Una skill ejecuta una parte del proceso, pero no debería confundirse con el responsable final. Por ejemplo, `prd-writer` puede generar el PRD, pero el owner del scope debería seguir siendo producto.

---

## 5. Agentes que intervienen

Ubicación:

```txt
.claude/agents/
```

Hay dos familias.

### 5.1. Orquestación / arquitectura

Modelo: `opus`.

| Agente | Rol |
|---|---|
| `product-owner` | Conduce discovery, priorización, descomposición en HU, sprints y cierre. No escribe código. |
| `feature-analyst` | Análisis funcional sin asunciones en el shaping. Auto desde `/feature-shaping`. |
| `backend-architect` | Diseño backend NestJS. Auto desde `/tech-design`, scope backend/fullstack. |
| `frontend-architect` | Diseño SPAs React/Next + widget. Auto desde `/tech-design`, scope frontend/fullstack. |
| `system-architect` | Features transversales SYSTEM: runtime, infra, agentic. Invocación manual. |
| `ai-engineer` | Features LLM/RAG/agente. Auto-invocado por `/tech-design` si detecta keywords. Aporta la sección `## AI Engineering Review`. |

### 5.2. Subagentes auditores P0

Auto desde:

```txt
/reviewer
```

Ejecución en paralelo real, read-only.

| Auditor | Revisa |
|---|---|
| `multitenant-auditor` | Triple red de aislamiento PT1: queries sin `{tenantId}`, jobs Bull, claves Redis, bus, idempotencia, JWT End User HMAC AD-24, M2M AD-25. |
| `llm-gateway-auditor` | PT7 zero-retention, AD-11 Bedrock-only, AD-03 metadata-only, AD-04 meter, AD-26 drenaje. |
| `prompt-versioning-auditor` | Prompts hardcoded fuera de `core/prompts/` + `PromptProvider`, modo transitorio hasta LLM-02. |
| `event-bus-auditor` | Disciplina del bus AD-23, cross-check contra `EVENT-CATALOG.md`. |
| `doc-code-drift-checker` | Paths citados que no existen, drift docs ↔ código. También gate de `/prd-writer`. |
| `security-auditor` | OWASP Web Top 10 + LLM Top 10 a nivel aplicativo. Siempre activo. |

### 5.3. P1 diferidos

- `legacy-cleanup-auditor`
- `finops-auditor`

Los auditores hacen un pre-flight check leyendo:

```txt
docs/state/AD-ARCHITECTURE-MAP.md
```

Concretamente la sección:

```txt
Drift conocido
```

Así pueden marcar hallazgos ya conocidos como `drift-confirmado` y evitar ruido.

> **Nota de mejora — subir FinOps antes**  
> En un producto con LLMs, generación de artefactos y pipelines agentic, `finops-auditor` no debería quedar demasiado tiempo como P1 diferido.
>
> No tiene por qué bloquear todos los PRs desde el principio, pero sí debería revisar:
>
> - coste estimado por ejecución,
> - coste por tenant,
> - número de llamadas LLM,
> - fan-out de agentes,
> - retries,
> - consumo por plan,
> - overage,
> - límites de seguridad por tenant,
> - trazabilidad de tokens/coste.
>
> En IA generativa, el coste no es solo infraestructura: es parte del diseño de producto.

> **Nota de mejora — añadir evaluación específica de outputs IA**  
> Los auditores técnicos están muy bien, pero las features LLM/RAG/agénticas necesitan gates propios:
>
> - golden dataset,
> - expected outputs,
> - evaluación de alucinaciones,
> - regresión de prompts,
> - coste por generación,
> - latencia por step,
> - validación humana muestral,
> - safety checks,
> - trazabilidad input → spec → output.
>
> El coverage de código no garantiza que un agente genere buenos artefactos.

> **Nota de mejora — riesgo del reviewer en CI**  
> Que el CI invoque un reviewer headless es potente, pero puede introducir coste, latencia y falsos positivos.
>
> Recomendación:
>
> ```txt
> P0/P1 crítico       → bloquea merge
> Hallazgo menor     → crea tarea o comentario, no bloquea
> Fallo técnico IA   → no bloquea automáticamente salvo ramas críticas
> Resultado dudoso   → requiere revisión humana
> ```

---

## 6. Otros elementos relevantes del flujo

### 6.1. Hooks Claude Code

Configurados en:

```txt
.claude/settings.json
```

Ejecutados por el harness, no por Claude.

| Hook | Trigger | Acción |
|---|---|---|
| `sensitive-files.sh` | `PreToolUse Edit/Write` | Bloquea `.env*`, `*.pem`, `*.key`, lockfiles. |
| `no-determinism.sh` | `PreToolUse Edit/Write` | Bloquea `Math.random()`, `Date.now()`, `crypto.randomUUID()` en workflows durables PT9. |
| `typecheck-precommit.sh` | `PreToolUse Bash (git commit)` | `tsc --noEmit` del workspace tocado. |
| `format-lint.sh` | `PostToolUse Edit/Write` | `prettier` + `eslint --fix` sobre el archivo. |

### 6.2. ESLint custom plugin

Ubicación:

```txt
nestjs-app/eslint-rules/
```

Incluye 8 reglas:

- 3 multitenant.
- 4 hexagonal.
- 1 no-determinism.

Enforza la triple red de aislamiento y las reglas hexagonales en CI.

### 6.3. Enforcement en CI

Pipeline:

```txt
pr-quality-gate
```

En Bitbucket Pipelines.

Incluye:

#### `check-prd-required.sh`

Exige PRD Ready cuyo módulo coincida con los paths tocados.

Permite bypass:

```txt
@hotfix-bypass: <razón >=20 chars>
```

El bypass queda logueado en:

```txt
docs/hotfix-bypasses.log
```

#### `run-reviewer.sh`

Invoca el skill `reviewer` headless vía Claude API, parsea `VERDICT:` y bloquea el merge si es:

```txt
Requiere cambios
```

### 6.4. Quality gates cuantificados

Los enforcen skills + auditores:

| Gate | Threshold |
|---|---|
| Coverage core | >=80% |
| Coverage products | >=60% |
| Archivo | <=300 LOC |
| Función | <=50 LOC |
| Ciclomática | <=10 |
| P95 lectura | <500ms |
| P95 ejecución | <2s |
| Overhead LLM | <100ms |
| Edge cases | >=3 edge cases por RF Must evaluando las 9 categorías |
| Cross-tenant | Test obligatorio por módulo |
| Edge case Must | Cada uno con test asociado, gate crítico |

### 6.5. Memoria persistente Engram

Los skills guardan decisiones/gotchas con `topic_keys` predecibles:

```txt
sdd/{AREA}-{NN}/prd
sdd/{AREA}-{NN}/tech-design
sdd/{AREA}-{NN}/review
docs/{AREA}/module-state
```

Engram es opcional. Sin Engram, los documentos siguen siendo la fuente de verdad.

### 6.6. Optimización de contexto

Los skills delegan el escaneo de código a sub-agentes Explore, con contexto separado.

Los architects llevan las constraints del proyecto cargadas en su system prompt, en vez de releerlas continuamente.

> **Nota de mejora — observabilidad post-release**  
> El flujo llega hasta PR, CI, merge y deploy, pero conviene explicitar el tramo posterior:
>
> ```txt
> deploy → smoke test → observability → métricas → rollback plan → post-release validation
> ```
>
> En pipelines IA, pasar CI no garantiza que el output sea bueno para el usuario.

> **Nota de mejora — feature flags y rollback**  
> Para features agentic o de generación de artefactos, se recomienda exigir:
>
> - feature flag,
> - plan de rollback,
> - métrica de activación,
> - métrica de error funcional,
> - métrica de coste,
> - trazas por tenant,
> - checklist de degradación controlada.

> **Nota de mejora — hotfix con deuda controlada**  
> El bypass está bien, pero debería exigir una tarea posterior:
>
> ```txt
> hotfix aplicado
>   -> registro en hotfix-bypasses.log
>   -> issue de normalización documental
>   -> reviewer diferido
>   -> cierre del bypass
> ```
>
> Sin eso, el bypass puede convertirse en una puerta trasera permanente.

---

## 7. Reglas de oro siempre activas

1. **Multitenancy fail-closed (PT1).** Toda query/job/log/traza lleva `{tenantId}`. Sin contexto → 403.
2. **Zero-retention LLM (PT7).** Ninguna llamada a Bedrock fuera de `core/llm/`.
3. **Prompts versionados.** Cero string literals tipo prompt en código TS; todo vive en `core/prompts/` vía `PromptProvider`.
4. **Workflows deterministas (PT9).** Prohibido `Math.random()`, `Date.now()` y `new Date()` en `core/execution/workflows/**`.
5. **AD-MAP siempre actualizado.** Cerrar una AD → actualizar `docs/state/AD-ARCHITECTURE-MAP.md` en el mismo PR.
6. **Audit WORM 5 años, metadata-only para LLM (AD-03).**
7. **Bus AD-23.** In-process síncrono `EventEmitter2`; cross-module asincrónico `SQS` + `EventBridge`. Todo evento con `tenantId` + `eventId` UUID v4 y handlers idempotentes.
8. **Cada edge case Must tiene test.** Sin test asociado, `/reviewer` emite `Requiere cambios`.
9. **Idioma.** Docs en castellano peninsular; código, identificadores y commits en inglés.

> **Nota de mejora — añadir regla de coste IA**  
> Se recomienda añadir una décima regla de oro:
>
> **Cost awareness by design.** Toda feature LLM/agentic debe declarar coste estimado, límites por tenant y estrategia de control de retries/fan-out.

> **Nota de mejora — añadir regla de evaluabilidad IA**  
> También podría añadirse:
>
> **AI outputs must be evaluable.** Todo artefacto generado por IA debe tener criterios de validación explícitos: estructura esperada, checks automáticos, revisión humana cuando aplique y trazabilidad desde la specification.

---

## 8. Resumen de mejoras propuestas

| Área | Mejora | Prioridad |
|---|---|---|
| Drift documental | Alinear `DEVELOPMENT-WORKFLOW.md`, `WORKFLOW.md`, `README.md` y `CLAUDE.md` con v2.0 | Alta |
| Flujo | Añadir loops explícitos desde reviewer hacia implementación, tech-design, PRD o shaping | Alta |
| Proceso | Crear carriles: SDD completo, SDD light y hotfix | Alta |
| Gates humanos | Definir qué gates requieren aprobación humana real y cuáles pueden ser delegados | Media/Alta |
| CI reviewer | Bloquear solo P0/P1 críticos; findings menores no deberían bloquear siempre | Media/Alta |
| FinOps | Subir `finops-auditor` antes para features LLM/agentic | Alta |
| IA | Añadir evaluación específica de outputs: golden datasets, prompt regression, hallucination checks | Alta |
| Release | Añadir feature flags, rollback, smoke tests y post-release validation | Media |
| Ownership | Añadir RACI/owners por documento, decisión y gate | Media |
| Hotfix | Exigir normalización posterior del bypass | Media |

---

## 9. Veredicto

El flujo actual es una base fuerte para un producto con IA, multitenancy, generación de artefactos y pipelines agentic.

Sus principales virtudes son:

- trabaja por HU,
- separa discovery y delivery,
- usa gates cuantificados,
- tiene auditores especializados,
- conecta documentación, CI y revisión,
- protege riesgos críticos como multitenancy, seguridad, LLM gateway y drift docs-código.

El mayor riesgo no es técnico, sino operativo: que el flujo se vuelva demasiado pesado o que el drift documental genere dos formas distintas de trabajar.

La recomendación principal es mantener el modelo, pero modularizarlo por carriles y reforzar las partes específicas de IA, coste, release y ownership humano.

En resumen:

> El flujo es bueno. No necesita ser sustituido. Necesita ser afinado para que no se convierta en burocracia y para que cubra mejor los riesgos propios de IA generativa en producción.
