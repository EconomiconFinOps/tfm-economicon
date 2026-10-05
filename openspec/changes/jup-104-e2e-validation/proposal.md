JUP: JUP-104
Trello: https://trello.com/c/lVvZa7P5/96-jup-104

## Why

La épica de migración del frontend llega a F5 sin que nadie haya recorrido la aplicación migrada de
principio a fin en un navegador, contra el backend local y sin atajos. Lo que existe son piezas:

- [JUP-095](../archive/2026-09-12-jup-095-portar-codigo-fuente/) lo intentó con Chromium y tuvo que
  desactivar la seguridad web para pasar del acceso, porque el backend no enviaba cabeceras CORS.
- [JUP-097](../archive/2026-09-21-jup-097-reconcile-api-layer/) verificó los contratos con peticiones
  directas y dejó el recorrido en navegador como pendiente.
- [JUP-085](../archive/2026-09-24-jup-085-auth-session-contract/) resolvió el CORS y comprobó en
  navegador real el acceso y el ciclo de sesión (8 de 8 en
  [su evidencia](../../../docs/evidence/JUP-085-validation.md)); la revisión del PR #50 observó
  también en navegador la expiración de sesión (`RF-098-002`).
- [JUP-050](../archive/2026-10-01-jup-050-reproducible-local-runtime/) aportó `local:smoke`, que
  recorre **por API** salud, acceso, costes y un trabajo de documento hasta el processor.
- La batería del frontend ([`frontend-quality-baseline`](../../specs/frontend-quality-baseline/spec.md))
  usa respuestas HTTP simuladas y declara que no sustituye a una prueba integrada.

Falta la parte que ninguna de ellas cubre: enviar un documento **desde la interfaz**, comprobar que
llega al processor y queda indexado, y ver que el asistente responde con fragmentos de ese documento
para el ámbito de cliente activo.

Al verificar el alcance contra el código (2026-10-05, `develop` en `0488372`) aparecieron cuatro
hechos que cambian lo que esta tarjeta puede acreditar, y que conviene fijar antes de ejecutar nada:

- **El chat no llama a un modelo generativo.** La respuesta del backend es una plantilla fija que
  lista hasta tres fragmentos recuperados. La configuración del modelo de lenguaje solo interviene
  en un paso del processor durante la ingesta.
- **Lo que es real desde [JUP-022](../archive/2026-10-03-jup-022-semantic-retrieval/) es la
  recuperación, y tiene dos modos.** Con el proveedor de embeddings `mock`, el de por defecto, se
  devuelven los cuatro fragmentos más cercanos del ámbito sin umbral de distancia: acredita el
  camino de los datos, no la pertinencia. El modo `litellm` necesita un gateway que vive en un
  proyecto Compose aparte, una clave de pago, una base vectorial de otra dimensión y reindexar; la
  evidencia de JUP-022 declara sin validar ese arranque completo.
- **La interfaz de ingesta solo muestra que el trabajo fue aceptado.** No vuelve a consultar su
  estado, así que la prueba de que se procesó está fuera de la interfaz.
- **`RF-087-002` sigue `Open` pero su causa ya no está en el código.** El error al recargar el
  historial de una conversación venía de decodificar dos veces un valor; JUP-086 (PR #47) cambió esa
  lectura. Ningún test contra la base de datos real lo cubre, así que hay que comprobarlo.

## What Changes

- **Preparar un entorno local identificable**: stack de Docker Compose reconstruido desde esta rama,
  en un proyecto Compose propio con volúmenes nuevos, comprobado con `local:doctor` y `local:smoke`.
- **Recorrer la aplicación en un navegador real**, sin desactivar ninguna protección y sin simular
  respuestas del backend: acceso, selección y cambio de ámbito de cliente, resumen de costes,
  ingesta de un documento, conversación con el asistente, recarga del historial y cierre de sesión.
- **Acreditar la ingesta extremo a extremo**: el trabajo creado desde la interfaz queda completado y
  deja el documento, sus fragmentos y sus vectores en la base vectorial, para el ámbito correcto.
- **Acreditar el contexto del asistente**: la respuesta contiene fragmentos del documento ingestado
  en el ámbito activo y no los contiene en otro ámbito. Se hace con el proveedor de embeddings
  `mock` y se deja escrito qué no acredita ese modo (ver `design.md`, decisión 1).
- **Comprobar `RF-087-002`** y dejar su estado al día en `openspec/findings/backlog.md`.
- **Identificar en el registro** qué pantallas y bloques muestran datos de demostración.
- **Registrar cada fallo** como hallazgo `RF-104-NNN` con su reproducción, sin corregirlo.
- **Dejar el recorrido repetible**: guion de navegador versionado como receta en la evidencia, y la
  decisión sobre automatizarlo o no en `design.md` (decisión 7).
- **Actualizar el spike** `docs/spikes/frontend-migration.md`: sustituir el marcador
  `jup-0xx-validacion-e2e` por `jup-104-e2e-validation` y corregir las dos menciones del acceso
  local `operator@example.com` / `secret`, que dejó de ser cierto con JUP-085.

No se modifica código de producto, pruebas, dependencias, `docker-compose.yml` ni CI. No se añade
Playwright al repositorio.

## Capabilities

### New Capabilities

- `operator-journey-validation`: qué debe acreditar una validación integrada del recorrido del
  operador (navegador real sin protecciones desactivadas, pasos cubiertos, ingesta y contexto del
  asistente comprobados más allá de lo que muestra la interfaz, límites declarados, hallazgos con
  reproducción) y cómo queda registrada para que otra persona pueda repetirla. Ninguna spec vigente
  lo cubre: [`frontend-quality-baseline`](../../specs/frontend-quality-baseline/spec.md) describe la
  batería con respuestas simuladas, [`local-runtime-operations`](../../specs/local-runtime-operations/spec.md)
  el smoke por API, y [`frontend-navigation-shell`](../../specs/frontend-navigation-shell/spec.md)
  el armazón y las direcciones de las pantallas.

### Modified Capabilities

<!-- Ninguna. Esta tarjeta observa el comportamiento que ya especifican `demo-auth-session`,
     `frontend-navigation-shell`, `frontend-api-layer`, `document-ingestion-handoff`,
     `semantic-retrieval` y `local-runtime-operations`; no cambia ninguno de sus requisitos. Si el
     recorrido encuentra una desviación respecto de alguna, se registra como hallazgo. -->

## Impact

- **Nuevo:** `docs/evidence/JUP-104-validation.md` (recorrido paso a paso),
  `docs/evidence/JUP-104-browser-recipe.md` (guion de navegador) y, al archivar, la spec
  `openspec/specs/operator-journey-validation/spec.md`.
- **Modificado:** `openspec/findings/backlog.md` (fila `RF-087-002` y los hallazgos nuevos) y
  `docs/spikes/frontend-migration.md` (hechos del destino, F5 y próximos pasos).
- **Solo lectura:** todo `apps/**`, `tools/**`, `packages/**`, `.github/**`, `docker-compose.yml`,
  `package.json`, `pnpm-lock.yaml`, `apps/frontend/README.md` y `README.md`.
- **Fuera del repositorio:** el proyecto con Playwright que conduce el navegador, las capturas de
  pantalla y los volúmenes del proyecto Compose de la validación. El proyecto Compose por defecto de
  la máquina no se toca.
- **Dependencia de orden con JUP-103 (PR #75, aprobado y sin fusionar):** ese PR reescribe F4 y
  añade un punto al final del spike, y añade filas al principio de la tabla del backlog. Los cambios
  de esta tarjeta en esos dos archivos se hacen al final, con JUP-103 ya en `develop` (ver
  `design.md`, decisión 10).
- **PR abiertos que cambian lo que se recorre:** JUP-025 (#55, citas visibles en el chat), JUP-036
  (#69, preguntas de gasto en el chat) y JUP-017 (#66, panel de etiquetado en la pantalla
  principal). Si alguno se fusiona antes de cerrar, se repite el paso afectado.
- **Relación con JUP-065 (PR #63, abierto):** esta tarjeta reutiliza las entradas que ya están en
  `develop` (el corpus de `docs/assistant-corpus/` y la pregunta `JUP-069-004`), no su guion. No
  sustituye su ensayo, que exige modelo real y citas visibles.
- **Findings:** `RF-087-002` pasa a `Fixed` si el historial carga, o conserva `Open` con la
  reproducción nueva. Los fallos que aparezcan se registran como `RF-104-NNN`.
- **ADR:** no aplica; no se añade ninguna dependencia ni se cambia la arquitectura (ver `design.md`,
  decisión 11).
