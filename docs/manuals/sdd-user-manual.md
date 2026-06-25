# Manual ligero del harness HU/OpenSpec

## 1. Que es este harness

En este repo, el harness sirve para implementar HUs y tasks sin perder trazabilidad.

Aunque el archivo se llame `sdd-user-manual.md`, el flujo actual no usa el harness SDD viejo. El flujo oficial es:

```txt
HU -> OpenSpec change -> tasks -> implementacion -> review -> aprobacion -> archive
```

El harness combina tres piezas:

- **OpenSpec**: guarda la HU, requisitos, diseno, specs, tasks y archivo historico.
- **Checks locales HU**: validan que no nos saltamos aprobaciones, review, findings o guardrails.
- **Engram**: memoria auxiliar local para recordar contexto operativo, nunca fuente de verdad.

La regla corta:

```txt
OpenSpec/Git decide. Engram recuerda.
```

## 2. Para que usamos OpenSpec

OpenSpec es la fuente de verdad del trabajo de cada HU.

Cada HU vive como un change en:

```txt
openspec/changes/<change-name>/
```

Un change normalmente contiene:

- `proposal.md`: que se quiere hacer y por que.
- `design.md`: como se va a hacer y decisiones tecnicas.
- `specs/*/spec.md`: requisitos observables.
- `tasks.md`: lista de tareas ejecutables.
- `review.md`: resultado de la revision, checks y findings.

Cuando una HU se termina y se archiva, queda como historico en:

```txt
openspec/changes/archive/
```

## 3. Para que usamos Engram

Engram se usa como memoria local del proyecto.

Sirve para guardar:

- gotchas del repo
- problemas de entorno
- comandos que funcionaron
- decisiones recurrentes
- contexto util para futuras sesiones
- notas operativas que ayudan tras cambiar de agente o despues de una compactacion

No debe ser el unico sitio donde vive:

- un requisito
- una aprobacion humana
- un criterio de aceptacion
- una decision final
- una decision de arquitectura aceptada
- un finding
- un resultado de review
- el estado real de una HU

Si algo afecta a una HU, debe reflejarse en OpenSpec o Git.

## 4. Carriles de trabajo

El harness puede usarse en carril ligero o pesado.

### Carril light

Usalo para cambios pequenos y claros:

- docs
- fixes simples
- cambios con poco riesgo
- HUs de 1 a 5 tasks
- cambios sin impacto transversal fuerte

En light se mantiene todo breve:

- proposal corto
- design corto
- spec minima si OpenSpec la requiere
- tasks pequenas
- checks enfocados
- review concreta

### Carril standard

Usalo para cambios mas pesados:

- cambios de producto con riesgo
- varias areas tocadas
- datos, seguridad, multi-tenant, costes o IA
- integraciones externas
- cambios que necesitan mas validacion

En standard se espera mas detalle:

- proposal con scope claro
- design mas completo
- specs cuidadas
- tasks verificables
- tests/lint/build cuando apliquen
- review mas estricta
- ADR si hay decision de arquitectura duradera

### Carril hotfix

Usalo solo para urgencias.

El hotfix permite reducir pasos antes de actuar, pero exige documentar despues:

- que se hizo
- por que no podia esperar
- que checks se ejecutaron
- que queda por normalizar

Usa la plantilla:

```txt
docs/templates/hu/hotfix-justification.md
```

## 5. Flujo ligero recomendado

Este es el flujo habitual para una HU pequena.

### 1. Ver cambios activos

```powershell
pnpm openspec:list
```

### 2. Crear o proponer la HU

Con agente:

```txt
/opsx:propose "descripcion corta de la HU"
```

O con CLI:

```powershell
pnpm exec openspec new change "hu-010-mi-cambio"
```

### 3. Completar artefactos

Rellena:

- `proposal.md`
- `design.md`
- `specs/*/spec.md`
- `tasks.md`

Para light, no escribas de mas. El objetivo es que otra persona o agente pueda implementar sin adivinar.

### 4. Revisar si hace falta ADR

Si la HU cambia arquitectura duradera, crea o enlaza un ADR:

```txt
docs/adr/ADR-0001-short-slug.md
```

Usa:

```txt
docs/templates/adr.md
```

Si no aplica, deja constancia en review:

```txt
ADR not applicable.
```

### 5. Registrar aprobacion pre-code

Antes de tocar codigo de producto o docs ejecutables, debe existir aprobacion humana estructurada:

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

### 6. Validar antes de implementar

```powershell
pnpm openspec:validate
pnpm hu:check:pre-code -- --change <change-name>
```

Si `hu:check:pre-code` falla, no empieces a tocar producto. Corrige los artefactos o documenta el bloqueo.

### 7. Implementar task por task

Con agente:

```txt
/opsx:apply <change-name>
```

O manualmente:

1. Lee `proposal.md`, `design.md`, specs y `tasks.md`.
2. Implementa una task.
3. Marca la task como completada en `tasks.md`.
4. Sigue con la siguiente.

No marques una task como hecha si no esta realmente hecha.

### 8. Ejecutar checks

Para light, usa checks enfocados y registra resultados.

Ejemplos:

```powershell
pnpm openspec:validate
pnpm hu:check:approval-format
pnpm hu:check:anti-harness
pnpm hu:check:findings
```

Si el cambio toca producto, anade los checks que apliquen:

```powershell
pnpm test
pnpm lint
pnpm build
```

Si un check no existe o falla por entorno previo, explicalo en `review.md`.

### 9. Registrar review

Crea o actualiza:

```txt
openspec/changes/<change-name>/review.md
```

La review debe decir:

- que se reviso
- si se acepta o no
- checks ejecutados
- findings encontrados
- si ADR aplica o no
- riesgos o follow-ups

Usa:

```txt
docs/templates/hu/review.md
```

### 10. Gestionar findings

Todo finding va primero en `review.md`.

Si el finding queda abierto, diferido, fuera de scope o aceptado como riesgo, tambien va en:

```txt
openspec/findings/backlog.md
```

Despues ejecuta:

```powershell
pnpm hu:check:findings
```

### 11. Registrar aprobacion post-review

Antes de archivar, hace falta aprobacion humana final:

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

### 12. Validar gate final y archivar

```powershell
pnpm hu:check -- --change <change-name>
```

Si pasa, se puede archivar:

```powershell
pnpm exec openspec archive <change-name>
```

Para cambios doc-only o proceso, puede aplicar:

```powershell
pnpm exec openspec archive <change-name> --skip-specs
```

## 6. Flujo pesado recomendado

El flujo pesado usa los mismos pasos, pero con mas rigor.

Usalo cuando el cambio:

- toca varias apps o paquetes
- cambia contratos entre frontend/backend/processor
- toca auth, permisos, datos, IA, costes o multi-tenant
- requiere migraciones o compatibilidad
- cambia arquitectura duradera

En carril standard:

1. El `proposal.md` debe dejar claro scope, non-goals y riesgos.
2. El `design.md` debe explicar decisiones, alternativas y trade-offs.
3. Las specs deben describir comportamiento observable.
4. `tasks.md` debe poder ejecutarse task por task.
5. Si aparece una decision de arquitectura duradera, crea o actualiza ADR.
6. Los checks deben cubrir producto, no solo harness.
7. La review debe ser mas estricta y registrar excepciones.
8. No se archiva hasta que `pnpm hu:check -- --change <change-name>` pase.

## 7. Comandos utiles

```powershell
pnpm openspec:list
pnpm openspec:validate
pnpm exec openspec status --change <change-name>
pnpm exec openspec instructions apply --change <change-name> --json
pnpm hu:check:pre-code -- --change <change-name>
pnpm hu:check:approval-format
pnpm hu:check:anti-harness
pnpm hu:check:findings
pnpm hu:check -- --change <change-name>
```

Usa `pnpm exec openspec ...` para llamadas directas de OpenSpec que no tengan script propio.

## 8. Reglas que no se negocian

- No tocar producto antes de que pase `pnpm hu:check:pre-code -- --change <change-name>`.
- No archivar antes de que pase `pnpm hu:check -- --change <change-name>`.
- No dejar aprobaciones solo en chat.
- No dejar decisiones finales solo en Engram.
- No dejar findings abiertos solo en la review si requieren backlog.
- No reintroducir el harness viejo.
- No crear ADRs para detalles locales pequenos.
- Si hay decision de arquitectura duradera, usar ADR.

## 9. Resumen rapido

Para una HU normal:

```txt
1. Crear OpenSpec change
2. Escribir proposal/design/specs/tasks
3. Revisar ADR si aplica
4. Registrar HiTL pre-code
5. Ejecutar hu:check:pre-code
6. Implementar tasks
7. Ejecutar checks
8. Registrar review y findings
9. Registrar HiTL post-review
10. Ejecutar hu:check final
11. Sync/archive
```

Si recuerdas una sola idea:

**OpenSpec guarda la verdad del cambio, el harness valida que no te saltes pasos y Engram solo ayuda a recordar contexto.**
