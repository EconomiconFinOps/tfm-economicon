# Plan de adaptacion HU con OpenSpec y Engram

## Objetivo

Adaptar el flujo de trabajo del proyecto para que sea mas robusto que el uso basico de OpenSpec, sin recrear un harness SDD pesado.

El flujo debe mantener la filosofia de OpenSpec:

- cambios pequenos y trazables,
- artefactos minimos pero suficientes,
- validacion antes de implementar,
- tareas ejecutables,
- archivo/sync al terminar,
- memoria auxiliar con Engram, sin convertirla en fuente de verdad.

La unidad operativa sera la HU, modelada como un `OpenSpec change`.

```txt
HU -> OpenSpec change
PRD + TD -> proposal/design/specs
TASKs -> tasks.md
HiTL -> aprobacion humana explicita
Execution -> apply
Review -> revision tecnica/funcional
HiTL -> aprobacion humana final antes de cerrar
```

## Principios obligatorios

1. **OpenSpec es la fuente operativa del flujo.** No se reintroducen `.sdd`, `packages/sdd-harness`, `SPEC` ni comandos del harness anterior.
2. **La HU vive como cambio de OpenSpec.** El nombre del change debe mapearse de forma clara a una HU: `hu-001-import-invoices`, `hu-002-tenant-dashboard`, etc.
3. **Review humano antes de codigo.** Nadie cambia codigo hasta que una persona apruebe PRD + TD + TASKs.
4. **Review humano despues de la review.** Tras implementar y revisar, una persona debe aprobar el resultado antes de archivar/cerrar.
5. **Documentacion primero, documentacion sincronizada.** Si cambia el comportamiento, debe cambiar el artefacto OpenSpec correspondiente.
6. **Ligero por defecto.** Solo se anade mas ceremonia si el cambio tiene riesgo, impacto transversal, IA, datos, seguridad, multi-tenant o coste relevante.
7. **Engram es memoria auxiliar.** Puede guardar decisiones, gotchas y contexto, pero los documentos versionados mandan.
8. **Las decisiones de arquitectura duraderas usan ADRs.** `design.md` captura decisiones locales de la HU; `docs/adr/` captura decisiones transversales o persistentes.

## Flujo objetivo

### 1. HU intake

Objetivo: convertir una necesidad en una HU pequena, entregable y testeable.

Entrada minima:

- titulo corto,
- problema,
- usuario o actor,
- resultado esperado,
- restricciones conocidas,
- riesgo percibido.

Salida esperada:

- nombre del change OpenSpec,
- alcance inicial,
- carril elegido: `light`, `standard` o `hotfix`.

Comando recomendado:

```powershell
pnpm openspec:list
pnpm openspec:init
```

Para crear la HU/change se usara el flujo de OpenSpec desde Codex o Claude:

```txt
/opsx:propose "descripcion de la HU"
```

Convencion de nombre:

```txt
hu-NNN-slug-corto
```

Ejemplo:

```txt
hu-001-upload-invoices
```

### 2. PRD + TD

Objetivo: dejar claro que se va a construir y como se va a integrar.

En OpenSpec esto debe quedar repartido en los artefactos generados por el change:

- `proposal.md`: que y por que.
- `design.md`: decisiones tecnicas relevantes.
- `specs/*/spec.md`: requisitos observables.
- `tasks.md`: plan ejecutable.

Si la HU introduce o cambia una decision de arquitectura duradera, `design.md` debe enlazar el ADR correspondiente en `docs/adr/`.

Checklist minimo del PRD:

- problema y objetivo,
- usuario/actor,
- comportamiento esperado,
- fuera de scope,
- criterios de aceptacion,
- edge cases relevantes,
- preguntas abiertas resueltas o explicitamente diferidas.

Checklist minimo del TD:

- componentes afectados,
- flujo de datos,
- contratos/API si aplica,
- persistencia si aplica,
- seguridad/permisos si aplica,
- impacto multi-tenant si aplica,
- impacto IA/coste si aplica,
- estrategia de pruebas.

Regla anti-drift:

- Si una decision tecnica cambia durante implementacion, se actualiza `design.md`.
- Si esa decision es duradera o transversal, se crea o actualiza un ADR.
- Si un requisito cambia, se actualiza `specs/*/spec.md`.
- Si una tarea deja de aplicar o aparece una nueva, se actualiza `tasks.md`.

### 3. TASKs

Objetivo: tener una lista pequena de pasos implementables.

Reglas:

- Cada task debe ser verificable.
- Cada task debe poder marcarse como hecha en `tasks.md`.
- Evitar tasks ambiguas como "mejorar backend".
- Preferir vertical slices pequenas.
- Para flujo `light`, mantener entre 1 y 5 tasks.
- Para flujo `standard`, mantener idealmente menos de 10 tasks.
- Si supera 10 tasks o toca muchas areas, dividir la HU.

Formato recomendado:

```md
- [ ] Implementar endpoint X con validacion Y.
- [ ] Anadir test de caso feliz y caso de error.
- [ ] Actualizar UI para consumir X.
- [ ] Validar OpenSpec y ejecutar test/lint/build.
```

### 4. HiTL pre-codigo

Objetivo: bloquear cambios de codigo hasta que una persona apruebe la HU.

La aprobacion humana debe confirmar:

- PRD entendible y sin preguntas abiertas criticas.
- TD suficiente para implementar sin decisiones ocultas.
- ADR creado/enlazado o declarado no aplicable cuando hay decisiones arquitectonicas.
- TASKs pequenas y ejecutables.
- Riesgos principales identificados.
- Carril correcto: `light`, `standard` o `hotfix`.

Registro de aprobacion:

- Debe quedar escrito en el change de OpenSpec, preferiblemente en `proposal.md` o `design.md`.
- Formato recomendado:

```md
## Human Approval

- Change: <change-name>
- Approval type: pre-code
- Decision: approved
- Approver: <approver>
- Date: <YYYY-MM-DD>
- Carril: light | standard | hotfix
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Main risks: <risks or "none identified">
- Required changes before execution: <items or "none">
- Notes: <optional>
```

Sin esta seccion aprobada, no se debe pasar a `apply`.

El bloque estructurado con `Approval type` y `Decision` es el unico formato valido de HiTL. El harness bloquea cualquier wording legacy de aprobacion.

Antes de ejecutar cambios de producto, validar el gate pre-code:

```powershell
pnpm hu:check:pre-code -- --change <change-name>
```

### 5. Execution

Objetivo: implementar solo lo aprobado.

Comando/flujo:

```txt
/opsx:apply <change-name>
```

Reglas:

- Implementar task por task.
- Marcar cada task completada en `tasks.md`.
- Mantener cambios pequenos y enfocados.
- Si aparece una decision nueva, parar y actualizar PRD/TD/TASKs antes de seguir.
- Si aparece una decision arquitectonica duradera, actualizar `design.md` y crear/enlazar ADR antes de seguir.
- No usar Engram como sustituto de actualizar los documentos.

Checks minimos antes de pedir review:

```powershell
pnpm openspec:validate
pnpm test
pnpm lint
pnpm build
```

Si algun check no existe o falla por configuracion previa del repo, debe documentarse en la review con el motivo.

### 6. Review

Objetivo: revisar que la implementacion cumple la HU y no introduce drift.

Checklist de review:

- El codigo implementa los criterios de aceptacion.
- Todas las tasks aplicables estan marcadas.
- Los tests cubren los casos esperados.
- `proposal.md`, `design.md`, `specs` y `tasks.md` siguen reflejando la realidad.
- Las decisiones de arquitectura estan en ADR o se marco ADR como no aplicable.
- No se introducen restos del harness SDD viejo.
- No se ha usado `npm i`.
- Engram no contiene informacion que deba estar versionada, incluyendo decisiones de arquitectura aceptadas.

Checks recomendados:

```powershell
pnpm install --frozen-lockfile
pnpm openspec:validate
pnpm test
pnpm lint
pnpm build
pnpm hu:check:approval-format
pnpm hu:check -- --change <change-name>
rg -n "sdd-harness|\\.sdd|Spec-Driven|validate-manifest|codex-smoke" .
```

Para cambios con IA, coste, seguridad o multi-tenant, anadir review especifica:

- coste estimado,
- limites por tenant,
- permisos,
- trazabilidad,
- dataset o casos de evaluacion,
- rollback o degradacion.

### Findings trackeables

El `review.md` de cada HU es el registro historico de lo que se encontro durante esa revision. Para seguimiento operativo, los findings abiertos, diferidos o aceptados como riesgo deben registrarse tambien en:

```txt
openspec/findings/backlog.md
```

Regla de uso:

- Todo finding debe aparecer primero en el `review.md` de la HU donde se detecta.
- Todo finding `Out of scope` debe anadirse al backlog central antes del HiTL final.
- Todo finding sin resolver o diferido debe anadirse al backlog central antes del HiTL final.
- Todo finding `In scope` bloquea el cierre salvo que se corrija o una persona lo acepte explicitamente.
- Si un finding se convierte en una HU, se actualiza `Change/Fix` con el nombre del change.
- Si una HU corrige un finding existente, actualiza su `Estado` en el backlog.
- Los findings cerrados no se borran; quedan como historial.

Formato de ID:

```txt
RF-<hu-number>-<sequence>
```

Ejemplo:

```txt
RF-004-001
```

Estados permitidos:

```txt
Open
Planned
In progress
Fixed
Accepted risk
Won't fix
```

Un finding fuera de scope no bloquea la HU si:

- esta documentado en `review.md`,
- esta anadido a `openspec/findings/backlog.md`,
- tiene accion definida,
- el humano acepta diferirlo en el HiTL final.

### Harness ligero pre-archive

Antes de archivar una HU se debe ejecutar el harness local:

```powershell
pnpm hu:check -- --change <change-name>
```

Este comando valida estructura de OpenSpec, aprobaciones HiTL, tasks cerradas, findings enlazados al backlog, `pnpm openspec:validate` y guardrails anti-harness. No ejecuta tests, lint ni build de producto; esos checks siguen siendo parte de la review y deben documentarse ahi.

Checks auxiliares:

```powershell
pnpm hu:check:approval-format
pnpm hu:check:findings
pnpm hu:check:anti-harness
```

### 7. HiTL post-review

Objetivo: cerrar solo cuando una persona acepte el resultado revisado.

La aprobacion humana final debe confirmar:

- implementacion aceptada,
- review aceptada,
- checks ejecutados o excepciones documentadas,
- documentacion sincronizada,
- decision de archivar o dejar abierto.

Registro recomendado:

```md
## Human Approval

- Change: <change-name>
- Approval type: post-review
- Decision: approved
- Approver: <approver>
- Date: <YYYY-MM-DD>
- Review accepted: yes
- Checks accepted: yes
- Documentation synchronized: yes
- Archive decision: archive
- Notes: <optional>
```

Tras esta aprobacion:

```txt
/opsx:sync
/opsx:archive <change-name>
```

## Carriles ligeros

### Light

Uso:

- bug pequeno,
- ajuste UI pequeno,
- cambio acotado sin impacto arquitectonico,
- refactor local.

Artefactos minimos:

- proposal breve,
- design breve si hay decision tecnica,
- ADR solo si hay decision de arquitectura duradera o transversal,
- tasks de 1 a 5 items,
- HiTL pre-codigo,
- execution,
- review,
- HiTL final.

### Standard

Uso:

- nuevo comportamiento,
- cambio con backend + frontend,
- cambio de datos,
- integracion externa,
- impacto en seguridad/permisos.

Artefactos:

- PRD completo en proposal/spec,
- TD en design,
- tasks verificables,
- checks completos,
- review documentada.

### Hotfix

Uso:

- incidencia urgente,
- produccion bloqueada,
- correccion de seguridad urgente.

Reglas:

- Puede reducir PRD/TD antes de codigo, pero no eliminarlos por completo.
- Debe existir aprobacion humana pre-codigo.
- Debe existir normalizacion posterior.
- La deuda documental se cierra antes de archivar.

Registro minimo:

```md
## Hotfix Justification

- Reason:
- Risk:
- Approver:
- Follow-up normalization task:
```

## Lecciones de HU-001

HU-001 (`hu-001-formalize-openspec-hu-workflow`) valido el flujo completo con una HU documental. Estas son las reglas practicas que quedan fijadas para las siguientes HUs:

- OpenSpec `spec-driven` necesita `proposal.md`, `design.md`, `specs/**/*.md` y `tasks.md` incluso en cambios documentales.
- En cambios doc-only o de proceso, crear una spec minima de proceso si OpenSpec la exige, pero no inventar una capability de producto.
- Para cambios doc-only, archivar con:

```powershell
pnpm openspec archive <change-name> --skip-specs
```

- Despues de archivar, `pnpm openspec:validate` puede devolver `No items found to validate`; eso es correcto si no quedan cambios activos.
- La busqueda textual anti-harness puede encontrar menciones documentales intencionales. Esas menciones no son fallo por si solas.
- Los checks que bloquean reintroduccion del harness viejo deben ser estructurales: existencia de rutas y archivos versionados.

## Guardrails anti-drift documental

Para evitar que la documentacion lleve a fallos:

1. Todo cambio de comportamiento debe tener cambio OpenSpec asociado.
2. Todo cambio de decision debe reflejarse en `design.md`.
3. Toda decision de arquitectura duradera debe reflejarse en `docs/adr/`.
4. Todo cambio de requisito debe reflejarse en `specs`.
5. Toda task completada debe marcarse en `tasks.md`.
6. Todo bypass/hotfix debe tener normalizacion posterior.
7. Engram puede recordar contexto, pero la verdad final vive en Git.
8. Antes de archivar se ejecuta `pnpm openspec:validate`.
9. Antes de cerrar se revisa que no haya drift entre codigo, specs y tasks.

## Checks anti-harness

La busqueda textual se mantiene como senal informativa:

```powershell
rg -n "sdd-harness|\\.sdd|Spec-Driven|validate-manifest|codex-smoke" .
```

Si devuelve solo referencias documentales que explican guardrails, no bloquea.

Los checks estructurales son los que deben bloquear:

```powershell
Test-Path .sdd
Test-Path packages\sdd-harness
Test-Path SPEC
git ls-files | rg "(^\.sdd/|^packages/sdd-harness/|^SPEC/)"
```

Resultado esperado:

- Los tres `Test-Path` devuelven `False`.
- `git ls-files | rg ...` no devuelve coincidencias.

## Uso de Engram

Engram se usa para memoria local del proyecto `tfm-economicon`.

Comandos:

```powershell
pnpm engram:doctor
pnpm engram:context
pnpm engram:mcp
```

Guardar en Engram:

- decisiones recurrentes,
- gotchas,
- convenciones descubiertas,
- motivos de tradeoffs,
- contexto util para futuras sesiones.

No guardar solo en Engram:

- requisitos,
- decisiones finales,
- decisiones de arquitectura aceptadas,
- aprobaciones humanas,
- criterios de aceptacion,
- resultados de review.

Eso debe vivir en OpenSpec y Git.

## Plantillas reutilizables

Las plantillas canonicas para copiar en cada HU viven en:

```txt
docs/templates/hu/
```

Plantillas disponibles:

- `pre-code-approval.md`: aprobacion humana antes de cambiar codigo o documentacion ejecutable.
- `review.md`: estructura de review tecnica/funcional.
- `post-review-approval.md`: aprobacion humana final antes de sync/archive.
- `hotfix-justification.md`: justificacion y normalizacion posterior para hotfix.
- `hu-checklist.md`: checklist operacional completo por HU.
- `../adr.md`: plantilla para decisiones de arquitectura duraderas.

Las plantillas son documentacion versionada. No son enforcement automatico ni sustituyen OpenSpec.

## Checklist operacional por HU

Usar esta lista para no saltarse pasos:

```md
## HU Checklist

- [ ] Crear OpenSpec change con nombre `hu-NNN-slug`.
- [ ] Completar PRD/proposal.
- [ ] Completar TD/design.
- [ ] Completar specs si aplica.
- [ ] Completar tasks verificables.
- [ ] Evaluar si la HU necesita ADR; crearlo/enlazarlo o marcar ADR no aplicable.
- [ ] Registrar HiTL pre-codigo.
- [ ] Ejecutar `pnpm openspec:validate`.
- [ ] Ejecutar `pnpm hu:check:pre-code -- --change <change-name>` antes de tocar codigo de producto.
- [ ] Implementar con `/opsx:apply`.
- [ ] Marcar tasks completadas.
- [ ] Ejecutar checks: install, validate, test, lint, build, o checks enfocados aceptados para el carril elegido.
- [ ] Registrar comandos exactos de validacion y cualquier setup de entorno usado para ejecutarlos.
- [ ] Revisar drift docs/codigo.
- [ ] Ejecutar checks estructurales anti-harness.
- [ ] Interpretar `rg` anti-harness como informativo si solo hay referencias documentales.
- [ ] Registrar review.
- [ ] Registrar `ADR creado/actualizado` o `ADR no aplicable` en review.
- [ ] Registrar findings en `review.md`.
- [ ] Anadir al backlog central cualquier finding fuera de scope, no resuelto o diferido.
- [ ] Enlazar cada finding del backlog con su HU origen.
- [ ] Si esta HU corrige un finding existente, actualizar su estado en `openspec/findings/backlog.md`.
- [ ] Ejecutar `pnpm hu:check:findings` si cambia el backlog de findings.
- [ ] Confirmar que no quedan findings sin decision antes del HiTL final.
- [ ] Registrar HiTL post-review.
- [ ] Ejecutar `pnpm hu:check:approval-format`.
- [ ] Ejecutar `pnpm hu:check -- --change <change-name>` antes de archivar.
- [ ] Ejecutar sync si aplica.
- [ ] Archivar change; usar `--skip-specs` si es doc-only/proceso.
```

## Proximos pasos para adoptar este plan

1. Crear una HU piloto pequena y ejecutarla con este flujo.
2. Ajustar el checklist segun fricciones reales.
3. Documentar una plantilla de aprobacion humana si se repite mucho.
4. Evaluar si hacen falta skills propias solo despues de 2 o 3 HUs reales.
5. Evitar crear agentes/auditores hasta que existan patrones claros que lo justifiquen.
