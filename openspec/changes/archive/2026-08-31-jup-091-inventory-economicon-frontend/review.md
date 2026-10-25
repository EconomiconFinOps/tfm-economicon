# Review: jup-091-inventory-economicon-frontend

## Result

Accepted

## Scope Reviewed

- `../Economicon/frontend` en solo lectura (snapshot: rama `main`, commit `1fe0030`, el mismo que
  inspeccionó JUP-083).
- `apps/frontend/src/services/api.js`, `apps/backend/app/api/routes/`,
  `apps/backend/app/schemas/billing.py` y `apps/backend/app/db/database.py`, como fuente de los
  contratos reales.
- `docs/spikes/frontend-migration.md` (tarjeta F1 marcada + matización del supuesto T5).
- `openspec/changes/jup-091-inventory-economicon-frontend/{proposal,design,specs,tasks}.md`.
- Entregable: `docs/planning/JUP-091-economicon-source-inventory.md`.

## Checklist

- [x] Las 61 dependencias declaradas del origen están clasificadas `MANTENER`/`SUSTITUIR`/`DESCARTAR` con motivo; la suma por etiqueta (11+2+48) cuadra con lo declarado.
- [x] Las 5 rutas están mapeadas y las 14 filas del mapeo llevan contrato, `PARCIAL` o `SIN EQUIVALENTE`.
- [x] El uso real se verificó leyendo el código, no solo el `package.json`.
- [x] Los huecos se agruparon por capacidad de backend ausente, no por pantalla.
- [x] El inventario anota el commit snapshot del origen y nada suyo se commiteó en este repo.
- [x] Checks del carril ejecutados y en verde (tarea 4.4).
- [x] Tasks.md marcado 12/12.

ADR no aplicable. Esta HU documenta el estado de un repositorio externo; no introduce ninguna
decisión de arquitectura duradera. La adopción de TypeScript, con su ADR, corresponde a la tarjeta
`jup-0xx-adr-adopcion-typescript` de F1.

## Validation

```txt
corepack pnpm openspec:validate -> PASS: 18 items validated strictly (3 specs, 15 changes)
corepack pnpm jup:check -- --change jup-091-inventory-economicon-frontend -> PASS: enlazado con Trello y completo
corepack pnpm jup:cleanup:check -> PASS: 341 archivos sin agentes personales, binarios ni tareas paralelas
test / lint / build -> N/A (doc-only, sin código de producto; harness TDD omitido: sin tester/coder/mutación)
```

Verificaciones propias del inventario, ejecutadas durante el apply:

```txt
Cobertura de dependencias -> PASS: 61/61 declaradas presentes, 0 sin clasificar; suma 11+2+48 = 61
Cobertura del mapeo       -> PASS: 5/5 rutas presentes, 14/14 filas con contrato, PARCIAL o SIN EQUIVALENTE
Deteccion de uso real     -> 13 dependencias sin un solo import; 38 alcanzadas solo por ui/ (codigo muerto)
```

## Review Findings

| ID | Tipo | Severidad | Scope | Descripcion | Accion | Backlog |
|----|------|-----------|-------|-------------|--------|---------|
| RF-091-001 | Documentation accuracy | Low | Out of scope | El supuesto T5 de JUP-083 describía el stack del origen como "Tailwind v4 + shadcn/ui + MUI 7 + next-themes". MUI 7 y `@emotion/*` no tienen un solo import en todo el árbol. | Matizado en `docs/spikes/frontend-migration.md` dentro de esta HU | Fixed |
| RF-091-002 | Dependency scope | Medium | Out of scope | Los 48 componentes de `src/app/components/ui/` son código muerto: ninguna pantalla los importa, y con ellos 38 de las 61 dependencias quedan sin uso real. Pero el destino sí necesita primitivos de formulario. | F2 debe decidir si adopta shadcn/ui (~4-6 paquetes Radix, no 26) o lo descarta | Open |
| RF-091-003 | Backend capability gap | High | Out of scope | Siete capacidades ausentes (C1-C7) impiden conectar la UI del origen: solo 2 de 14 datos tienen contrato y ambos parciales; 4 de las 5 pantallas no tienen ninguno. | Decisión de épica sobre el alcance de F3 | Open |
| RF-091-004 | Mock data in production path | Medium | Out of scope | `GET /billing/summary` devuelve `monthly_spend` y `savings_identified` hardcodeados en `db/database.py`; solo `open_ingestions` es real, pese a existir ingesta Azure real en CockroachDB. | Conectar el endpoint a los datos ingestados | Open |

## Risks / Follow-Ups

- **El alcance de F3 tal como está escrito en el spike no es ejecutable.** Con 4 de 5 pantallas sin
  ningún contrato, "portar el código fuente" no produce una aplicación funcional. La épica debe
  decidir entre portar con datos mock a la espera de backend, recortar pantallas del alcance, o
  añadir tarjetas de backend. Confirma y agrava `RF-083-002`.
- **Hay una vía barata que conviene no perder de vista:** C1 (serie temporal) y C2 (desglose por
  dimensión) son sobre todo camino de lectura sobre datos que el processor ya ingesta y normaliza
  (JUP-072 a JUP-077). Desbloquean `index` y `/operational` sin lógica de negocio nueva.
- F2 arranca con una decisión pendiente (`RF-091-002`) que cambia mucho el `package.json` resultante:
  11 dependencias si se descarta shadcn/ui, ~17 si se adopta.

## Human Approval

- Change: jup-091-inventory-economicon-frontend
- Approval type: post-review
- Decision: approved
- Approver: Victor
- Date: 2026-08-31
- Review accepted: yes
- Checks accepted: yes
- Documentation synchronized: yes
- Archive decision: archive
- Notes: JUP-091 doc-only completada (12/12 tareas): inventario del origen publicado en
  `docs/planning/JUP-091-economicon-source-inventory.md` con las 61 dependencias clasificadas
  (11 `MANTENER`, 2 `SUSTITUIR`, 48 `DESCARTAR`) y las 5 pantallas mapeadas contra los contratos
  reales del backend. Cuatro hallazgos registrados: `RF-091-001` corregido en la propia HU (el
  supuesto T5 del spike describía un stack con MUI y shadcn/ui que no se usa); `RF-091-002`,
  `RF-091-003` y `RF-091-004` quedan abiertos para F2, la épica y el backend respectivamente. Cierra
  la tarjeta F1 `inventariar-frontend-economicon`. Sin `docs/evidence/JUP-091-validation.md`: se
  sigue el precedente de JUP-083 y JUP-090 para HUs doc-only, con `review.md` como único registro de
  validación. **El resultado obliga a replanificar F3 antes de arrancarla** (`RF-091-003`): con 4 de
  5 pantallas sin ningún contrato, portar el código fuente no produce una aplicación funcional. Esa
  decisión de alcance queda explícitamente fuera de esta HU.
