# Evidencia JUP-087 — Calidad minima del frontend

- Fecha: 2026-09-08.
- Trello: https://trello.com/c/JHcidwiR
- Rama: `chore/JUP-087-frontend-quality-baseline`.
- Base: `origin/develop` en `ae538aadbf8012c144d540644691a9d80a5a4508`.
- OpenSpec: [jup-087-frontend-quality-baseline](../../openspec/changes/archive/2026-09-14-jup-087-frontend-quality-baseline/proposal.md).
- Pull request: https://github.com/EconomiconFinOps/tfm-economicon/pull/29
- Commit de implementacion: `fbb1e55d6d8be95899236d525075329393d9ac24`.
- CI de implementacion: https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/34260957444

## Estado de cierre — 2026-09-14

La implementacion esta integrada en `develop` desde el 12/09 mediante la
[PR #29](https://github.com/EconomiconFinOps/tfm-economicon/pull/29), aprobada
y fusionada por Lucia. Esta actualizacion documenta la validacion operativa
delegada, archiva el cambio y consolida su especificacion. El cierre se limita
al baseline de calidad del frontend: el ensayo integrado detecta dos defectos
heredados que permanecen abiertos en JUP-085 y JUP-035. No acredita un producto
completo sin fallos ni una validacion personal de Paris.

Los apartados fechados del 08 al 10/09 conservan su contexto historico. El
estado actual, las participaciones y las limitaciones constan al final.

## Resultado

El baseline tenia 49 errores `react/prop-types` en nueve JSX y un script de
pruebas que solo imprimia un mensaje. Los componentes existentes, hooks y
cliente HTTP pasan a TypeScript estricto siguiendo ADR-0003. Las props tienen
contratos explicitos y las respuestas/payloads reflejan los schemas del backend.
JSX sigue sujeto a `react/prop-types`; dos pruebas ejecutan ESLint para verificar
que rechaza props JavaScript sin contrato y acepta props TypeScript tipadas.

`pnpm test` ejecuta Vitest con React Testing Library y jsdom. Cada montaje usa
un QueryClient nuevo; la suite limpia DOM, storage, mocks y cache. Los handlers
HTTP usan datos sinteticos y rechazan solicitudes no previstas. Los tests
tienen su propio proyecto TypeScript para mantener los globals Node fuera
del codigo de navegador. No se añaden dependencias de produccion ni se cambian
las versiones existentes de React, Vite o sus dependencias en el lockfile.

## Matriz de regresion

| Recorrido | Exito | Fallo y recuperacion |
|---|---|---|
| Login/sesion | Credenciales, estado pendiente, persistencia, recarga y logout que limpia cache/storage | Credenciales rechazadas, fallo de red, reintento y sesion persistida invalida |
| Tenant | Carga, seleccion valida, persistencia y cabeceras de contexto | Lista vacia, fallo de autorizacion y Reset session |
| Dashboard | Salud y resumen de costes del tenant, estado de carga | Error visible sin desmontar la aplicacion |
| Ingesta | Payload con tenant coherente y confirmacion del job encolado | Rechazo visible, documento conservado para reintentar |
| Conversaciones | Lista, creacion, historial, envio, respuesta y estados pendientes | Fallos al listar, cargar, crear o enviar; borradores disponibles para reintentar |
| Cambio de tenant | Contexto nuevo y estado de pagina independiente | No combinar ID de conversacion antiguo con cabecera nueva ni aplicar respuestas tardias al formulario actual |

La validacion detecto y corrigio fallos heredados: sesiones JSON con estructura
invalida, dashboard sin datos disponibles y errores de lista/detalle de
conversaciones que no se mostraban. Las paginas de ingesta y conversaciones
reinician sus estados al cambiar de tenant. Las operaciones ya enviadas pueden
terminar para su tenant original; el cambio no pretende cancelarlas en el servidor.

## Puerta de CI

El check obligatorio `Frontend build` ejecuta lint, pruebas y build, en ese
orden, sin `continue-on-error`. `Frontend type check` comprueba aplicacion,
configuracion y tests. Se conservan los siete nombres de checks existentes.

Se verifico la nueva prueba de gobernanza primero contra el workflow anterior:
fallo 1/8 por no exigir lint/pruebas. Tras conectar los pasos obligatorios,
la suite paso 8/8. Los tests de props tambien comprueban el diagnostico real
`react/prop-types`, no solo el texto de una configuracion.
Las siete regresiones de cambio de tenant tambien se ejecutaron antes de la
correccion: 7/7 fallaban. Tras aislar el montaje por tenant, 7/7 pasan.

## Validacion local

| Comprobacion | Resultado |
|---|---|
| `corepack pnpm install --frozen-lockfile` | Correcto |
| `corepack pnpm lint` | Correcto; frontend con cero errores |
| `corepack pnpm build` | Correcto en los cuatro paquetes ejecutables |
| `corepack pnpm --filter @finops/frontend typecheck` | Correcto en aplicacion, configuracion y tests |
| `corepack pnpm test --filter=@finops/frontend` | 28/28 pruebas reales de recorridos y contratos |
| `node --test tools/*.test.mjs` | 56/56 |
| `python -m unittest discover -s tools/collaboration/tests -v` | 12/12 |
| `corepack pnpm openspec:validate` | 25/25 |
| `corepack pnpm jup:check:all` | 13 cambios activos correctos |
| `corepack pnpm jup:cleanup:check` | Sin archivos prohibidos, incluidos los nuevos no ignorados |
| `corepack pnpm assistant-corpus:validate` | Manifiesto valido |

En Chromium se ejecuto ademas login, cambio de tenant, dashboard, ingesta,
creacion/envio de conversacion y logout a 1440 x 1000, con HTTP interceptado:
los seis recorridos pasaron y no hubo errores JavaScript ni de consola. Se
verifico que el logout borra sesion y tenant. La captura es evidencia local;
la suite versionada constituye la reproduccion automatizada del contrato.

En este Windows, Turborepo encontraba un pnpm 11 ajeno al workspace. Los
comandos locales se ejecutaron con un wrapper temporal externo al repositorio
que dirige pnpm a Corepack y a la version 9 declarada por el proyecto. La
instalacion congelada no altera el lockfile. El intento de ejecutar todos los
tests Python mediante `pnpm test` encontro un entorno sin `fastapi`; las tres
suites de servicios se verifican en CI con sus `requirements-dev.txt`, sin
presentar ese intento local como una validacion satisfactoria.

## Validacion remota

El CI del commit de implementacion termino con los siete checks obligatorios
en verde: JUP policy, OpenSpec, las tres suites Python, Frontend build y
Frontend type check. Dentro de Frontend build se confirmo la ejecucion correcta
de lint, las 28 pruebas y el empaquetado. La descripcion de la PR enlaza ademas
la ejecucion del ultimo head tras incorporar esta evidencia documental.
Las suites Python registraron 58 pruebas aprobadas en azure-cost-api, 24 en
backend y 152 en processor; processor omite 34 pruebas en ese entorno de CI.
Esas omisiones no se presentan como pruebas ejecutadas.

## Alcance y revision

RF-082-002 queda corregido por codigo y pruebas en esta rama. RF-083-002
conserva el residual visual/funcional de JUP-035; JUP-095 puede reutilizar el
runner al portar Figma. `allowJs` permanece hasta F5 segun ADR-0003. JUP-087
no cambia el consumo de `/me`, la expiracion/autorizacion de JUP-085/086,
el Docker reproducible pendiente ni los providers mock de RAG/billing.

La revision automatizada independiente contrasto los contratos con los schemas
backend y la configuracion de CI. La tarjeta permanece en revision hasta la
aprobacion humana y la evidencia atribuible de sus roles; esta validacion no
declara pairing ni participacion humana realizados. Los checks y su ejecucion
remota final se enlazan desde la descripcion de la PR de esta rama.

## Revalidacion contra develop — 2026-09-09

- Base integrada: `7d76fc376e0eca1aac6401304977575a2f92ceb5`, con JUP-049
  (PR #16, contenedores) y JUP-024 (PR #18, guardrails del agente).
- Head anterior: `ddbc68930afc81d0690bb776e072adf8532d8514`. Se incorpora la
  base mediante merge, conservando el historial publicado de la PR #29.
- El unico conflicto textual estaba en `apps/frontend/package.json`.
  Se conservan lint, Vitest, typecheck y dependencias de JUP-087, junto al
  comando Docker de JUP-049 que usa la raiz del workspace como contexto.
- CI mantiene lint y pruebas dentro de `Frontend build` e incorpora
  `docker:validate`. Dockerfile, Compose y processor coinciden con `develop`;
  el codigo, las 28 pruebas y el lockfile de JUP-087 permanecen intactos.
- La mencion previa al Docker pendiente corresponde al baseline del 08/09;
  esta integracion incorpora el trabajo de JUP-049 y su build reproducible.

| Validacion del resultado integrado | Resultado |
|---|---|
| Instalacion con lockfile congelado | Correcta, sin cambios en dependencias |
| Lint del workspace | Cero errores |
| Frontend | 28/28 pruebas; build y typecheck correctos |
| Herramientas del repositorio, incluida topologia Docker | 64/64 |
| Puente de colaboracion con clientes simulados | 12/12 |
| OpenSpec estricto | 27/27 |
| Trazabilidad / higiene / corpus | 15 cambios, 475 archivos y manifiesto correctos |
| Revision independiente de la integracion | Sin hallazgos introducidos por el merge |

La imagen frontend se construyo con el Dockerfile versionado y contexto raiz
del workspace: Docker Engine 29.6.2, Node 20.20.2, pnpm 9.0.0, Vite 5.4.21 y
Vitest 3.2.7. El contenedor exclusivo alcanzo `healthy` con usuario `node`
(UID 1000), raiz de solo lectura, `/tmp` en tmpfs, `no-new-privileges` e init.
No se publicaron puertos. La pagina y sus assets JS/CSS respondieron HTTP 200.

El preview arranco con la configuracion copiada a `/tmp`; se comprobo tambien
la resolucion y carga real de `vitest/config` desde esa ruta. No hubo errores
de ejecucion; solo el aviso heredado de deprecacion de la API CJS de Vite.
El contenedor y la imagen exclusivos de prueba se retiraron al finalizar.
Logs y harness locales: `materiales/07-evidencias/jup087-reconciliation-20260909/`,
fuera del repositorio. Esta prueba valida el frontend empaquetado, sin repetir
los recorridos contra un backend real ni las suites de integracion de servicios.

Los siete checks remotos se ejecutan de nuevo al publicar el resultado. Su
ejecucion queda enlazada en la descripcion de la PR y en Trello. Se mantiene
la solicitud de revision a Lucia; la actualizacion no acredita aprobacion ni
validacion humana y no fusiona la PR hacia `develop`.

## Comprobacion de cierre y revalidacion — 2026-09-10

La PR #29 seguia sin revisiones ni comentarios de aprobacion, y Trello no
registraba validacion nueva de Paris. La solicitud a Lucia (`lmatsan`) se
conserva. La [Definition of Done](https://trello.com/c/6l0Jan5Q) requiere PR
revisado, validacion funcional registrada y archivo/promocion OpenSpec, o una
excepcion documentada. Por tanto, JUP-087 permanece en revision y este cambio
no acredita cierre humano ni fusion de la PR.

Se integra `develop` en `1ff8e071f83a58f630c496740d712e8c0e2cc443` sobre el
head anterior `1f2d80912309ab699b06894128ab4bbf13b27222`, conservando el
historial publicado. La base incorpora JUP-044, los cierres de JUP-024/049 y
JUP-053. El conflicto en el backlog se resuelve preservando todos los hallazgos
RF-053 y el estado corregido de RF-082-002. RF-053-004 sigue abierto y asignado
a JUP-020; las pruebas frontend con HTTP simulado no acreditan una ingesta real
completa y no cierran ese defecto heredado del backend/processor.

El login TypeScript conserva la contraseña inicialmente vacia de JUP-053.
Las pruebas verifican ese estado y escriben una contraseña sintetica antes de
simular rechazo/reintento. El test de topologia que inspeccionaba `LoginPage.jsx`
fallaba con ENOENT tras el rename; ahora inspecciona `LoginPage.tsx`, manteniendo
sus aserciones. Se registro el fallo previo (26/27) y el resultado corregido
(27/27). Los contratos HTTP y las medidas de secretos de `develop` se conservan.

La primera prueba que carga los plugins ESLint tardo 10,7 segundos en este
Windows y supero el limite de cinco segundos. Su limite individual pasa a
30 segundos; mantiene el diagnostico exigido `react/prop-types` y no modifica
las aserciones ni los limites del resto de la suite. La repeticion paso 28/28.

| Comprobacion | Resultado |
|---|---|
| Instalacion con lockfile congelado | Correcta, sin cambios en dependencias |
| Lint del workspace y frontend | Cero errores |
| Suite frontend | 28/28 |
| Build y typecheck frontend | Correctos |
| Herramientas del repositorio, incluida topologia/secretos | 83/83 |
| Puente de colaboracion con clientes simulados | 12/12 |
| OpenSpec estricto | 29/29 |
| Trazabilidad / higiene / corpus | 12 cambios, 507 archivos y manifiesto correctos |
| Revision independiente del delta | Sin hallazgos pendientes |

El resultado de build, typecheck y las tres suites Python se contrasta tambien
en los siete checks del nuevo head, enlazados desde la PR y Trello. La prueba
Docker del apartado anterior corresponde al 09/09; no se presenta como una
ejecucion nueva del stack con secretos externos.

## Validacion operativa delegada y cierre acotado — 2026-09-14

### Autorizacion, roles y auditoria

El usuario autoriza expresamente ejecutar la validacion en esta tarea para
cerrar JUP-087, conservando el rol y la auditoria de Paris. La ejecucion que
sigue es automatizada, realizada por el asistente bajo esa autorizacion y
publicada mediante `Iber1to`; no es una ejecucion manual atribuible a Paris
ni demuestra pairing o coautoria. La sustitucion afecta a esta ejecucion
operativa, no a la asignacion del rol.

| Rol previsto, conservado | Persona | Evidencia actual |
|---|---|---|
| Liderazgo | Victor Mendez | Se conserva la asignacion; no se infiere una actividad adicional. |
| Pairing/coautoria | Alejandro Aguado (`Iber1to`) | Implementacion/publicacion en la PR #29; no consta pairing explicito. |
| Revision de PR | Lucia Mateo (`lmatsan`) | [APPROVED del 12/09 a las 15:45:23 UTC](https://github.com/EconomiconFinOps/tfm-economicon/pull/29#pullrequestreview-5186996159), sobre `746fd5dce2e3ef75c760f5095beda64af25fee3a`. |
| Validacion, pruebas y documentacion; auditoria | Paris Arcos Martin (`ParisArcos`) | Rol conservado. Su auditoria personal sigue pendiente; no se marca como realizada ni como aprobacion. |

Lucia fusiono la PR #29 el 12/09 a las 15:47:38 UTC, squash
[`1de7b1663c52050b9f27e6f46fe02d5c077d800b`](https://github.com/EconomiconFinOps/tfm-economicon/commit/1de7b1663c52050b9f27e6f46fe02d5c077d800b),
y movio [Trello](https://trello.com/c/JHcidwiR) a **70 — Hecho** a las
15:50:26 UTC. Su revision ya distinguia la validacion pendiente de Paris.
Los [siete checks de la implementacion](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/34509261904)
son satisfactorios. Esa aprobacion pertenece a la PR #29 y no se transfiere
a la PR documental de cierre.

La excepcion documentada a la [Definition of Done](https://trello.com/c/6l0Jan5Q)
consiste en aceptar esta ejecucion operativa delegada, manteniendo abierta
la auditoria personal de Paris. No elimina los requisitos de revision de
GitHub ni declara satisfechos los recorridos integrados fallidos. Paris puede
contrastar los resultados y registrar hallazgos posteriores sin perder su rol.

### Base y comprobaciones

Base ejecutada: `develop` en
`cfc6668bceb60c38045f72976b9de8e8b8337555`, que incluye JUP-087 y la
[correccion del contrato de ingesta de JUP-020, PR #34](https://github.com/EconomiconFinOps/tfm-economicon/pull/34).
Las menciones anteriores a RF-053-004 abierto corresponden a su fecha:
esa correccion esta integrada desde el 13/09; el alcance completo de JUP-020
sigue siendo independiente.

| Comprobacion ejecutada | Resultado |
|---|---|
| Instalacion con lockfile congelado | Correcta, sin modificar dependencias. |
| Lint del workspace | Correcto; cero errores frontend. |
| Suite frontend mediante el comando raiz filtrado | 28/28 en cinco archivos, incluidos errores, recuperacion, aislamiento por tenant y contratos reales de ESLint. |
| Typecheck frontend | Aplicacion, configuracion y tests correctos. |
| Build del workspace | Cuatro tareas satisfactorias; Azure Cost API reutiliza cache, el resto se ejecuta. |
| Herramientas del repositorio | 83/83. |
| Puente de colaboracion, clientes simulados | 12/12. |
| OpenSpec estricto tras archivo/promocion | 30/30; cuatro requisitos promovidos sin cambiar su contrato. |
| Trazabilidad, higiene y corpus | 12 cambios activos enlazados, 524 archivos sin elementos prohibidos y manifiesto valido. |
| Revision automatizada independiente del cierre | Sin hallazgos materiales en atribucion, alcance, enlaces, promocion y evidencia sanitizada; no constituye aprobacion humana de GitHub. |

Se conserva el wrapper externo de pnpm 9 para la resolucion local de Turbo.
No se presenta `compileall` como una suite Python: las suites de servicios
pertenecen al CI enlazado. No se amplian las omisiones conocidas de ese CI.

### Ensayo con navegador y servicios reales

Se construyen frontend, backend y processor desde sus Dockerfiles canonicos
en un proyecto Docker exclusivo, con CockroachDB, RabbitMQ y pgvector vacios,
secretos efimeros externos y operador sintetico con dos tenants. Se arranca
backend antes de processor para evitar la carrera conocida de JUP-096; esto
no corrige esa carrera. Los seis servicios base y el proxy de prueba alcanzan
`healthy`. Azure Cost API y monitorizacion no forman parte de este ensayo.

La configuracion entre puertos falla el preflight CORS: `OPTIONS /auth/login`
devuelve 405 y no incluye `Access-Control-Allow-Origin`. Para continuar se
construye el frontend con `VITE_API_BASE_URL=/api` y se añade un proxy de
prueba de mismo origen. No se modifica el producto ni se declara corregida
su configuracion canonica. Chromium usa 1440 x 1000 y servicios reales;
solo los errores 503 especificados abajo se inyectan deliberadamente.

| Recorrido observado | Resultado y procedencia |
|---|---|
| Login/sesion | Password inicial vacia; rechazo HTTP 401 real sin crear sesion; login real, recarga, persistencia y logout correctos. Sesion persistida malformada se elimina sin fallo JavaScript. |
| Tenant/dashboard | Dos tenants reales, seleccion persistida y dashboard real. Fallos 503 controlados muestran el error; dashboard se recupera y bootstrap permite `Reset session`. El resumen economico conserva sus cifras mock heredadas. |
| Ingesta | Rechazo 422 real con texto vacio; reintento HTTP 202 con documento sintetico. Job `17898355-5bed-4836-94f1-0a0ccc4fc060` termina `completed` para `tenant-growth`: un documento, un chunk y un embedding de dimension 8 persistidos. Cambio de tenant limpia borrador y confirmacion anterior. |
| Conversaciones | Listado y creacion reales; 503 controlados al listar/enviar visibles, borrador conservado tras rechazo y estado aislado entre tenants. POST de mensaje devuelve 201 y persiste ambos mensajes. |
| Historial real tras responder | **FALLA**: GET del detalle devuelve 500 porque `fetch_messages` intenta `json.loads()` sobre metadata JSONB que psycopg ya entrega como `dict`. Se reproduce sin proxy. La interfaz muestra el error y permanece operativa. La visualizacion/persistencia del historial completo no queda validada. |
| Aislamiento adicional | El mismo detalle pedido con el tenant incorrecto devuelve 404; no se muestran conversaciones ni borradores del otro tenant. |

El primer recorrido registra siete comprobaciones satisfactorias y una fallida
(historial). El seguimiento registra otras seis comprobaciones satisfactorias,
incluida la presentacion del error real; no convierte el recorrido fallido en
un exito. No se observan errores JavaScript. Los errores HTTP de consola
incluyen los rechazos previstos, los 503 controlados, un favicon 404 y el
500 real: no se afirma una consola sin errores.

Embeddings y respuesta del asistente usan providers mock; se validan HTTP,
colas, persistencia y manejo de interfaz, no calidad RAG/LLM ni facturacion
real. La respuesta del asistente existe en base de datos, pero no llega al
historial visible por el defecto descrito.

Los resultados sanitizados estan versionados en
[JUP-087-runtime-validation.json](JUP-087-runtime-validation.json).
Capturas, harness y logs complementarios quedan fuera del repositorio en
`materiales/07-evidencias/jup087-validation-20260914/`. No se versionan
credenciales, tokens, volumenes ni entornos generados.

### Residuales y archivo

- **RF-087-001 / JUP-085:** definir y verificar conexion browser/API entre
  origenes o un proxy soportado; reproducir preflight y login real.
- **RF-087-002 / JUP-035:** normalizar metadata JSONB del historial y comprobar
  envio seguido de lectura/recarga con CockroachDB real. La linea defectuosa
  procede del commit `4aee5d78` del 14/06, anterior a JUP-087. No se corrige aqui.
- JUP-054 conserva el seguimiento de pruebas integradas; JUP-096 conserva la
  carrera entre servicios. RF-083-002 y los providers mock tampoco se cierran.

Los cuatro requisitos de JUP-087 quedan acreditados por lint, runner real,
matriz positiva/de error y aislamiento de la suite. Se archiva el cambio en
`openspec/changes/archive/2026-09-14-jup-087-frontend-quality-baseline/` y se
promueve `openspec/specs/frontend-quality-baseline/spec.md`, sin ampliar sus
garantias al backend completo. El archivo se prepara en la PR documental;
su incorporacion a `develop` requiere la aprobacion propia de esa PR.
