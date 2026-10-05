JUP-104 — Validación E2E del recorrido completo. Carril `standard`.

## Context

Motivación y alcance en [`proposal.md`](proposal.md); requisitos en
[`specs/operator-journey-validation/spec.md`](specs/operator-journey-validation/spec.md). Aquí solo el
estado que condiciona el enfoque, leído en el código el 2026-10-05 sobre `develop` en `0488372`. Nada
de esta sección se ha ejecutado todavía: el stack estaba parado.

**Pantallas.**

| Dirección | Origen de los datos |
| --- | --- |
| `/login` | Backend (`POST /auth/login`) |
| `/` | Dos secciones: "Costes reales de Azure" (backend) y otra rotulada "Datos de demostración" |
| `/operational`, `/cuts`, `/recommendations` | Demostración |
| `/anomalies` | Datos de prueba, con un aviso visible "Datos de demostración" |
| `/ingest`, `/assistant`, `/overview-legacy` | Backend |

La pantalla principal arranca con el mes en curso como periodo, que no tiene datos: los costes que
carga `local:smoke` son de `2024-06-01` a `2024-06-21` y pertenecen a Core Finance (`tenant-core`).
Growth Ops (`tenant-growth`) no recibe costes.

**Ingesta.** `/ingest` es un formulario de texto (origen, URI del artefacto y contenido). Al enviar
muestra "Job accepted" con el identificador, el estado y la cola, y no vuelve a consultar. El
processor trocea el texto, calcula un vector por fragmento y guarda documento, fragmentos y vectores
en pgvector con el identificador del trabajo como identificador del documento. El estado del trabajo
vive en la tabla `jobs` de CockroachDB; `local:smoke` ya lo lee de ahí.

**Asistente.** `POST /assistant/conversations/{id}/messages` guarda la pregunta, calcula su vector
con el proveedor de embeddings configurado, busca en pgvector filtrando por ámbito y compone la
respuesta con una plantilla: una frase fija y hasta tres fragmentos (origen y los primeros 140
caracteres), o un mensaje de "sin contexto" si no recupera nada. La interfaz pinta el rol y el texto
de cada mensaje; los fragmentos recuperados viajan en la respuesta pero no se muestran aparte. El
backend escribe un evento `retrieval` con identificadores de fragmento y de documento y distancias,
sin contenido.

**Proveedor de embeddings.**

| | `mock` (por defecto) | `litellm` |
| --- | --- | --- |
| Dimensión | 8 | 1536 |
| Umbral de distancia por defecto | Ninguno | 0.6 |
| Qué necesita | Solo `RUNTIME_ENVIRONMENT=development` o `test` | Gateway de `infra/litellm` (proyecto Compose aparte), clave de OpenRouter, dos claves virtuales, volumen de pgvector nuevo y reindexado |
| Estado | Camino habitual en local | La [evidencia de JUP-022](../../../docs/evidence/JUP-022-validation.md) declara sin validar el arranque completo contra Compose; ADR-0016 y ADR-0017 siguen `Proposed` |

El `.env` de la máquina de validación no define el proveedor ni las claves del gateway.

**Entorno.** El stack completo se levanta con Docker Compose desde la raíz; el frontend del
contenedor sirve la compilación, y la dirección del backend es un argumento de compilación.
`local:doctor` y `local:smoke` respetan `COMPOSE_PROJECT_NAME`. `local:doctor` no valida
`CORS_ALLOWED_ORIGINS` (`RF-050-002`). Cada ejecución de `local:smoke` añade un documento y un
fragmento `local-smoke` al corpus de `tenant-core`.

**Hallazgos abiertos que el recorrido alcanza.** `RF-087-002` (error al recargar el historial; su
causa ya no está en el código), `RF-096-002` (enviar un mensaje antes de que el processor haya
migrado pgvector da un error y deja la pregunta sin respuesta) y `RF-098-002` (el aviso de sesión
expirada puede tardar unos 7 s).

**Otros cambios en curso.** JUP-103 (PR #75, aprobado y sin fusionar) modifica el spike y el
backlog. JUP-025 (#55), JUP-036 (#69) y JUP-017 (#66) cambian el chat o la pantalla principal y no
están en `develop`. Playwright no es dependencia del repositorio; los precedentes de navegador
(JUP-099 y la [receta de JUP-057](../../../docs/evidence/JUP-057-browser-recipe.md)) lo ejecutan desde
fuera.

## Goals / Non-Goals

**Goals:**

- Que cada afirmación del registro se apoye en algo observado en esta ejecución, con el commit y el
  modo identificados.
- Que la prueba de la ingesta y del contexto del asistente no dependa de lo que la interfaz dice de
  sí misma.
- Que el recorrido se pueda repetir en otra máquina con lo que queda versionado.
- Que el resultado no dependa de datos que ya hubiera en la máquina.

**Non-Goals:**

- Acreditar la calidad semántica de la recuperación ni una respuesta generada por un modelo.
- Montar el gateway de LiteLLM, conseguir claves o reindexar a 1536 dimensiones.
- Repetir las pruebas de sesión expirada y de credenciales incorrectas, ya acreditadas en JUP-085 y
  JUP-098.
- Corregir lo que el recorrido encuentre, conectar pantallas de demostración a datos reales o
  actualizar `apps/frontend/README.md` (JUP-105).
- Pruebas de carga, rendimiento, accesibilidad o despliegue fuera de local.
- Añadir una prueba de navegador a CI.

## Decisions

### 1. El recorrido se acredita con el proveedor de embeddings `mock`

Es el único modo que la máquina de validación puede ejecutar hoy y el que usa cualquier clon local.
Con él queda probado el camino de los datos: el documento enviado por la interfaz se trocea, se
guarda y vuelve en la respuesta del asistente, filtrado por ámbito. No queda probada la pertinencia:
sin umbral, `mock` devuelve los cuatro fragmentos más cercanos del ámbito sea cual sea la pregunta.
La evidencia lo dice así y enumera como pendiente el modo `litellm`.

En ningún documento de esta tarjeta se escribe "modelo real" ni "respuesta generada": el chat no
genera texto.

*Alternativas descartadas.* Acreditar con `litellm`: exige gateway, clave de pago y reindexado que
esta tarjeta no tiene, y arrastraría un arranque que JUP-022 dejó sin validar. Hacer ambos: duplica
el entorno sin que la tarjeta lo pida; si el equipo aporta gateway y claves, se añade como
ampliación con nueva aprobación.

### 2. Stack de Compose en un proyecto propio con volúmenes nuevos

Se levanta con `COMPOSE_PROJECT_NAME=jup104-e2e`, definido en la consola y no en `.env`, con
`docker compose up --build --wait`. Así las imágenes salen de esta rama, las bases de datos empiezan
vacías y el proyecto por defecto de la máquina conserva sus volúmenes. Los puertos son los mismos,
de modo que el proyecto por defecto debe estar parado.

Al terminar, el proyecto se para sin borrar volúmenes, por si la revisión del PR pide repetir una
comprobación. Borrarlos después lo decide quien usa la máquina.

*Alternativas descartadas.* Reutilizar el proyecto por defecto: arrastra datos de pruebas anteriores
y no se puede saber qué había en el corpus. Borrar sus volúmenes: destruye datos que no son de esta
tarjeta. `pnpm dev`: no deja sirviendo backend ni processor sin configuración adicional (hallazgo
`RF-103-001`, registrado en el PR #75).

### 3. Datos del recorrido: los del smoke y el corpus versionado

- **Costes:** los que carga `local:smoke`, ejecutado **una sola vez**. En la pantalla principal se
  fijan a mano `2024-06-01` y `2024-06-21` con Core Finance, y se contrasta con Growth Ops, que debe
  mostrar ausencia de datos.
- **Documento:** `docs/assistant-corpus/finops/azure-finops-mvp.md` íntegro, enviado desde `/ingest`
  con Growth Ops seleccionado, origen `assistant-corpus` y la ruta del archivo como URI del
  artefacto.
- **Pregunta:** el caso `JUP-069-004` de `docs/validation/JUP-069-questions.json`, en una
  conversación nueva de Growth Ops; después, la misma pregunta en Core Finance.

Growth Ops no recibe nada del smoke, así que todo fragmento que el asistente devuelva allí procede
del documento del recorrido. En Core Finance el corpus solo contiene el fragmento `local-smoke`, lo
que da el contraste de aislamiento por ámbito.

*Alternativa descartada.* Ingerir en Core Finance: el fragmento del smoke puede aparecer entre los
tres que muestra la respuesta y la prueba deja de ser limpia. Inventar un documento y una pregunta:
el repositorio ya versiona unos, y son los que usará el ensayo de JUP-065.

### 4. El navegador lo conduce un guion, y hay además una pasada manual

"Navegador real" significa aquí Chromium iniciado sin ninguna opción que relaje la seguridad, con
un perfil vacío, que carga la interfaz desde `http://localhost:5173` y cuyas peticiones llegan al
backend por la red. El guion no intercepta ni responde peticiones y no escribe la sesión en el
almacenamiento: entra por el formulario de acceso.

El guion se ejecuta con Playwright desde un proyecto **fuera del repositorio**, lee la contraseña de
una variable de entorno y guarda fuera del repositorio sus capturas y resultados. Su texto se
versiona como receta en `docs/evidence/JUP-104-browser-recipe.md`, como hizo JUP-057. Además, quien
valida hace una pasada manual corta en su navegador habitual con la lista de pasos de la evidencia:
el guion aporta repetibilidad y la pasada manual, que el recorrido funciona fuera del navegador de
pruebas.

*Alternativas descartadas.* Solo manual: no es repetible y depende de la atención de quien lo hace.
Solo guion: deja sin cubrir el navegador que usa una persona. Guion con respuestas simuladas, como
la receta de JUP-057: sirve para una pantalla de demostración, no para un recorrido integrado.

### 5. La ingesta y el contexto se prueban fuera de la interfaz, con consultas de solo lectura

Para cada trabajo creado desde la interfaz se registra:

- su estado en `jobs` (CockroachDB), con la misma consulta que usa `local:smoke`, esperando a
  `completed` con un plazo de 120 s;
- en pgvector, la fila de `knowledge_documents` con ese identificador y ese ámbito, y el número de
  filas de `document_chunks` y `chunk_embeddings` asociadas;
- el evento `retrieval` del backend para la pregunta, con los identificadores de documento.

Las consultas se ejecutan con `docker compose exec` dentro de los contenedores y solo leen. Las
salidas se guardan sin cadenas de conexión ni contenido de documentos más allá del fragmento que ya
muestra la interfaz.

### 6. `RF-087-002` se comprueba, no se da por conocido

El recorrido envía un mensaje, recarga la página y vuelve a abrir la conversación.

- Si se muestran la pregunta y la respuesta, la fila pasa a `Fixed` citando el cambio de lectura que
  introdujo JUP-086 (PR #47) y la evidencia de esta tarjeta.
- Si falla, la fila conserva `Open` y se le añade la reproducción nueva, con el código de respuesta
  y el registro del backend.

En ambos casos se anota que ningún test contra la base de datos real cubre esa lectura.

### 7. Automatización: receta versionada ahora, CI en una tarjeta propia

Criterio 7 de la tarjeta. Se adopta la opción intermedia: el recorrido queda como guion repetible
versionado en la evidencia y ejecutado fuera del repositorio.

| Opción | Decisión | Motivo |
| --- | --- | --- |
| Manual documentado, sin guion | Descartada | No es repetible |
| Receta versionada, Playwright fuera del repositorio | **Adoptada** | Repetible sin añadir dependencias ni tocar CI; tiene precedente |
| Playwright como dependencia y job de CI | Fuera de esta tarjeta | Exige que CI levante CockroachDB, RabbitMQ y pgvector, que hoy no levanta (`RF-096-004`, `Open`), cambia el lockfile, `ci.yml` y su test, y sería una decisión duradera que pediría ADR |

Si tras ejecutarlo el guion resulta inestable, se dice en la evidencia y se revisa esta decisión en
la aprobación posterior a la revisión.

### 8. Sin código de producto y sin ciclo Red/Green

Esta tarjeta no añade ni cambia código ni pruebas, así que no hay ciclo Red/Green ni mutación; la
excepción se deja escrita en `review.md`. La tarjeta permite corregir fallos triviales del frontend,
pero aquí se renuncia a ello por defecto: el valor del registro es que describe `develop` tal cual.
Si aparece un fallo trivial que impida seguir, se para, se pide ampliar el alcance y la corrección
lleva su ciclo de pruebas.

### 9. Un fallo detiene el paso, no el recorrido

Cada paso se registra como acreditado, fallido o no ejecutado. Un fallo genera un hallazgo
`RF-104-NNN` con reproducción, resultado esperado y observado, y el recorrido continúa con los pasos
que no dependan de él. Los que sí dependan se marcan como no ejecutados, con el motivo. Si el fallo
contradice un requisito de la spec de esta tarjeta, el requisito no se rebaja: se decide en la
aprobación posterior a la revisión si se archiva con el hallazgo abierto o se ajusta.

### 10. El spike y el backlog se editan al final, con JUP-103 en `develop`

JUP-103 reescribe F4 del spike y le añade el punto 11, y añade filas al principio de la tabla del
backlog. Esta tarjeta toca las mismas zonas (F5 y el punto siguiente del spike; filas nuevas y
`RF-087-002` en el backlog). Para evitar un conflicto seguro, esos dos archivos se editan en el
último grupo de tareas, después de traer `develop` con el PR #75 fusionado. Si a esa altura no lo
está, se para y se decide con quien lidera JUP-103 si se espera o se asume el conflicto.

Mientras tanto, los hallazgos se redactan completos en la evidencia, de modo que pasarlos al backlog
sea copiar.

### 11. No aplica ADR

No se añade ninguna dependencia, no cambia ningún contrato y la decisión 7 no compromete al
repositorio más allá de esta evidencia. Haría falta un ADR, con nueva aprobación, si se optara por
añadir Playwright al repositorio o un job de navegador a CI; el siguiente número libre sería
`ADR-0019` (`ADR-0017` es el último en `develop` y el PR #73 reserva `ADR-0018`).

### 12. Las capturas quedan fuera del repositorio

`docs/evidence/` solo contiene texto y JSON. Las capturas del guion se guardan fuera y, si la
revisión las pide, se adjuntan en la conversación del PR. La evidencia describe lo observado con
texto: títulos, valores, mensajes y recuentos.

## Risks / Trade-offs

- **Con `mock` la prueba del asistente es débil** → Se compensa con el contraste entre ámbitos y con
  el evento `retrieval`, y se declara el límite en la evidencia (decisión 1).
- **El primer arranque con volúmenes nuevos tarda** (el processor migra durante unos minutos) →
  `up --wait` y el plazo del smoke lo cubren; no se usa `/assistant` hasta que el processor esté
  sano, para no confundir el resultado con `RF-096-002`.
- **El `.env` local es anterior a JUP-022 y JUP-023** → Se compara con `.env.example` solo por
  nombres de variable antes de arrancar; las que falten toman el valor por defecto de Compose.
- **`local:doctor` puede pasar y el backend no arrancar** (`RF-050-002`) → El criterio de entorno
  listo es `up --wait` más el smoke, no el diagnóstico.
- **El proyecto por defecto está levantado y ocupa los puertos** → Se comprueba antes; si lo está,
  se para sin borrar nada.
- **El guion puede fallar por tiempos y no por el producto** → Esperas por condición y no por
  tiempo fijo; un fallo se repite antes de registrarlo, y no se atribuye a la carga de la máquina
  sin descartar antes una carrera real.
- **`develop` avanza durante la tarjeta** → Si se fusiona un PR que cambia el chat o la pantalla
  principal, se reconstruye y se repite el paso afectado; el registro indica sobre qué commit se
  hizo cada paso.
- **La batería de pruebas completa no es determinista con los cuatro paquetes a la vez**
  (`RF-098-004`; `RF-103-005` en el PR #75) → Se ejecuta por mitades y se dice en la evidencia.
- **`local:test` falla con la infraestructura de Compose levantada** (`RF-103-004`, PR #75) → Se
  ejecuta antes de levantar el stack.
- **Los enlaces relativos de estos artefactos cambian al archivar** → Se corrigen en el mismo paso
  del archivado, porque la carpeta baja un nivel.

## Open Questions

- ¿Cuenta este registro como parte del ensayo de JUP-065? No cambia las tareas: se pregunta a quien
  lidera JUP-065 y la respuesta se anota en la evidencia.
