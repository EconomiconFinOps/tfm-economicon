# Review: jup-104-e2e-validation

## Result

Listo para el gate post-review de Victor. **No es un veredicto independiente**: lo redacta quien
implementó. La revisión y la validación de terceros llegan con el pull request («Revision JUP-104» y
«Validacion JUP-104»). Evidencia completa, con las salidas reales, en
[`docs/evidence/JUP-104-validation.md`](../../../docs/evidence/JUP-104-validation.md) y guion
repetible en [`docs/evidence/JUP-104-browser-recipe.md`](../../../docs/evidence/JUP-104-browser-recipe.md).

Resumen: el recorrido completo del operador funciona en un navegador real, contra el stack de Docker
Compose y sin desactivar ninguna protección, **con un fallo del producto y con límites que conviene
leer antes que las cifras**.

- **Acreditado** (guion en Chromium 153, 14 de 15 pasos, y pasada manual en Chrome 154, 9 pasos):
  acceso por el formulario con CORS real entre orígenes distintos; selección y cambio de ámbito;
  costes de Core Finance (`0.06 USD`, 38 registros); ingesta de un documento desde la interfaz hasta
  pgvector, con los 19 fragmentos **idénticos, uno a uno**, a los que produce el algoritmo del
  processor sobre ese texto; filtro por ámbito en la recuperación del asistente; recarga del historial
  y cierre de sesión.
- **Falla el producto, no el guion:** `RF-104-001`. Con conversaciones previas, «New» crea la
  conversación pero el mensaje va a la que era la primera de la lista y la nueva queda vacía.
  Reproducido por el guion y a mano, también a ritmo humano y en Core Finance.
- **`RF-087-002` no se reproduce** y se propone `Fixed`: el historial se recarga con 200 contra
  CockroachDB real.
- **Límites que condicionan la lectura.** El chat **no genera texto**: compone una plantilla con
  fragmentos. Con el proveedor de embeddings `mock`, el único ejecutable sin claves, la recuperación
  **no mide pertinencia**: el fragmento que responde a la pregunta no se recuperó. El modo `litellm`,
  las citas visibles y las preguntas de gasto en el chat no están acreditados.

De los 7 criterios de la tarjeta, **el 2, 3, 5, 6 y 7 se cumplen**; el 1 y el 4 se cumplen **con
salvedades escritas** (ver «Checklist»).

## Scope Reviewed

Diez archivos, todos de documentación o del propio change; **ninguno bajo `apps/`, `tools/`,
`packages/` ni `.github/`**, y sin cambios en `package.json`, `pnpm-lock.yaml`, `docker-compose.yml` ni
`README.md`.

- `docs/evidence/JUP-104-validation.md`: la evidencia del recorrido, paso a paso.
- `docs/evidence/JUP-104-browser-recipe.md`: receta y guion de navegador.
- `docs/spikes/frontend-migration.md`: acceso local corregido, F5 y punto 12 de «Próximos pasos».
- `openspec/findings/backlog.md`: `RF-104-001` a `004` y `RF-087-002`.
- `openspec/changes/jup-104-e2e-validation/`: `proposal.md`, `design.md`, `tasks.md`, la spec nueva
  `operator-journey-validation` y este `review.md`.

Fuera del repositorio, y **no versionados**: el proyecto de Playwright, las capturas y los resultados
de cada pasada, y el entorno virtual de Python. Se menciona en la evidencia qué contienen, no se
adjuntan.

## Checklist

| # | Criterio de la tarjeta | Estado | Dónde |
| --- | --- | --- | --- |
| 1 | Recorrido en navegador real sin desactivar ninguna protección | **Cumplido con salvedades** | Pasos `0.1` y `4.1`; pasada manual |
| 2 | Cada paso registrado con lo hecho y lo observado | Cumplido | Evidencia, grupos 4 a 6 |
| 3 | Ingesta acreditada extremo a extremo | Cumplido | Pasos `5.1` a `5.4` |
| 4 | Asistente con contexto recuperado, o parte dependiente de JUP-022 y JUP-025 registrada | **Cumplido con salvedades** | Pasos `6.1`, `6.2`, `6.4` |
| 5 | Pantallas con datos de demostración identificadas | Cumplido | Paso `4.4`, `RF-104-004` |
| 6 | Todo fallo como hallazgo con su reproducción | Cumplido | `RF-104-001` a `004` en el backlog |
| 7 | Decisión sobre automatizar registrada en `design.md` | Cumplido | `design.md`, decisión 7 |

Salvedades:

- **Criterio 1.** El guion usa Chromium en modo headless con las opciones estándar de automatización
  de Playwright (entre ellas `--no-sandbox` y `--disable-popup-blocking`); el paso `0.1` acredita, con
  la línea de comandos real del proceso, que **ninguna** de `--disable-web-security`,
  `--allow-running-insecure-content`, `--disable-site-isolation-trials` ni
  `--ignore-certificate-errors` está presente. La pasada manual en Chrome 154 cubre el navegador de una
  persona, pero se hizo en Incógnito **sin comprobar si había extensiones permitidas**, y no se probó en
  otros navegadores.
- **Criterio 4.** Se acredita el camino de los datos y el aislamiento por ámbito, no la pertinencia.
  La tarjeta pedía «citando contexto real recuperado»: las citas visibles dependen de JUP-025 (PR #55,
  sin fusionar) y la pertinencia de un proveedor de embeddings real, que esta máquina no puede
  ejecutar. Lo aprobó el gate pre-código como ajuste de alcance.

Escenarios de la spec `operator-journey-validation`: **16 de 18 acreditados**, 1 **no ejercitado**
(el trabajo de ingesta que no se completa, que cubre a nivel de API el smoke de JUP-050) y 1
**pendiente** (que otra persona repita la receta). Tabla completa en la evidencia, apartado
«Trazabilidad».

## Decisiones tomadas durante la implementación

Respecto al plan aprobado en el gate pre-código:

1. **Cinco pasadas del guion, no una.** La primera falló en `6.1` por un defecto de **mi
   comprobación**: comparaba el fragmento con el documento sin normalizar espacios y el chunker los
   normaliza (`" ".join(text.split())`). Las siguientes descubrieron `RF-104-001` (pasadas 2 y 3) y una
   atribución errónea de peticiones en `4.4` (pasada 4). La pasada 5 es la evidencia, y su guion es
   idéntico al de la receta, comprobado byte a byte. Se registran las cinco.
2. **Tarea `6.3b` añadida**, que no estaba en `tasks.md`: reproduce de forma determinista el fallo de
   la conversación nueva. Cuenta como tarea del change (44 en total).
3. **Residuo en el stack, declarado y sin borrar.** Las pasadas dejaron seis copias del mismo documento
   en Growth Ops y 13 conversaciones vacías. Una pasada limpia exigía volúmenes nuevos; **no se borró
   ningún volumen**. La evidencia acota sus afirmaciones («procede de un documento ingerido en estas
   pasadas», no «del de la pasada 5»).
4. **Pasada de solo lectura previa** (`E2E_PHASE=read`) para depurar selectores sin ensuciar el stack, no
   usada como evidencia del recorrido.
5. **Paso `0.1` lee la línea de comandos real del navegador**, porque `chrome://version` no se puede
   abrir con Playwright.
6. **Entorno de Python recreado** fuera del repositorio con Python `3.13.7`; el de JUP-103 ya no
   existía. CI usa `3.12`, que no hay en esta máquina.
7. **Stack parado antes de la batería** (`docker compose stop`, sin borrar volúmenes), porque las pruebas
   con plazos de tiempo son sensibles a la carga (`RF-098-004`).
8. **Grupo 10: parada y decisión.** El PR #75 de JUP-103 no estaba fusionado y había dejado de ser
   fusionable (conflicto con `develop` en `backlog.md`). Se decidió editar ya y resolver al integrar;
   `develop` (JUP-067) se fusionó en la rama sin conflictos y sin tocar `apps/`.
9. **`RF-087-002` a `Fixed`** es una **propuesta** de esta tarjeta; la decisión es de este gate.

## Validation

Todo con la rama en su estado final salvo lo indicado; salidas completas en la evidencia.

| Comprobación | Resultado |
| --- | --- |
| `corepack pnpm local:test` (antes de levantar el stack) | 74 de 74 |
| `local:doctor` y `up --build --wait` en el proyecto `jup104-e2e` | Entorno nuevo; 9 servicios, 8 `healthy` y grafana sin healthcheck, en 5 min 33 s |
| `corepack pnpm local:smoke` (una vez) | 5 de 5 |
| Guion de navegador, pasada 5 | 14 pasos acreditados y 1 fallido (`6.3b`, fallo del producto); 0 errores de página, de consola y de CORS; 0 respuestas 4xx y 5xx |
| Pasada manual en Chrome 154 (Incógnito) | 9 pasos; mismos resultados que el guion, incluido `RF-104-001` |
| `install --frozen-lockfile` | Salida 0; no modifica archivos versionados |
| `lint`, `typecheck`, `build` con `--force` | 4/4, 1/1 y 4/4 tareas, ninguna desde caché |
| Pruebas Python, por mitad | 1085 correctas, 85 omitidas, 0 fallidas |
| Pruebas frontend, un solo worker | 48 archivos y 443 pruebas correctas |
| `openspec:validate`, `jup:check`, `jup:cleanup:check` | 47 de 47, correcto y correcto (con `develop` fusionado) |
| `repository:governance:test` y `ci:check:test` | 13 de 13 y 12 de 12 |

**Sin validar:** la CI del pull request (aún sin abrir) y el comando único `corepack pnpm test`, que no
se ejecutó (se hizo por mitades por `RF-098-004` y `RF-103-005`). Las 85 pruebas omitidas no se han
inspeccionado una a una. Python `3.13.7`, no el `3.12` de CI.

## Excepción del ciclo Red/Green

La tarjeta **no añade ni cambia código de producto ni pruebas**: el diff no toca `apps/`, `tools/`,
`packages/` ni `.github/`. Por tanto no hay ciclo Red/Green ni mutación; es la decisión 8 del
`design.md`, aprobada en el gate pre-código. El guion de navegador no es código del repositorio: vive
fuera, y su texto se versiona como receta. No se corrigió ningún fallo del producto, ni siquiera los
triviales del frontend que la tarjeta permitía.

**ADR:** no aplica (decisión 11 del `design.md`): no se añade ninguna dependencia ni se cambia la
arquitectura. Haría falta un ADR, con nueva aprobación, si se añadiera Playwright al repositorio o un
job de navegador a CI; el siguiente número libre es `ADR-0018`, reservado por el PR #73, así que sería
el `ADR-0019`.

## Review Findings

Ningún bloqueo. Hallazgos del producto para el backlog (ya registrados en esta rama, ninguno corregido
aquí):

| ID | Severidad | Resumen |
| --- | --- | --- |
| `RF-104-001` | Media | La conversación recién creada con «New» no recibe el mensaje: va a la que era la primera de la lista. Reproducido por guion y a mano |
| `RF-104-002` | Baja | Cada `GET /health` abre una conexión nueva a RabbitMQ y deja 12 eventos de `pika`, uno de nivel `error`: ruido que no deja distinguir un fallo real |
| `RF-104-003` | Media | La interfaz no puede saber si un trabajo de ingesta terminó o falló: el backend no tiene lectura de estado de trabajos |
| `RF-104-004` | Baja | `/operational`, `/cuts` y `/recommendations` no avisan de que son demostración; `/anomalies` sí |

**`RF-087-002`:** no se reproduce; propuesta `Fixed`, citando JUP-086 (PR #47) y esta evidencia, con la
nota de que sigue sin haber un test automatizado contra una base real.

Observaciones sin hallazgo (detalle en la evidencia): `GET /favicon.ico` con 404 en el navegador real;
la suma de los grupos mostrados puede diferir un céntimo del total por redondeo; el agrupado por
Servicio deja los 38 registros simulados «sin dimensión»; una petición `ERR_ABORTED` es la capa API
cancelando una consulta al cambiar la selección.

**Errores míos detectados y corregidos durante la ejecución**, por transparencia: la comprobación de
fragmentos de `6.1` (arriba); la atribución de peticiones del paso `4.4`; un recuento de conversaciones
vacías (9 donde eran 10); una primera cifra de ruido de `pika` que incluía mis propias llamadas; y una
instrucción de formato de fecha (`dd/mm`) que no correspondía al navegador de la pasada manual
(`mm/dd`). Todos quedaron corregidos en el guion, la receta o la evidencia.

## Risks / Follow-Ups

- **Conflictos al integrar con el PR #75 (JUP-103), aditivos:** principio de la tabla del backlog
  (`RF-103-001` a `005` frente a `RF-104-001` a `004`) y final de «Próximos pasos» del spike (puntos 11
  y 12). Se resuelven conservando ambas partes, y el punto de esta tarjeta es el 12 por eso.
- **Que otra persona repita la receta** (quien revise o valide el PR) es el único escenario de la spec
  sin acreditar. Necesita un stack con volúmenes nuevos para no heredar el residuo.
- **Residuo en el stack `jup104-e2e`:** parado, con 5 volúmenes y las imágenes `jup104-e2e-*`.
  Borrarlos (`docker compose down -v` en ese proyecto) queda a decisión de quien usa la máquina.
- **Enlaces relativos al archivar:** los de `proposal.md`, `design.md`, este `review.md` y la receta
  bajan un nivel; se corrigen en el mismo paso del archivado y se verifica el del spike.
- **Cada hallazgo es su propia tarjeta.** `RF-104-001` es el único que afecta a que un mensaje acabe
  en la conversación equivocada; conviene tenerlo en cuenta antes de fusionar JUP-025 (PR #55) y
  JUP-036 (PR #69), que conservan el mismo efecto en el mismo archivo.
- **JUP-105** recibe el recuento de pantallas de este recorrido: 4 consumen el backend (`/`, en su
  sección de costes, `/overview-legacy`, `/ingest` y `/assistant`) y 4 son solo demostración
  (`/operational`, `/cuts`, `/anomalies` y `/recommendations`). El `README.md` del frontend sigue
  desactualizado; es de JUP-105.
- **Pregunta abierta de `design.md`, sin responder:** si este registro cuenta como parte del ensayo de
  JUP-065. Se pregunta a quien lo lidera; no cambia ninguna tarea.
- **Automatizar el recorrido en CI** queda para una tarjeta propia: exige que CI levante CockroachDB,
  RabbitMQ y pgvector (`RF-096-004`), cambia el lockfile y `ci.yml`, y pediría ADR.

## Human Approval

- Change: jup-104-e2e-validation
- Approval type: post-review
- Decision: approved
- Approver: Victor
- Date: 2026-10-06
- Archive decision: archive
- Scope reviewed: las 44 tareas de `tasks.md`; este `review.md`; la evidencia
  `docs/evidence/JUP-104-validation.md` (línea base, stack aislado, guion, recorrido de los grupos 4 a 6,
  pasada manual, hallazgos y límites, batería, archivos compartidos y pendientes); la receta
  `docs/evidence/JUP-104-browser-recipe.md`; y los cambios en `openspec/findings/backlog.md` y
  `docs/spikes/frontend-migration.md`.
- Condition approved: ninguna adicional a lo redactado en este `review.md`.
- Decisions approved: (1) **`RF-087-002` pasa a `Fixed`**, tal como lo propone la tarjeta, citando
  JUP-086 (PR #47) y esta evidencia, y con la nota de que sigue sin haber un test automatizado contra una
  base real. (2) **Se archiva con `RF-104-001` a `RF-104-004` abiertos y sin corregir**, incluido el paso
  `6.3b` fallido: es un fallo del producto, no del recorrido, y cada hallazgo es su propia tarjeta. (3)
  Los criterios 1 y 4 de la tarjeta se dan por cumplidos **con las salvedades escritas** en «Checklist»
  (opciones de automatización del Chromium del guion, extensiones de Incógnito sin comprobar, y
  pertinencia y citas fuera de lo acreditable con `mock` y sin JUP-025). (4) Los conflictos aditivos con
  el PR #75 de JUP-103 se resuelven al integrar, conservando ambas partes.
- Resultado verificado: guion de navegador, pasada 5, con 14 pasos acreditados y 1 fallido por el
  producto, 0 errores de página, de consola y de CORS y 0 respuestas 4xx y 5xx; pasada manual en Chrome
  154 con los mismos resultados; ingesta extremo a extremo con 19 fragmentos idénticos a los del
  algoritmo del processor; `lint`, `typecheck` y `build` desde la raíz (4 de 4, 1 de 1 y 4 de 4, con
  `--force`); pruebas por mitades (1085 de Python y 443 de frontend correctas); y `openspec:validate`
  47 de 47, `jup:check`, `jup:cleanup:check`, `repository:governance:test` 13 de 13 y `ci:check:test`
  12 de 12 sobre el árbol fusionado con `develop` (`f0cacdd`).
- Salvedades aceptadas: el chat no genera texto y, con `mock`, la recuperación no mide pertinencia; el
  modo `litellm`, las citas visibles y las preguntas de gasto no están acreditados; el escenario del
  trabajo de ingesta que no se completa no se ejercitó en el navegador; que otra persona repita la receta
  queda pendiente; el residuo de las pasadas sigue en el stack `jup104-e2e`, parado y sin borrar; Python
  `3.13.7` en lugar del `3.12` de CI; 85 pruebas omitidas sin inspeccionar; el comando único
  `corepack pnpm test` no se ejecutó.
- Constraints: ningún archivo de `apps/**`, `tools/**`, `packages/**` ni `.github/**`, ni `package.json`,
  `pnpm-lock.yaml`, `docker-compose.yml` ni `README.md`, en el diff de la rama. La aprobación **no**
  sustituye la revisión y la validación del pull request («Revision JUP-104» y «Validacion JUP-104»),
  **no** acredita el CI (pendiente del PR) ni autoriza fusionar.
- Required changes before archive: ninguno más; al archivar se corrigen los enlaces relativos de
  `proposal.md`, `design.md`, este `review.md` y la receta (bajan un nivel) y se verifica el enlace del
  spike a `openspec/changes/archive/<fecha>-jup-104-e2e-validation/`.
