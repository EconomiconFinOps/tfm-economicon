# Evidencia JUP-087 — Calidad minima del frontend

- Fecha: 2026-09-08.
- Trello: https://trello.com/c/JHcidwiR
- Rama: `chore/JUP-087-frontend-quality-baseline`.
- Base: `origin/develop` en `ae538aadbf8012c144d540644691a9d80a5a4508`.
- OpenSpec: [jup-087-frontend-quality-baseline](../../openspec/changes/jup-087-frontend-quality-baseline/proposal.md).
- Pull request: https://github.com/EconomiconFinOps/tfm-economicon/pull/29
- Commit de implementacion: `fbb1e55d6d8be95899236d525075329393d9ac24`.
- CI de implementacion: https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/34260957444

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
