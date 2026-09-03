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

Se adopta TypeScript en `apps/frontend` con las siguientes cuatro decisiones, aprobadas por el
equipo en el gate pre-código de JUP-092:

**1. Nivel de rigor: `strict: true` desde el inicio.**
El frontend se reemplaza por completo (estrategia de reemplazo total del spike); no hay deuda
JavaScript heredada que migrar de forma gradual. El momento más barato para exigir rigor es antes de
escribir el código nuevo, no después de portarlo sin tipos y retrofitear `strict` sobre él.

**2. Convivencia con JavaScript: `allowJs: true` durante la migración, `false` al cerrar F5.**
El spike prohíbe explícitamente el "big bang" y exige avanzar por slices verificables. Con
`allowJs: false` desde el primer commit, el primer slice migrado rompería el build de todo el
JavaScript aún sin portar. La tarjeta de cierre de F5 endurece la opción a `false` una vez no quede
JavaScript en `src/`.

**3. CI: type-check como check obligatorio; `RF-082-002` se cierra por obsolescencia, no se resuelve.**
El type-check debe correr en CI — de lo contrario `strict` es solo una anotación decorativa sin
consecuencia. Respecto a las 49 violaciones de `react/prop-types`: la vía elegida **no es arreglarlas
una a una**, sino que la regla deja de aplicar. `prop-types` es validación de tipos en tiempo de
ejecución; TypeScript la sustituye en tiempo de compilación con garantías más fuertes. Mantener
ambas sería redundante. F2 desactivará `react/prop-types` para archivos `.ts`/`.tsx` en
`eslint.config.js`, y `RF-082-002` se documentará como resuelto estructuralmente por la migración, no
por corrección manual de las 49 violaciones.

**4. Ubicación del `tsconfig`: a nivel de `apps/frontend`, no compartido.**
`packages/shared-config` (`@finops/shared-config`) existe, pero hoy solo contiene un `index.js` con
metadatos del workspace. `apps/frontend` sería el **único** paquete TypeScript del repositorio —
backend y processor son Python. Extraer una configuración base compartida para un solo consumidor es
abstracción prematura. Si en el futuro aparece un segundo paquete TypeScript en el monorepo, se
extraerá entonces un `tsconfig.base.json` a `shared-config`; esta decisión no lo descarta, solo lo
pospone hasta que haya un segundo consumidor real.

## Consecuencias

<!-- Se completa en la tarea 2.4 -->

## Alternativas consideradas

<!-- Se completa en la tarea 2.5 -->

## Evidencia y seguimiento

<!-- Se completa en la tarea 2.6 -->
