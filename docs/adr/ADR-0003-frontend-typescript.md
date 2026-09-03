# ADR-0003: Adopción de TypeScript en el frontend

- Estado: Proposed
- Fecha: 2026-09-02
- Tarjeta Trello: [JUP-092](https://trello.com/c/R5t2PL2F/84-jup-092-adr-de-adopción-de-typescript-en-el-frontend)
- OpenSpec relacionado: `jup-092-frontend-typescript-adr`
- Sustituye a: ninguno
- Sustituido por: ninguno

## Contexto

El spike de migración del frontend ([docs/spikes/frontend-migration.md](../spikes/frontend-migration.md))
fija la adopción de TypeScript en `apps/frontend` como su decisión número 1, calificándola de
"transversal y duradera" porque afecta tooling, build, lint y todas las tareas futuras del frontend.
[docs/adr/README.md](README.md) exige ADR para exactamente este tipo de decisión: patrones
compartidos que afectan a varios módulos o tareas futuras.

El punto de partida, verificado en JUP-090 y JUP-091 antes de esta tarjeta, no es el que el spike
supuso inicialmente:

- **El destino** (`apps/frontend`) es JavaScript con JSX. No declara `typescript` ni paquetes de
  tipos; no hay `tsconfig.json` en ningún punto del repo.
- **El origen** (Economicon) llega en TSX, pero **tampoco tiene verificación de tipos**: no declara
  `typescript` entre sus 61 dependencias (inventario de JUP-091) ni incluye `tsconfig.json`. Su TSX
  lo transpila esbuild sin comprobar nada.

Adoptar TypeScript no es, por tanto, "conservar lo que trae el origen": es **introducir verificación
de tipos donde no existe en ningún lado**, y sería el primer código tipado del repositorio en el lado
JavaScript — backend y processor están en Python.

Dos hechos adicionales, verificados directamente sobre el repo, condicionan la decisión:

- `apps/frontend` acumula **49 violaciones de `react/prop-types`** (recuento reproducido en esta HU
  con `pnpm lint`), el motivo por el que su lint no es check obligatorio de CI
  ([docs/governance/github-branch-protection.md](../governance/github-branch-protection.md),
  finding `RF-082-002` en `openspec/findings/backlog.md`). TypeScript sustituye a `prop-types` como
  mecanismo de validación de props.
- `apps/frontend` no tiene tests: su script `test` es un `echo` sin tooling real.

Sin esta decisión resuelta, la tarjeta de tooling de F2 (`jup-0xx-configurar-typescript`) no puede
instalar dependencias ni crear `tsconfig` sin saber qué nivel de rigor se exige, cómo convive con el
JavaScript existente durante la migración por slices, y qué ocurre con el lint actual.

## Decisión

<!-- Se completa en las tareas 2.2 y 2.3 -->

## Consecuencias

<!-- Se completa en la tarea 2.4 -->

## Alternativas consideradas

<!-- Se completa en la tarea 2.5 -->

## Evidencia y seguimiento

<!-- Se completa en la tarea 2.6 -->
