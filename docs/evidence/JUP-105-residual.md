# JUP-105: reconciliación residual del 10/10/2026

[Tarjeta](https://trello.com/c/YZvtBdGV) ·
[PR #86](https://github.com/EconomiconFinOps/tfm-economicon/pull/86) ·
[Evidencia original](JUP-105-validation.md)

## Alcance y procedencia

La implementación de Víctor ya estaba en `ca9e67f902e74c66b603424ca0589119542acde4`.
Esta continuación del encargo de JUP-105 corrige el residual documental; conserva
el pairing real de Alejandro del 10/10, recibo Trello `6ac997e95f590e8340a02e6c`.
No constituye `Revision JUP-105` ni `Validacion JUP-105`, que corresponden a
Lucía y Paris. No modifica roles, prioridades ni criterios.

Preparación aislada en `tfm-economicon-jup105-residual`, rama
`docs/JUP-105-residual`, creada desde `origin/develop` `c2995a1` e incorporando
la rama de #86 sin conflictos. Los cambios entrantes de gobernanza de JUP-062
se conservan. No se modifica el checkout compartido.

## Correcciones

1. `DashboardPage.test.tsx` describe ahora el contexto de sesión implementado y
   los datos reales de `/`. Suprime las referencias obsoletas a la fase Red y
   `DashboardPage.jsx`. Solo cambian comentarios; la retirada de la ruta sigue
   pendiente en `RF-105-001`.
2. `tasks.md` y `review.md` archivados de JUP-097 reciben notas fechadas para
   las dos afirmaciones de exclusividad que faltaban en la búsqueda anterior.
   Se mantienen resultados y decisiones históricas.
3. Evidencia, tasks y backlog reconocen el diagnóstico Codex entregado el 09/10.
   [RF-093-001](../continuidad/pnpm-entorno-rf093001.md) sigue `Open`: la prueba
   sobre `ff2ea6b` dio pnpm 11.19.0 y lint 0/4 con `NO_TTY`; **no es una prueba
   desde la consola normal ni una corrección permanente**. La nota al inicio de
   `review.md` distingue el nuevo corte del gate histórico, que queda intacto.
4. Se registra el resultado final de la CI y se mantiene continuidad con índice
   y enlaces, preservando las entradas ya versionadas.

## Criterios de aceptación

| Criterio | Evidencia y estado en este aporte |
| --- | --- |
| 1. Batería de raíz | Evidencia del líder conservada; CI técnica de ca9e67f verde. Los 145 fallos del backend en Windows (`RF-105-004`) siguen pendientes: no se declara cumplimiento total ni se repite esa batería como prueba propia. |
| 2. `allowJs: false` | Configuración de #86 conservada; control TS7016 y 629 pruebas documentados por el líder y contraste de pairing existente. No hay nueva modificación del compilador. |
| 3. Spike cerrado | Conservado el punto 13 y las excepciones explicadas del checklist/placeholder histórico. |
| 4. Recuento único | Se conserva como fuente [Rutas del frontend](../../apps/frontend/README.md#rutas); los nuevos comentarios y notas remiten allí. |
| 5. Textos contradictorios | Corregido el comentario vivo y anotados los dos registros archivados adicionales. Búsqueda multilínea sobre el árbol y lectura de las notas; resultados históricos preservados. |
| 6. Findings con responsable y motivo | Estados y motivos conservados; `RF-093-001` precisa la confirmación pendiente. Las categorías de equipo no se convierten en asignaciones personales: liderazgo aún debe concretar las que Trello no identifica. |
| 7. Deuda documental | Barrido de enlaces del aporte; solo se admiten los dos destinos ficticios `route` de JUP-099 como falsos positivos. No se reintroducen referencias a configuración personal como instrucciones. |
| 8. Ruta y módulo huérfano | Decisión de conservación intacta; `RF-105-001` y `RF-105-002` siguen `Open`. Corregir el comentario no equivale a retirar código. |
| 9. Estado final | Migración técnica descrita en el spike; cierre operativo pendiente de dictámenes, integración y actualización por liderazgo. |

## Verificaciones propias

Entorno: Windows, Node 24.14.1, pnpm fijado 9.0.0, OpenSpec 1.8.0,
TypeScript 5.9.3 del lockfile. Logs y scripts reproducibles en
`../materiales/07-evidencias/JUP-105-residual-20261010/` del workspace de coordinación.
Los bloqueos iniciales de red offline y `spawn EPERM` del sandbox se resolvieron
ejecutando las mismas comprobaciones con acceso necesario; no son fallos del producto.

- `corepack pnpm install --frozen-lockfile --offline=false`: exit 0, lockfile intacto.
- `corepack pnpm jup:check:all`: exit 0. El change 105 está archivado; no se
  recrea como activo para forzar `jup:check -- --change`.
- `corepack pnpm openspec:validate`: **55/55**. El incremento frente a 54 incluye
  la spec de gobernanza de memoria entrante en `develop`.
- `node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs`:
  **82/82**, sin omisiones.
- `corepack pnpm jup:cleanup:check`: exit 0, **983 archivos**.
- `git diff --check`: exit 0; lockfile, configuración del compilador, runtime y
  workflows intactos en el commit residual.
- `node ../materiales/07-evidencias/JUP-105-residual-20261010/check-residual.cjs .`:
  salida JavaScript de `DashboardPage.test.tsx` idéntica antes/después con
  TypeScript 5.9.3 y `removeComments`; **1.062 enlaces** comprobados, solo los dos
  falsos positivos de JUP-099 (líneas 505 y 793). `allowJs: false`, cero JS/JSX
  en src/tests y RF-093-001/RF-105-001 aún `Open`.

## CI y límites

Lectura del 10/10 de todas las reviews, comentarios de conversación e inline de
#86: las tres fuentes estaban vacías. CI sobre **ca9e67f**, ejecución
[38013862466](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38013862466):
los siete jobs técnicos/política terminaron con éxito, incluido `Python tests
(backend)`. `JUP reviews` falla porque faltan los dos dictámenes. Sustituye la
mención a CI todavía en ejecución en el corte anterior; es evidencia remota,
no una batería nueva de este chat ni una validación del aporte posterior.

No se ejecutan UI/HTTP, backend, consola normal ni cambios globales de Corepack;
no se deduce de la CI Linux una corrección de Windows. No se añaden tests de
producto para comentarios/prosa. La identidad del código ejecutable de la prueba
se verifica mecánicamente. `RF-105-004`, RF-093-001 y decisiones de producto
mantienen sus límites. La evidencia nueva no concede aceptación humana.
