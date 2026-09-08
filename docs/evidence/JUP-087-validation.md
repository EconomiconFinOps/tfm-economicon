# Evidencia JUP-087 — Calidad minima del frontend

- Fecha: 2026-09-08.
- Trello: https://trello.com/c/JHcidwiR
- Rama: `chore/JUP-087-frontend-quality-baseline`.
- Base: `origin/develop` en `ae538aadbf8012c144d540644691a9d80a5a4508`.
- OpenSpec: [jup-087-frontend-quality-baseline](../../openspec/changes/jup-087-frontend-quality-baseline/proposal.md).

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
