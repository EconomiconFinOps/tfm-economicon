# Evidencia De Validacion JUP-053

## Estado Actual Tras QA

- Revision tecnica de JUP-053 **PASS en alcance**: RF-053-001/002/003
  verificados Fixed mediante pruebas y probes independientes.
- QA ejecutada: controles acotados conformes; dictamen global
  **QA_FAIL / NEEDS_HUMAN**. RF-053-004 sigue Open, preexistente y fuera del
  alcance. El 2026-09-10 Paris Arcos acordo su correccion en JUP-020;
  pendiente reevaluar QA tras esa decision, sin cambiar el dictamen observado.
- **Smoke completo FAIL**, no se dispensa el fallo de ingesta. No hay
  aprobacion final ni autorizacion de publicacion.
- El resto de este documento conserva la evidencia historica de Green2;
  los resultados actuales de Green3/Mutation2 se recogen a continuacion.

### Seguimiento RF-053-004: JUP-020

Decision de Paris Arcos registrada el 2026-09-10 a las 09:14 UTC:
corregir la incompatibilidad payload/text_content en JUP-020 y añadir la
referencia al finding en su tarjeta privada. Se reutiliza RF-053-004;
su identificador conserva el origen en JUP-053, no la JUP de correccion.
Estado Open/High. No se ha implementado ni probado la correccion funcional.

Registro: [finding](../../openspec/findings/backlog.md) y
[decision completa](../../openspec/changes/jup-053-secure-runtime-secrets/review.md#decision-sobre-rf-053-004).
Seguimiento privado actualizado y releido el 2026-09-10 a las 09:16 UTC:
https://trello.com/c/1Y9HVCQs. Descripcion anterior de 1718 caracteres
conservada integra, mas nota de 289: total 2007 caracteres. Coincidencia exacta
de descripcion verificada; nombre, lista Backlog, posicion, etiquetas,
miembros, comentarios, fechas de entrega y estados sin cambios.
Tarjeta oficial: https://trello.com/c/Mi3kPCOD, sin modificar; replica manual
pendiente. El finding permanece local, sin commit ni URL GitHub publicada.
Esta accion no constituye aprobacion post-QA ni cierre de JUP-053.

Validaciones de esta actualizacion documental desde el worktree JUP-053:
`corepack pnpm openspec:validate` (28 items), `node tools/jup-check.mjs --all`
(16 cambios), `node tools/jup-cleanup-check.mjs` (480 rutas) y
`git diff --check`, todos exit 0. El primer intento de OpenSpec fallo por
EPERM al acceder a la cache de pnpm; se repitio con permiso de acceso y paso.
No se ejecutaron nuevas pruebas funcionales ni se modificaron codigo o tests.

### Auditoria QA

QA read-only reejecuto 448 casos (113 backend, 254 processor, 81 Node)
y contrasto 104 anteriores (34 Cockroach, 58 Azure, 12 colaboracion).
Total sin duplicados: 552 casos, 192 nuevos. Backend conserva 11 warnings;
processor omite sus 34 casos condicionales en esta ejecucion y reutiliza
el resultado real anterior. Entorno sintetico, sin opt-in de integracion,
bytecode y cache pytest desactivados; basetemps comprobados ausentes:

```powershell
& "$run/test-venv/Scripts/python.exe" -B -m pytest tests -q --tb=short --basetemp "$run/qa-1-backend-2db003c7dfda4969a9bf9be7c9ab2049"
& "$run/test-venv/Scripts/python.exe" -B -m pytest tests -q --tb=short --basetemp "$run/qa-1-processor-149e5b2372684196b874b465a7431e01"
node --test tools/docker-topology.test.mjs tools/llm-gateway-config.test.mjs tools/jup-check.test.mjs tools/jup-cleanup-check.test.mjs tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/delivery-roadmap.test.mjs tools/repository-governance.test.mjs tools/assistant-corpus.test.mjs
```

Pytest desde cada servicio; Node desde la raiz. Los tres comandos exit 0.
QA tambien reejecuto OpenSpec 28, trazabilidad individual y global de 16
cambios, higiene 480, validacion de corpus, frontend typecheck y diff check,
todos exit 0. Lint exit 1: mismos 49 errores, cero warnings.
Build frontend se contrasta contra Green2 porque sus fuentes no cambiaron;
no se afirma una reconstruccion en QA. Se comprobaron 31 destinos locales
Markdown en 15 archivos, sin rotos; anchors y URLs externas quedan fuera.
Las salidas se observaron en la sesion QA, sin crear nuevos logs en el repo.

QA inspecciono los 22 logs de mutation, informes y scripts de imagenes,
bundle, contextos y smoke. Coinciden los hashes de 476 entradas sin cambios
del manifiesto, incluidas 209 Markdown; las cuatro diferencias eran la
sincronizacion documental declarada.
El guard qa-1 paso sin cambios ni violaciones; ningun valor .env leido.

Dieciseis de los 17 escenarios tienen evidencia acotada automatizada o
inspeccion. Rotacion conserva **prueba runtime parcial**: demo/JWT si,
DB/broker/gateway solo procedimientos revisados, no rotaciones ejecutadas.
No se afirma validacion universal, despliegue productivo ni TLS/proveedor real.

El chequeo local DoD Stage qa paso los prerequisitos registrados; no prueba
aceptacion final. Stage final fallo (exit 20) antes del registro del dictamen,
por los eventos QA/guard/post-QA aun no registrados. El guard se registra
despues como PASS y QA como FAIL; la aprobacion humana continua pendiente.
La decision del 2026-09-10 asigna la correccion de RF-053-004 a JUP-020;
la reevaluacion de readiness sigue pendiente. No se interpreta esa asignacion
como correccion, dispensa del smoke fallido ni aprobacion post-QA.

### Green3 Y Regresiones De Review

Review 1 origino 55 pruebas adicionales: 44 fallos de validacion efectiva
de DSN, seis fugas en claves de JSON y un fallo de diagnostico, mas cuatro
controles validos. Logs `review-red-2-*-{baseline,red}.txt`.
Los cambios de producto se limitaron a ambos runtime_secrets.py,
processor/tasks/ingest.py y la explicacion de opciones query del manual.

| Verificacion actual | Resultado | Exit |
| --- | --- | --- |
| Backend completo, pytest tests | 113 passed | 0 |
| Processor completo, pytest tests | 254 passed, 34 skipped condicionales | 0 |
| Cockroach real, las mismas 34 condicionales | 34 passed, 22.34 s | 0 |
| Topologia / gateway | 26 / 6 passed | 0 |
| Suma con suites no modificadas descritas abajo | **552 pruebas distintas, 192 nuevas** | 0 por suite |

Comandos completos y basetemps unicos en `green-3-*.txt`.
El comando Cockroach conserva el DSN loopback y seleccion de tests mostrados
abajo, con basetemp `$run/green3-real-crdb-1`. Nodo exclusivo de memoria
`7207f07ae78bbda33b6599274ee292e35e80c018653ebaa410eed6a3cba54878`,
marcado, validado y eliminado por ID/etiquetas tras terminar.
Frontend, Azure y tooling sin cambios reutilizan resultados anteriores,
sin afirmar que se reejecutaron en Green3. Lint sigue en 49 errores.

### Mutation2 E Imagenes Actuales

Con el mismo Python 3.12 y nuevas copias/basetemps temporales:

```powershell
& "$run/test-venv/Scripts/python.exe" "$run/verify_mutation_2.py"
& "$run/test-venv/Scripts/python.exe" "$run/verify_images_2.py"
& "$run/test-venv/Scripts/python.exe" "$run/verify_contexts_2.py"
& "$run/test-venv/Scripts/python.exe" "$run/verify_bundle_2.py"
& "$run/test-venv/Scripts/python.exe" "$run/verify_smoke_2.py"
```

Los primeros cuatro comandos terminan exit 0; smoke exit 1 por RF-053-004.
Mutation2 repite los seis mutantes historicos y agrega cinco:

| Mutante nuevo | Baseline pass | Mutante fail / pass |
| --- | --- | --- |
| Query override backend | 24 | 22 / 2 |
| Query override processor | 24 | 22 / 2 |
| Claves secretas backend | 3 | 3 / 0 |
| Claves secretas processor | 3 | 3 / 0 |
| Perdida de causa original processor | 1 | 1 / 0 |

Total dirigido **11/11 detectados**: 80 passes de baseline; 63 fallos
significativos y 17 passes en mutantes. Todos los baselines exit 0 y todos
los mutantes exit 1, sin errores setup/import. No sumarlos a los 552 tests.
Los 480 hashes de fuente permanecieron identicos. Resultados/comandos en
`mutation-2-verification/mutation-results.json`.

Se construyeron de nuevo las cuatro imagenes reales; 42 capas/configs,
tres archivos reales de bundle y tres probes de contexto sin sentinelas,
con controles positivos. Treinta fixtures dotenv sinteticas excluidas.
Los contenedores del smoke usaron exactamente estas imagenes:

| Aplicacion | SHA-256 de imagen |
| --- | --- |
| Backend | bc5c31ebf41e3d8ac9773ae8156f20ccb1fb36ad384b388eb39304962eabbba1 |
| Processor | 2c13302c026104989e04e9b0305e8c10a90385d54b4d66a10dd24c2880303d07 |
| Frontend | 64ccdb02812cd97cec951b8051299dd43a8f7e1d945164a311fde791c2d6f9ab |
| Azure simulador | 2a105dd878834cd142040d3f9eb3656070d10bc4765abcd1760d2015f237d693 |

Comandos e informes en `acceptance-2-verification/`:
`commands.json`, `image-results.json`, scans por capas/contexto/bundle.
Scan de 480 rutas, cinco patrones con controles positivos; seis rutas
clasificadas como fixtures, denylist o specs. Mismos limites del scan
historico; no almacenes reales, historial ni deteccion universal.

Smoke actual: once comprobaciones PASS, incluyendo aislamiento/health,
16 rechazos de input requerido, preservacion de seed, rotacion demo/JWT
y conservacion completa de Grafana sintetica. Login 200, ingesta 202 y job
failed; ahora el diagnostico saneado conserva KeyError/text_content.
**El resultado global permanece FAIL**. Evidencia exacta en
`acceptance-2-verification/smoke-attempt-1/{smoke-results,smoke-commands}.json`.
Se verificaron y eliminaron los nueve contenedores, cuatro volumenes y red
propios de `jup053-smoke-f127816ad9`. Ningun contenedor sigue ejecutandose.
No se toco .env real ni se cambiaron password, cuenta o volumen compartidos.

Review 2 contrasto los 480 hashes y los informes, ejecuto probes sinteticos
sin conexiones y confirmo las tres correcciones, sin hallazgos nuevos en
el delta de remediacion. Guard read-only PASS; sync de evidencia posterior
solo documental, no invalida las imagenes de producto comprobadas.

## Contexto

- Fecha: 2026-09-09. Las secciones siguientes conservan el registro historico
  tras revision tecnica 1; no sustituyen el estado actual anterior.
- Trello oficial: https://trello.com/c/2UCJTDhi
- [Cambio OpenSpec](../../openspec/changes/jup-053-secure-runtime-secrets/proposal.md)
  y [revision](../../openspec/changes/jup-053-secure-runtime-secrets/review.md).
- Rama `feat/JUP-053-secure-runtime-secrets`, base
  `7d76fc376e0eca1aac6401304977575a2f92ceb5`; cambios sin commit.
- Python 3.12.13, Node 24.17, pnpm 9.0.0, Docker Engine 28.0.4.
- Artefactos temporales locales fuera del repositorio:
  `%TEMP%/codex-openspec-harness/c9f016c65661a7bb/jup053-secure-runtime-secrets-20260909`
  (en los comandos siguientes, `$run`). No contienen credenciales reales
  para las pruebas; no se versiona el harness personal.

## Pruebas Hasta Green2

Desde cada servicio, con el Python 3.12 de `$run/test-venv/Scripts/python.exe`,
`PYTHONDONTWRITEBYTECODE=1`, `PYTEST_ADDOPTS=-p no:cacheprovider`,
entorno de prueba sintetico y basetemp nuevo comprobado antes de ejecutar:

```powershell
& "$run/test-venv/Scripts/python.exe" -m pytest tests -q --tb=short --basetemp <directorio-nuevo>
```

| Suite / comando | Resultado | Exit |
| --- | --- | --- |
| Backend pytest | 86 passed | 0 |
| Processor pytest, sin opt-in de integracion | 226 passed, 34 skipped | 0 |
| Processor, test_azure_cost_cockroach_integration.py | Las mismas 34 skipped: 34 passed, 123.77 s | 0 |
| Azure Cost API pytest, Python 3.12 con requirements-dev existentes | 58 passed, dos warnings de dependencias | 0 |
| node --test tools/docker-topology.test.mjs | 26 passed | 0 |
| node --test tools/llm-gateway-config.test.mjs | 6 passed | 0 |
| node --test tools/jup-check.test.mjs tools/jup-cleanup-check.test.mjs tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/delivery-roadmap.test.mjs tools/repository-governance.test.mjs | 41 passed | 0 |
| node --test tools/assistant-corpus.test.mjs | 8 passed | 0 |
| python -B -m unittest discover -s tools/collaboration/tests -v | 12 passed | 0 |

Total agregado: **497 pruebas distintas aprobadas**, de ellas **137 nuevas**.
No contar las 34 de Cockroach dos veces, los reruns, los mutantes ni los 17
escenarios como pruebas adicionales. Las 58 de Azure se ejecutaron antes de
Green2; sus fuentes no cambiaron. Las suites se ejecutaron por separado.
Los warnings de fixtures SQLite y claves JWT sinteticas se conservan.

Comando real DB desde apps/processor:

```powershell
$env:PROCESSOR_COCKROACH_TEST_URL='cockroachdb+psycopg://root@127.0.0.1:36453/defaultdb?sslmode=disable'
& "$run/test-venv/Scripts/python.exe" -m pytest tests/test_azure_cost_cockroach_integration.py -q --tb=short --basetemp "$run/final-real-crdb-1"
```

Nodo v24.1.11 fijado por digest, memoria desechable, sin volumen, puerto
loopback y marcador processor-integration-tests. Solo bases temporales
propias. Tras finalizar se verificaron ID/etiquetas y se elimino el nodo.
Problemas iniciales de permisos/temp y preparacion se resolvieron sin
modificar producto; no se consideran fallos de comportamiento.

Red inicial: backend 54 failed/32 passed; processor 48 failed/174 passed/34
skipped; topologia 17 failed/9 passed. Los 119 fallos eran nuevos comportamientos.
Dos pruebas de captura de logs se corrigieron sin rebajar assertions y
fallaron de forma significativa contra la base. Cuatro casos adicionales
de cierre del worker dieron tres Red y un control; Green2 los resuelve.
Comandos, basetemps y salidas exactas: `red-*-final.txt`,
`red-fix-1-*.txt` y `green-2-*.txt` bajo `$run`.

## Repositorio Y Frontend

| Comando | Resultado | Exit |
| --- | --- | --- |
| corepack pnpm openspec:validate | 28 passed, 0 failed | 0 |
| node tools/jup-check.mjs --all | 16 cambios activos validos | 0 |
| node tools/jup-cleanup-check.mjs | 478 archivos conformes antes de estos dos documentos | 0 |
| node tools/assistant-corpus.mjs validate | PASS | 0 |
| corepack pnpm --filter @finops/frontend build | PASS | 0 |
| corepack pnpm --filter @finops/frontend typecheck | PASS | 0 |
| corepack pnpm --filter @finops/frontend lint | 49 errores react/prop-types preexistentes, 0 warnings | 1 |
| git diff --check | PASS | 0 |

RF-082-002 sigue abierto. El script test de frontend no ejecuta pruebas
reales; no se presenta como cobertura. Se instalo el lockfile existente
con `corepack pnpm install --frozen-lockfile`, sin nuevas dependencias.
Los siete checks remotos (JUP policy, OpenSpec, tres suites Python, build y
typecheck frontend) siguen pendientes: no hay PR ni ejecucion de CI remota.
Las pruebas del validador JUP no acreditan metadatos de una PR inexistente.

## Mutation Y Limites De Build

En copias temporales aisladas, sin tocar producto ni agregar dependencias:
`python $run/verify_mutation.py`, exit 0. Seis baselines exit 0 y seis
mutantes exit 1 por assertions, no por setup/import:

| Decision mutada | Baseline | Mutante |
| --- | --- | --- |
| JWT placeholder, backend | 4 pass | 1 fail, 3 pass |
| Destino DB no local, backend | 7 pass | 2 fail, 5 pass |
| Destino DB no local, processor | 7 pass | 2 fail, 5 pass |
| Redaccion final, backend | 3 pass | 3 fail |
| Redaccion final, processor | 3 pass | 3 fail |
| Sobrescritura hash demo | 1 pass | 1 fail |

Resultado dirigido **6/6 detectados**, no score universal. Los 478 hashes
de fuente coinciden antes/despues. Detalles y comandos:
`mutation-1-verification/mutation-results.json`.

`verify_images.py`, `verify_contexts.py` y `verify_bundle.py`: exit 0.
Cuatro builds de los Dockerfiles reales en una copia con identidad verificada;
tres contextos distintos cubren las cuatro aplicaciones. Dotenv sinteticos
raiz, variantes y anidados quedan excluidos. Se inspeccionaron **42 capas**,
configuraciones de imagen y **3 archivos reales del bundle**: cero sentinelas.
Controles positivos detectados; no se pasaron secretos runtime mediante ARG,
ENV de imagen ni VITE_*. Comandos docker exactos y salidas bajo
`acceptance-1-verification/commands.json` y los informes de contextos/bundle.
Imagenes retenidas: backend `967f7e6fb2a1`, processor `cdd255099719`,
frontend `4dbb9cde9a6e`, simulador `30fe40d91fe8`; IDs completos en
`acceptance-1-verification/image-results.json`.

Scan acotado: 478 rutas de texto versionadas o propuestas, cinco patrones
y cinco controles positivos; nueve registros categoria/ruta en seis rutas
(16 ocurrencias), clasificados como tests sinteticos, denylists o specs.
No inspecciona dotenv reales, almacenes, historial, entropia arbitraria ni
todas las codificaciones. No demuestra ausencia universal de credenciales.
`acceptance-1-verification/bounded-source-scan.json` contiene categorias
y rutas, no valores reales.

## Smoke Aislado

`python $run/verify_smoke.py`, intento final: **exit 1**.
Evidencia en `acceptance-1-verification/smoke-attempt-3/`,
`smoke-results.json` y `smoke-commands.json`.

- Proyecto Docker nuevo y verificado, nueve contenedores, once puertos altos
  publicados solo en loopback, credenciales sinteticas y opt-in local explicito.
- Cuatro aplicaciones saludables; login HTTP 200.
- Dieciseis casos de secretos requeridos ausentes/vacios rechazados.
- Reinicio/cambio del input seed conserva hash, identidad y roles.
- Rotacion explicita demo/JWT rechaza password/token anteriores.
- Grafana conserva password sintetica, cuenta, preferencias, volumen y
  autenticacion tras trasladar la fuente a dotenv.
- **Ingesta HTTP 202 pero job failed**: incompatibilidad heredada entre
  payload anidado del backend y text_content esperado por processor.
  Reproducida en base 7d76fc3 y Green2 mediante
  `verify_ingestion_handoff.py` (exit 0 acredita reproduccion, no arreglo).
- El error inicial SET CLUSTER SETTING dentro de transaccion multisentencia
  se corrigio solo en preparacion; permanece como intento fallido registrado.
- Se eliminaron solo contenedores, volumenes, redes e imagenes de sondeo
  propios tras verificar identidad; ningun contenedor sigue ejecutandose.

La password Grafana local se conserva en .env ignorado del worktree de
JUP-053, sin imprimirla, rotarla, borrar cuenta/volumen ni desactivar auth.
El traslado se refiere al valor existente de configuracion, no a un cambio
en una instalacion compartida. La prueba de conservacion usa fixtures.
Rotaciones DB/broker/gateway solo se documentaron, no se ejecutaron sobre
servidores reales; no hubo proveedor LLM real ni provisionamiento TLS.

## Estado Historico Tras Review 1

La primera revision reviso los 17 escenarios y encontro RF-053-001/002/003
dentro del alcance: overrides DSN, claves secretas en JSON y diagnostico
original perdido. Esos hallazgos invalidan la suficiencia del Green actual:
se necesitan Red/Green, mutation y revision adicionales antes de QA.
RF-053-004 es el fallo funcional heredado de ingesta y requiere una decision
humana separada. No se ha dispensado ni ampliado el alcance para corregirlo.

Guards planner/tester/coder/reviewer PASS; reviewer no cambio archivos.
QA y aprobacion humana final pendientes. No commit/push, PR, Trello, merge,
archivado ni cambios de responsables. Develop permanece limpio y se
preservan los nueve cambios staged preexistentes del worktree anterior.
