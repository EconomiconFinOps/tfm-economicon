# JUP-057 — Evidencia de preparación del panel

Fecha inicial: 2026-10-01. [Tarjeta](https://trello.com/c/29e5Pisa).
Base `de0d62e`; rama `feat/JUP-057-anomalies-panel`.
[PR #62](https://github.com/EconomiconFinOps/tfm-economicon/pull/62), implementación
`c6015a3` (histórica, anterior a las correcciones del 02/10).

## Resultado y alcance

Se reutiliza `/anomalies` y su protección de sesión. Los cinco ejemplos originales
se conservan tipados: tres abiertos, dos abiertos de criticidad alta, impacto
estimado abierto de 30.700 EUR y dos resueltos. Los indicadores se derivan de las
filas y se etiquetan como resumen de toda la muestra, independiente del filtro.

La vista inicial contiene EC2, CloudFront y EBS, ordenados por criticidad e impacto.
Permite combinar criticidad y estado, recuperar la vista inicial
y exportar únicamente las filas visibles. La exportación lleva origen y periodo
demo; queda deshabilitada cuando no hay resultados. Se retiran el gráfico
supuestamente en tiempo real y las métricas ficticias 23/87%.

Los datos son explícitamente independientes del cliente activo y del backend.
No existe detección nueva, alerta saliente, resolución persistente ni ahorro real.
JUP-030, RF-091-003 y RF-095-002 conservan su alcance pendiente.

## Comprobaciones iniciales (01/10, antes de las correcciones)

- Instalación: `corepack pnpm install --frozen-lockfile`, sin cambios de lockfile.
- Pruebas focalizadas: cinco escenarios en `AnomaliesPanel.test.tsx`, PASS.
- `corepack pnpm --filter @finops/frontend typecheck`: PASS (tres configuraciones).
- `corepack pnpm --filter @finops/frontend lint`: PASS.
- `corepack pnpm --filter @finops/frontend build`: PASS; aviso de bundle >500 kB.
- `corepack pnpm openspec:validate`: 36/36 PASS.
- `corepack pnpm jup:check -- --change jup-057-anomalies-panel`: PASS.
- `corepack pnpm jup:cleanup:check` y `git diff --check`: PASS.
- `corepack pnpm --filter @finops/frontend test -- --maxWorkers=1`: 46 archivos,
  269 tests PASS, cero fallos. Tras los ajustes de texto/etiquetas se repiten las
  cinco pruebas focalizadas y el navegador, también PASS.

Se corrigieron dos incidencias durante la verificación: las etiquetas envolventes
incluían el texto de las opciones en una consulta de accesibilidad Playwright;
ahora label/select son hermanos. El test usó inicialmente `exact` en ByRoleOptions,
propiedad no soportada por Testing Library; retirada y typecheck repetido en verde.

## Navegador real inicial (01/10)

Chromium mediante Playwright, viewport desktop 1440×1100 y móvil 390×844,
sesión ficticia y respuestas `/me`/`/tenants` interceptadas. No valida autenticación
ni detección contra servicios reales.

Comprobaciones PASS: orden/indicadores iniciales, filtros combinados, CSV realmente
descargado con las dos filas resueltas y procedencia demo, estado vacío/exportación
deshabilitada, restablecimiento, orden por impacto, controles móviles y contención
del panel. Cero errores `pageerror`.

El panel mide 390 px de clientWidth y scrollWidth; la región de tabla mide 341 px
y desplaza sus 860 px internos. La página completa mide 1026 px debido a la
cabecera/navegación heredada de `Layout.tsx`, sin cambios en esta rama. Es el
[RF-026-002 existente](../../openspec/findings/backlog.md#rf-026-002), no un fallo
resuelto por este cambio. No se afirma aprobación visual global del shell móvil
ni una nueva excepción humana para JUP-057.

Capturas y script de reproducción se conservan en el workspace local, fuera de
Git, en `materiales/07-evidencias/JUP-057-panel-2026-10-01/`: `desktop.png`,
`mobile.png`, `empty.png`, `filtered-demo.csv`, `browser-results.json`,
`frontend-tests.log` y `playwright-test-jup057.js`.

Reproducción: iniciar `corepack pnpm --filter @finops/frontend dev`, abrir
`/anomalies` con sesión demo; comprobar resumen, seleccionar Resuelto + Media,
exportar CSV, cambiar a Alta para vacío y restablecer. Repetir a 390 px, usando
scroll horizontal de la tabla para acceder a impacto/fecha/estado.

## Revisión

Evaluación visual independiente por otro agente, del mismo proveedor por no
disponer de otro proveedor en esta sesión. Primera ronda PASS con dos mejoras
menores aplicadas: texto de ordenación más corto en tablet y ayuda visible para
desplazar la tabla en pantallas estrechas. Segunda ronda PASS con capturas nuevas
a 1440/768/375 px y comprobación de filtros/CSV, sin errores de página.
Se conserva la limitación RF-026-002.
No sustituye revisión de Paris ni validación de Victor.

## Correcciones solicitadas por Victor — 02/10/2026

- Se retira el selector «Ordenar por». La prioridad fija cumple el spec:
  criticidad descendente, después impacto descendente. Se conservan las cifras
  de la muestra y se explica la prioridad en pantalla.
- Dos tests nuevos con fixture adversarial prueban desempate por impacto,
  exclusión de una alta resuelta del contador de altas abiertas, todos los
  indicadores independientes de los filtros y procedencia independiente del
  cliente. Los cinco tests existentes se adaptan a la prioridad fija.
- Se retiran del diff `AGENTS.md` y `docs/continuidad/`; se conserva la documentación
  de alcance y evidencia en OpenSpec/docs/evidence. La continuidad privada permanece
  fuera de Git. No se publica una nueva norma del equipo.
- Conflicto resuelto incorporando develop `5a54ce2`, incluidos estilos JUP-099:
  panel adaptado a tokens semánticos sin añadir excepciones de color.
- Se actualiza la fila de anomalías del mapa de carencias y se restauran las
  referencias RF-091-003/RF-095-002 y el marcador de fixtures sustituibles.

Verificación del 02/10 tras incorporar develop:

- Siete tests del panel y 173 tests de tokens PASS (180 focalizados).
- Sensibilidad: siete mutantes temporales detectados por fallos de aserción:
  quitar desempate por impacto, contar altas resueltas, hacer depender del filtro
  el contador de abiertas/altas abiertas/resueltas, atribuir ejemplos al cliente
  y eliminar el aviso de alcance del resumen. Se restaura la fuente original y
  se repiten los siete tests como control. No se usa un error de compilación como
  evidencia de detección. El selector retirado ya no tiene un mutante aplicable.
- Suite frontend serial: 48 archivos, 443 tests PASS, cero fallos.
- Typecheck (tres configuraciones), lint y build PASS; permanece aviso >500 kB.
- OpenSpec estricto 37/37, trazabilidad JUP-057, higiene y diff check PASS.
- Chromium sobre build/preview 4173, escritorio y móvil: prioridad fija y ausencia
  del selector, métricas, filtros, CSV realmente descargado, vacío/reset y
  contención local PASS; cero pageerror. Panel 390/390, región de tabla 341/860;
  shell 1026 px heredado. Sesión y endpoints simulados.
- [Receta de navegador completa](JUP-057-browser-recipe.md) versionada, ejecutable
  en un entorno externo con Playwright, sin rutas personales ni credenciales.

Los resultados históricos anteriores se conservan identificados como tales.
