# Evidencia JUP-085: Autenticacion, Sesion Y CORS

JUP: JUP-085
Trello: https://trello.com/c/Z8M443Hu

## Publicacion Para Revision: 23/09/2026

Paris autoriza commit, push y PR hacia `develop`; registro a 17:15:32 UTC
en [review.md](../../openspec/changes/jup-085-auth-session-contract/review.md#autorizacion-de-publicacion-para-revision).
PR prevista como borrador: no levanta QA_BLOCKED_ENV ni cierra RF-085-002,
no supone aprobacion humana final ni permite ejecutar merge o archivado.
`origin/develop` comprobado antes de publicar: `3a08d60`, sin cambios frente
a la base probada. El commit solo consolida el diff validado y este registro;
no se modifica producto ni se repiten las suites al registrar la autorizacion.
Las menciones posteriores a ausencia de commit/PR describen cada ronda local
anterior. El resultado remoto de CI y las revisiones se consultan en la PR;
no se anticipan como PASS. `.env` real, relojes y trackers quedan intactos.

## Incremento Actual: Tolerancia JWT De 5 s

Paris autorizo explicitamente "ok implementa la medida de tolerancia y deja el
reloj de cockrachDB"; addendum registrado el 23/09/2026 a 16:01:44 UTC en la
[propuesta](../../openspec/changes/jup-085-auth-session-contract/proposal.md).
Base `3a08d60ddd48a8693a95025948bc941a0e54b7de` mas diff local sin publicar.
Cambio de producto de este incremento: una linea `leeway=5` en `jwt.decode`.
No cambia TTL emitido, HS256, firma, claims requeridos, tipos estrictos,
`exp > iat`, consulta de usuario ni JUP-097. `iat`/`nbf` admiten hasta `now+5`;
expiracion admite `now < exp+5`, nunca la igualdad. No hay nueva configuracion.

| Comprobacion incremental | Resultado | Exit |
| --- | --- | --- |
| Baseline backend antes de cambiar tests | 245 PASS | 0 |
| Red semantico | 252 PASS / 7 FAIL, 259 casos; sin errores de setup | 1 |
| Green auth focalizado / backend completo | 60 PASS / 259 PASS; 12 warnings existentes | 0 |
| Backend antes/despues de mutacion | 259 PASS en ambas pasadas | 0 |
| Mutacion dirigida | 7/7 detectados; 0 equivalentes, 0 supervivientes | 0 |
| Revision independiente | REVIEW_PASS; guard sin escrituras ni infracciones | 0 |
| Navegador real sobre backend actualizado | 8/8 PASS | 0 |
| QA incremental | QA_PASS acotado a leeway=5; 16:33:02.775 UTC | 0 |

Incremento neto: **14 pruebas backend**, de 245 a 259. Se sustituyo un caso
historico por 15 casos, conservando los otros 244; la fixture de iat futuro
pasa de +1 a +6 conforme al nuevo contrato. Rechazos verifican 401 generico,
sin lookup ni filtracion de credenciales. Fronteras exactas y +/-0.001 s,
claims negativos y orden temporal invertido/igual estan cubiertos.
Las otras suites no se repitieron: sus 654 PASS y 34 SKIP anteriores pertenecen
a superficies intactas. El agregado historico actualizado seria 913 PASS y
34 SKIP, no una ejecucion conjunta nueva ni pruebas de integracion omitidas.

Mutantes: leeway 0/4/6 producen 7/6/6 fallos; desactivar iat/exp/nbf produce
2/2/2; retirar `exp > iat` produce 2. **BE1 ahora es detectado**, no equivalente:
`iat=now+4, exp=now-4` y `iat=exp=now+4` exigen ese control independiente.
La equivalencia anterior solo describe margen cero; no se suman campanas.
Mutacion en memoria, 55 hashes backend intactos, sin escrituras de producto.

Comandos con Python 3.12.13/PyJWT 2.14.0 y entorno de pruebas ya existente,
desde `apps/backend`; cada ejecucion usa basetemp nuevo, sin instalaciones:

```powershell
$env:PYTHONPATH = ''
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -B -m pytest -p no:cacheprovider --basetemp <nuevo-temporal> -q --tb=short tests/test_auth_api.py
python -B -m pytest -p no:cacheprovider --basetemp <nuevo-temporal> -q --tb=short tests
python -B <evidencia-temporal>/leeway5-mutations.py
docker compose --env-file <env-sintetico> -p jup085-qa-20260923 build backend
docker compose --env-file <env-sintetico> -p jup085-qa-20260923 up -d --no-deps --no-build --wait backend
```

Backend reconstruido y saludable a 16:15:46.9797503 UTC, exit 0. Imagen
`sha256:03904ecbf021dcb3c798247ed56a6e0f46dd367af8cfc67b20e095a262586c6a`.
Los otros cuatro contenedores conservan IDs/inicios/restarts; no se reinicia
CockroachDB ni se opera sobre relojes/configuracion Windows, WSL, Docker o DB.
Entorno sintetico externo, `.env` real intacto, sin secretos en evidencias.

Reviewer ejecuto una pasada real del navegador entre 16:23:15.692 y
16:23:20.082 UTC: login/bootstrap, preflight nativo, billing protegido,
recarga, logout, JWT invalido, expirado 60 s y origen denegado: 8/8 PASS.
Sin mocks ni bypass de seguridad; billing sigue siendo demo. Fingerprints de
login/storage/requests coinciden, firma verificada y TTL emitido 28.800 s.
No es prueba de estabilidad sostenida del reloj ni de costes reales.

Artefactos locales conservados bajo `economicon-jup085-runtime-20260923`:
`leeway5-red-handoff`, `leeway5-green-coder-handoff`,
`leeway5-mutation-handoff` (MD/JSON, logs/XML asociados) y
`leeway5-review-2026-09-23T16-23-15-692Z/reviewer-handoff.md` con capturas,
metadatos y resultado de navegador. Guards spec/tester/coder/reviewer PASS.
Hashes SHA-256 verificados en disco, y security tambien dentro del contenedor:

- `security.py`: `4dde07e3a3e0804bd9afa06482facd33bb4b9bccd83888908d1178f81598568d`.
- `test_auth_api.py`: `4e0d0bcc573ddde8c0534fcf0035d9b592e8b3d777aeaca579bd18dd0a996811`.

**RF-085-002 sigue Open y el bloqueo ambiental global no se levanta.** El
usuario excluye nuevas intervenciones de reloj; se retira la propuesta de
ajuste persistente. Leeway reduce rechazos por desfase JWT pequeno, pero no
repara errores internos de CockroachDB. El estado horario obsoleto anterior
no demuestra por si solo un fallo actual de la app; causa del 500 no probada.
No hay aprobacion humana final ni autorizacion de PR/merge/archivo/tracker.

QA independiente del incremento, registrado a 16:33:02.775 UTC: **QA_PASS**.
Ejecuto OpenSpec 33/33, trazabilidad, higiene (615 archivos), diff y control
de preparacion, todos exit 0. Cotejo Red/Green/mutacion, 55 hashes backend,
48 enlaces y evidencia 8/8 del reviewer sobre imagen/hash correctos. No
repitio suites ni navegador; guard QA sin escrituras ni infracciones. No
midio ni infirio estado actual del reloj. Este resultado no sustituye el
gate global QA_BLOCKED_ENV ni la aprobacion humana final pendiente.

## Resultado Previo Del 23/09/2026 (Historico, Margen Cero)

**Codigo REVIEW_PASS; QA_BLOCKED_ENV por RF-085-002: sincronizacion Windows obsoleta.**
Base `3a08d60ddd48a8693a95025948bc941a0e54b7de` mas diff local, rama
`feat/JUP-085-auth-session-contract`. HEAD no contiene aun esta implementacion:
no hay nuevo commit ni PR. `develop` principal permanece limpio.

[Propuesta y aprobacion](../../openspec/changes/jup-085-auth-session-contract/proposal.md),
[diseno](../../openspec/changes/jup-085-auth-session-contract/design.md),
[tareas](../../openspec/changes/jup-085-auth-session-contract/tasks.md),
[review](../../openspec/changes/jup-085-auth-session-contract/review.md) y
[ADR-0007](../adr/ADR-0007-backend-cors-policy.md).
Paris aprobo el residual y los parametros CORS el 23/09; registro 13:05:53 UTC.
Se avanzo la rama desde `1ff8e07` preservando byte a byte los 15 archivos
locales anteriores. No se acredita participacion humana por trabajo automatizado.

Se conservan perfil/tenants paralelos, query keys y retries/refetch de JUP-097;
cualquier error de la query actual `/me` cierra sesion. Se completan validacion
runtime, perfil persistido, reconciliacion de identidad, limpieza y generacion,
401 global autenticado antes del body y aislamiento de respuestas antiguas.
CORS conserva la politica exacta y los limites aprobados de middleware/errores.
No se modifican `.env`, credenciales existentes, migraciones, seed, CI,
dependencias, tenant authorization ni persistencia del historial conversacional.

## Pruebas Y Gates Anteriores Al Incremento

| Comprobacion | Resultado | Exit |
| --- | --- | --- |
| Backend completo | 245 passed; 12 warnings existentes | 0 |
| Frontend completo final | 235 passed, 39 archivos | 0 |
| Processor | 266 passed, 34 skips condicionales | 0 |
| Azure cost API simulada | 58 passed | 0 |
| Nueve suites Node de gobernanza/topologia | 83 passed | 0 |
| Colaboracion | 12 passed | 0 |
| Frontend lint / typecheck / build | PASS; warning de chunk grande heredado | 0 |
| CORS con Settings 2.3.4 / 2.15.0 | 76 passed en cada version; imports sin secretos correctos | 0 |
| OpenSpec estricto tras sincronizacion documental | 33/33 | 0 |
| Trazabilidad / higiene / whitespace | PASS; 10 cambios activos, 615 archivos | 0 |
| Corpus documental | PASS | 0 |
| Limites por fase / revision tecnica | PASS; re-review coteja 135 hashes | 0 |
| Re-review ambiental | PASS acotado: 741 muestras sin retrocesos y tres pasadas 8/8 | 0 |
| QA final tras mitigacion del reloj | BLOCKED: Windows vuelve a error 2, informacion horaria obsoleta | pendiente |
| Aprobacion humana final / CI remoto / PR | No realizados | pendiente |

Total distinto: **899 pruebas correctas**, 34 omitidas, sin sumar reruns,
selecciones, compatibilidad, mutantes, OpenSpec ni recorridos de navegador.
Residual nuevo del 23/09: **215 casos** (76 CORS y 139 frontend); los 54 nuevos
backend del 10/09 son adicionales y ya estan incluidos en los 245 actuales.
Los skips del processor no son PASS ni prueba de integracion de su base real.

Red residual: backend baseline 169 PASS; CORS nuevo 17 PASS / 59 fallos
semanticos, backend total 186 PASS / 59 FAIL. Frontend baseline 96 PASS;
135 casos nuevos iniciales con 65 PASS / 70 FAIL, total 161 PASS / 70 FAIL.
Cuatro fixtures antiguos no cumplian el contrato de exito de `/me`/login;
tester corrigio solo sus datos en SessionGate.test.tsx, routes.integration.test.tsx
y LoginPage.test.tsx, sin debilitar aserciones. Dos casos adicionales detectan
rechazos tardios; dos posteriores detectaron RF-085-001 (233 PASS / 2 FAIL).
No se cuentan errores de instalacion, importacion o setup como Red semantico.

Se corrigio aparte una incompatibilidad real con el minimo Settings 2.3.4:
NoDecode no existia alli. Se usa Json/lista estricta compatible, sin elevar
dependencias; la matriz de CORS se repitio con el paquete minimo real.

### Comandos Reproducidos

Python 3.12.13, con entornos temporales separados para backend y regresiones.
Backend: pytest 9.1.1, FastAPI 0.141.1, Pydantic 2.13.5, Settings 2.15.0,
PyJWT 2.14.0. Matriz adicional Settings 2.3.4 inyectada por PYTHONPATH y
version/path comprobados en proceso nuevo. No es matriz de todas las versiones.
Frontend: pnpm 9, lockfile intacto, Vitest 3.2.7, Vite 5.4.21; Node local 24.

Desde cada `apps/backend`, `apps/processor` y `apps/azure-cost-api`, con su
interprete/requirements existentes instalados en el entorno temporal:

```powershell
$env:PYTHONPATH = ''
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -B -m pytest -p no:cacheprovider --basetemp <nuevo-temporal> -q tests
# Backend, matriz Settings minimo y actual:
python -B -m pytest -p no:cacheprovider --basetemp <nuevo-temporal> -q tests/test_cors.py
```

Desde la raiz del worktree:

```powershell
corepack pnpm install --frozen-lockfile
corepack pnpm --filter @finops/frontend test
corepack pnpm --filter @finops/frontend lint
corepack pnpm --filter @finops/frontend typecheck
corepack pnpm --filter @finops/frontend build
node --test tools/assistant-corpus.test.mjs tools/ci-workflow.test.mjs tools/delivery-roadmap.test.mjs tools/docker-topology.test.mjs tools/jup-check.test.mjs tools/jup-cleanup-check.test.mjs tools/llm-gateway-config.test.mjs tools/pr-policy.test.mjs tools/repository-governance.test.mjs
python -m unittest discover -s tools/collaboration/tests -v
node tools/assistant-corpus.mjs validate
node tools/jup-check.mjs --all
node tools/jup-cleanup-check.mjs
corepack pnpm openspec:validate
git diff --check
```

Algunos accesos restringidos a Corepack/Python devolvieron EPERM antes de
ejecutar. Se usaron permisos de ejecucion y, en la sincronizacion documental,
los mismos entrypoints Node instalados, sin cambio de dependencias. La primera
instalacion offline incompleta se sustituyo por frozen-lockfile correcto.
Esos fallos de entorno se excluyen de los recuentos funcionales.

## Mutacion Dirigida Final

37 variantes: 18 backend (17 kills, BE1 equivalente) y 19 frontend (18 kills,
FE1 equivalente). **35/35 variantes no equivalentes detectadas**, ninguna
pendiente; cobertura dirigida, no exhaustiva. Solo aserciones de comportamiento
cuentan como kills, no errores del runner. Mutacion en memoria, sin editar producto.

- B01-B13: default/CORS, HTTPS, wildcard, JSON vacio/null, origenes/metodos/
  cabeceras/credenciales, montaje, preflight y diagnosticos. Todos detectados.
- B14-B17: TTL, iat obligatorio, Bearer duplicado y firma. Todos detectados.
- F01-F05: contratos runtime/storage/login/perfil. Todos detectados.
- F06-F10 y F17: caches, 401 antes del body, exclusiones publicas y 403. Detectados.
- F11-F16: generaciones, body/rechazos tardios, errores `/me` y paralelismo.
  Detectados; F13 necesito dos regresiones adicionales, no una excepcion.
- F18: retirar gcTime Infinity en mutaciones abandonadas reproduce los dos
  fallos de timers tras logout. F06/F17 finales producen 22 fallos cada uno.
- BE1: reloj/claims requeridos conservan `iat <= now < exp`, que implica exp > iat.
- FE1: tras leer el body de error, el throw sincronico llega al catch con guard
  de generacion intacto; no hay await/efecto entre ambos controles.

Comandos locales: `python -B <evidencia-local>/backend-mutations.py` y
`node <evidencia-local>/frontend-mutations.mjs` con IDs de la tabla final.
Se reejecutaron variantes afectadas tras compatibilidad y limpieza; el ultimo
tester cotejo 57 hashes backend antes de reutilizar sus resultados. Artefactos
temporales de diagnostico, no dependencias ni herramientas personales versionadas.

SHA-256 de los registros locales finales:
- backend-mutations.py: `82da556e0f8596a6d0d4d92fc3cb2ebf837f7f01f729a6bea633c065fc00ebd3`.
- frontend-mutations.mjs: `ee8984e33fbd946ccd9bb626b4bb2d5dfa9484fd9feda481a6255994bf3c4d9f`.
- mutation-handoff.json: `800d45a6c2f1d9fa436d92e54c30b9f0a5a22e82142b1b22436698dd07e914d5`.
- reviewer-runtime-browser-results.json: `704d1d5192be04d85d9c01f912edcf82da7a688b2a5316900abf37ec2804a569`.

## Navegador Y Entorno Aislado

Compose `jup085-qa-20260923`, env temporal con valores sinteticos, cinco
servicios: CockroachDB, RabbitMQ, pgvector, backend y frontend. Sin datos
compartidos, LLM ni processor. Frontend `http://127.0.0.1:59173`, API
`http://127.0.0.1:58085`; ambos publicados en loopback, sin proxy.
Chromium 1161 con seguridad normal. Imagenes finales:
backend `9086281d485ca1be2b5ebac90188a1bbed85ec5e45c367cf8b9608727b5434a7`,
frontend `b1b32b7ac5bcf80a034a4e34a6d2602bec0d3f81ee1bff5a35a2239cfddb4f17`.
Coordinacion cotejo 38 archivos backend y 36 frontend entre imagen y worktree.

Comandos: `docker compose --env-file <env-sintetico> -p jup085-qa-20260923
build backend frontend` y `up -d --no-build --wait` sobre esos cinco servicios;
se reconstruyo cada aplicacion tras su ultima correccion. Config quiet, builds
y health checks pasaron. No se leyo, copio ni edito el `.env` real del usuario.

Ocho recorridos reales: login/bootstrap, OPTIONS nativo sin JWT, billing con
Bearer/tenant, recarga/restauracion, logout local, token invalido, expirado y
origen denegado (`localhost` distinto de `127.0.0.1`). Billing conserva sus
constantes demo: no se entregan nuevas API de costes ni datos Azure reales.

`node <evidencia-local>/browser-checks.cjs` fue reutilizado por tester y
coordinacion. Tras el ultimo rebuild: primer intento login 500, segundo
3 checks PASS y recarga 401; ambos fallidos. La primera repeticion independiente
con instrumentacion del reviewer paso **8/8** entre las 14:37:19-22 UTC del
backend, entre saltos de reloj. Token emitido/guardado/enviado coincide,
firma correcta y TTL 28.800 s. No convierte el entorno en estable.

Diagnostico adicional con UI real y respuestas interceptadas sinteticas,
sin ingesta efectiva: antes RF-085-001 dejaba un timer recurrente tras tres
ciclos; despues los ciclos fueron 4->0, 0->0, 0->0, sin sesion/tenant retenidos.
Este diagnostico no se presenta como un noveno recorrido real de API.

## Bloqueo Del Entorno

Antecedente anterior a la mitigacion autorizada descrita debajo:

RF-085-002: CockroachDB registra retrocesos de 2-3 s aproximadamente cada 28 s,
mas errores remote wall time, SQL y liveness. Login correcto a 14:32:53.133;
recarga con 401 a 14:32:51.670, tras retroceso de -2.104183 s registrado a
14:32:51.647956. Respaldan rechazo de iat futuro; el token de ese fallo no
se capturo y la causa exacta del 500/InternalError anterior sigue sin probar.

El 500 de 14:29:12.156 siguio a otro retroceso de -3.048755 s a 14:29:09.990812.
Lecturas directas repetidas y un login mas seis `/me` HTTP posteriores pasaron;
demuestran intermitencia, no resolucion. Una unica ejecucion 8/8 tampoco basta.
No se alteraron reloj, WSL/Docker compartido, leeway JWT ni politica `/me`.

Accion entonces pendiente: estabilizar reloj con autorizacion para cualquier operacion
compartida y repetir runtime/QA. No hay excepcion aprobada ni permiso para
cerrar RF-087-001/RF-095-001, publicar PR, fusionar o archivar. RF-087-002
sigue fuera del alcance. La revision de codigo PASS no es un QA final PASS.

## Mitigacion Local Del Reloj: 23/09

Paris autorizo abordar el reloj mediante "autorizado", sin reiniciar servicios
compartidos sin nueva confirmacion. Windows estaba sin sincronizar, fuente
Local CMOS Clock; tres muestras NTP midieron -3.1223012, -3.1216807 y
-3.1199908 s respecto a time.windows.com. Ubuntu usaba ntp.ubuntu.com,
offset -3.126223 s y sondeo de 32 s; WSL tenia timesync_implicit habilitado.
Los datos apuntan a correcciones host/guest contradictorias, no a un defecto
JWT. No se ha demostrado por separado el mecanismo interno exacto.

Se solicitaron dos resincronizaciones con la fuente Windows ya configurada,
a las 15:14:15 y 15:15:35 UTC. El intento sin elevacion devolvio acceso
denegado; la elevacion normal de Windows termino exit 0 en ambos casos:

```powershell
$p = Start-Process "$env:WINDIR\System32\w32tm.exe" -ArgumentList '/resync','/rediscover' -Verb RunAs -WindowStyle Hidden -PassThru -Wait
$p.ExitCode
w32tm /query /status /verbose
w32tm /stripchart /computer:time.windows.com /samples:3 /dataonly
wsl -d Ubuntu -- timedatectl timesync-status
```

No se cambiaron configuraciones, fuentes NTP, codigo, JWT, `.env`, imagenes
ni contenedores; no hubo reinicios de Windows, WSL, Docker ni servicios.
Tras la primera operacion persistieron transitorios: el ultimo aviso observado
fue -0.354459 s a 15:15:49.988651. La ventana estable empieza despues.

Re-review independiente: **REVIEW_PASS ambiental acotado**, no QA final.
Entre 15:17:58.480 y 15:21:03.649 UTC se tomaron 741 muestras backend a
cadencia nominal 250 ms: 185.169 s, cero retrocesos y divergencia puntual
maxima realtime/monotonico de 0.729 ms. CockroachDB no roto su log;
lineas nuevas 4045-4051 sin eventos de reloj, liveness ni job-claim detectados.
Windows termino leap 0, stratum 5, error 0; offsets NTP finales +5.36 a +5.96 ms.

Se reutilizaron los scripts de navegador sin cambiar aserciones, con salidas
separadas: 15:17:58-15:18:02, 15:18:37-15:18:42 y 15:19:17-15:19:21 UTC,
**8/8 PASS cada pasada**, separadas por 35 s. Son ocho escenarios repetidos,
no 24 pruebas distintas ni ampliacion de las 899. Login, storage y requests
conservaron fingerprint, firma y TTL 28.800 s correctos. Se observaron 57
respuestas 200 y 12 rechazos 401 intencionados por tokens invalidos/caducados;
ningun 500 ni fallo de solicitud inesperado. Los 16 artefactos previos siguen
intactos. Guard reviewer PASS, cero escrituras/infracciones.

Evidencia temporal: `environment-review-2026-09-23T15-17-57-749Z/summary.json`,
SHA-256 `fb5cc99299b02471d4c7735e44bf3f4bf69e183e0ca3d8e186ea765d709cb089`.
Incluye muestras, eventos sanitizados y tres pasadas; el handoff describe
comandos, intervalos y preservacion. No se versionan herramientas personales.

RF-085-002 quedo provisionalmente **Mitigated (local; durabilidad pendiente)**. Permitio retomar
QA en el entorno observado, no acredita estabilidad permanente: el intervalo
Windows existente de 32768 s y futuras suspensiones/reanudaciones no se han
validado. Comprobar reloj y logs antes de otra QA; si reaparecen saltos, bloquear
runtime de nuevo. No se acepta una excepcion a JWT ni se cierra el riesgo del
host. RF-087-001/RF-095-001 siguen pendientes de QA y cierre; RF-087-002 ajeno.

## Revalidacion QA Tras Mitigacion: 23/09

**QA_BLOCKED_ENV**, registrado a 15:35:35.747 UTC. Windows regreso de error
0 a error 2 (informacion horaria obsoleta), confirmado a 15:34:54.304 UTC;
ultima sincronizacion seguia siendo 15:15:35. No se observaron nuevos saltos
de reloj ni fallos funcionales, pero la correccion puntual no acredita una
sincronizacion automatica mantenida. RF-085-002 vuelve a **Open**, con
mitigacion temporal registrada, no cierre ni excepcion.

QA tomo otras 741 muestras durante 185.172 s: cero retrocesos, divergencia
maxima 3.091 ms y cero nuevos avisos de reloj en CockroachDB. Una pasada
independiente de los ocho escenarios existentes dio **8/8 PASS** entre
15:30:56.991 y 15:31:01.093 UTC. Se acumulan cuatro pasadas posteriores a la
correccion, no 32 pruebas distintas ni sustitucion de la QA bloqueada.

OpenSpec 33/33, trazabilidad de 10 cambios, higiene de 615 archivos, corpus
y whitespace PASS. Verificados ocho documentos, 40 enlaces, 135 fuentes,
140 artefactos y cinco hashes publicados. Los 899 PASS/34 SKIP, calidad y
mutacion se revisaron como evidencia, sin reejecutar esas suites. Cinco
contenedores y 16 artefactos previos intactos; guard QA sin cambios/infracciones.
Registro `qa-final-2026-09-23T15-30-56-263Z/summary.json`, SHA-256
`d5ec2eb66d7a19f0078ae63abe72e95b73f7f223a1060e7ce247fa8e9059a6f8`.

Diagnostico posterior: equipo no unido a dominio y sin clave de politica
W32Time. Configuracion existente: time.windows.com,0x9, SpecialPollInterval
32768 s, MinPollInterval 10 y MaxPollInterval 15. El intervalo especial
prolongado es una hipotesis respaldada por la configuracion y la caducidad,
no prueba de que se haya reproducido exactamente un defecto interno de Windows.
[Microsoft documenta el sondeo adaptativo como alternativa](https://learn.microsoft.com/en-us/troubleshoot/windows-server/active-directory/w32time-sync-specialpollinterval-ignored)
y [los ajustes de frecuencia y su aplicacion sin reiniciar](https://learn.microsoft.com/en-us/windows-server/networking/windows-time-service/configuring-systems-for-high-accuracy).

Se solicito entonces autorizacion especifica para un ajuste persistente: conservar
time.windows.com, retirar el intervalo especial y usar sondeo adaptativo
64-1024 s, guardando los valores previos. Afecta al reloj del equipo completo;
**no aplicado**. La decision posterior del usuario lo excluye de este alcance;
no queda como preparativo obligatorio del incremento JWT. La estabilidad
sostenida del entorno sigue sin acreditarse.
No se modificaron registros, politicas, servicios, producto, JWT ni `.env`.
Publicacion, merge, archivo, trackers y gate humano post-QA siguen pendientes.

## Auditoria QA Anterior Del 23/09

**QA_BLOCKED_ENV**, no QA PASS. La auditoria independiente no establecio otro
defecto de producto. Ejecuto OpenSpec estricto 33/33, trazabilidad de 10 cambios,
higiene de 615 archivos, corpus y whitespace, todos exit 0. Cotejo 31 enlaces
en ocho documentos, 135 hashes de fuente, 140 de artefactos y los cuatro
hashes publicados. Las suites 899/34, lint/typecheck/build y mutacion se
revisaron como evidencia registrada, no se reejecutaron en esta auditoria.

Se detecto una omision administrativa de dos registros consolidados de limites
de roles, aunque sus comparaciones originales ya estaban ejecutadas y PASS.
Coordinacion los registro a partir de esa evidencia y repitio correctamente
el control de preparacion para QA. No acredita QA funcional ni aprobacion
final. Guard QA sin escrituras e infracciones. RF-085-002 permanece High/Open;
en ese momento no habia correccion del reloj ni excepcion humana autorizadas.

## Historial Anterior

Los registros siguientes describen sus fechas; no sustituyen el estado actual.

### Avance Backend Del 10/09

JUP: JUP-085
Trello: https://trello.com/c/Z8M443Hu

## Contexto Y Resultado

Registro del 2026-09-10. Base `1ff8e071f83a58f630c496740d712e8c0e2cc443`,
rama `feat/JUP-085-auth-session-contract`, diff local sin commit ni PR.
[Aprobacion](../../openspec/changes/jup-085-auth-session-contract/proposal.md)
de Paris a las 18:30:51 UTC; [revision backend](../../openspec/changes/jup-085-auth-session-contract/review.md)
PASS. QA backend PASS, registrado a las 19:15:39 UTC; no se declara QA integral
ni entrega completa.

Python 3.12.13; pytest 9.1.1, FastAPI 0.141.1, httpx 0.28.1, Pydantic 2.13.5,
pydantic-settings 2.15.0, PyJWT 2.13.0, structlog 26.1.0, SQLAlchemy 2.0.52.
Se reutilizo el entorno ya instalado, sin modificar dependencias. Los imports
de config, security, dependencies, auth routes y schema se verificaron contra
el worktree de JUP-085, no contra el codigo de otra entrega.

Las rutas HTTP son las reales de FastAPI mediante transporte ASGI, con usuario
y DB falsos y configuracion sintetica. Los casos de seed reutilizan sus fixtures
existentes. No se conectaron servicios compartidos ni se leyo/modifico .env.
Esto no es un smoke del stack con bases reales ni una prueba de navegador.

## Comandos Y Recuentos

Desde `apps/backend`, usando ese interprete (`python` en los comandos de abajo):

```powershell
$env:PYTHONPATH = ''
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
# Cada invocacion usa un directorio temporal nuevo, comprobado inexistente.
python -B -m pytest -p no:cacheprovider --basetemp <nuevo-temporal> -q tests/test_auth_schema.py tests/test_security_utils.py tests/test_secret_config.py tests/test_secret_boundaries.py tests/test_demo_seed.py
python -B -m pytest -p no:cacheprovider --basetemp <nuevo-temporal> -q --tb=short tests/test_auth_schema.py tests/test_security_utils.py tests/test_auth_api.py tests/test_secret_config.py
python -B -m pytest -p no:cacheprovider --basetemp <nuevo-temporal> -q tests/test_auth_schema.py tests/test_security_utils.py tests/test_auth_api.py tests/test_secret_config.py tests/test_secret_boundaries.py tests/test_demo_seed.py
python -B -m pytest -p no:cacheprovider --basetemp <nuevo-temporal> -q tests
```

| Ejecucion | Resultado | Exit |
| --- | --- | --- |
| Seleccion preexistente antes de escribir tests | 92 passed | 0 |
| Red focalizado tras anadir tests, antes de producto | 102 passed, 22 failed | 1 |
| Red con regresiones, confirmado independientemente | 124 passed, 22 failed | 1 |
| Green focalizado con regresiones | 146 passed | 0 |
| Backend completo tras Green | 169 passed | 0 |
| Backend completo antes/despues de mutacion | 169 passed en cada ejecucion | 0 |
| Backend completo en revision independiente | 169 passed | 0 |
| Backend completo en QA independiente | 169 passed | 0 |

54 casos nuevos: schema 3, utilidades JWT 1, API HTTP 46 y configuracion TTL 4.
El Red incluye 32 casos nuevos que ya pasaban y 22 que fallaban; conserva
70 casos focalizados antiguos y 22 regresiones antiguas. No hubo errores de
coleccion/setup. Las repeticiones y selecciones no aumentan el total distinto.

Los 22 fallos demostraron password vacia (2), emision iat/TTL (2), Bearer (4),
subject/tipos/valores temporales (9), ausencia iat/exp (2), usuario eliminado (1)
y TTL no positivo (2). Desaparecen con cuatro archivos de producto modificados.

Se observaron 12 warnings por claves sinteticas y deprecacion SQLite datetime.
Los primeros intentos de acceso al interprete/CLI desde el entorno restringido
fallaron antes de ejecutar; los reintentos autorizados usaron las mismas
instalaciones. Esos errores de entorno no se presentan como Red ni como PASS.

## Mutacion Dirigida

Cada caso se ejecuto en un proceso nuevo, con una sola variante de codigo
compilada en memoria. No se editaron archivos de producto en disco. Los nodos
seleccionados pasaron primero sobre codigo sin mutar. Ejecucion local:
`python -B <directorio-local-de-evidencia>/backend-directed-mutation.py`, exit 0.
El script y los logs son diagnosticos locales, no dependencias del producto.

| Caso | Cambio deliberado | Deteccion por pruebas |
| --- | --- | --- |
| M01 | Permitir password vacia | schema y HTTP 422: 2 fallos |
| M02 | Permitir TTL cero/negativo | startup sanitizado: 2 fallos, 1 control correcto |
| M03 | Omitir iat emitido | emision y login: 2 fallos |
| M04 | Tratar minutos como segundos | emision y login: 2 fallos |
| M05 | Completar iat antiguo con cero | legacy-without-iat: 1 fallo |
| M06 | Delegar tipos estrictos solo a PyJWT | subject vacio y tipos/valores temporales: 8 fallos, 10 controles correctos |
| M07 | Aceptar primer header duplicado | duplicate: 1 fallo |
| M08 | Exigir mayusculas exactas en Bearer | case-insensitive: 1 fallo |
| M09 | Ignorar segmentos extra del Bearer | extra-segment: 1 fallo |
| M10 | Revelar usuario eliminado | removed-user: 1 fallo |
| M11 | Permitir un segundo de tolerancia | expiracion exacta/future-iat: 2 fallos |
| M12 | Saltar firma manteniendo claims | unsigned/wrong-key/wrong-algorithm: 3 fallos, 1 control correcto |
| E01 | Retirar guardia explicita exp > iat | Equivalente: 19 casos correctos |

Resultado: 13 variantes unicas, 12 detectadas por aserciones de comportamiento,
0 supervivientes no equivalentes y 1 equivalente. No es cobertura exhaustiva
ni se cuentan fallos de importacion o setup como deteccion. E01 conserva
required/tipos y el reloj de PyJWT con `iat <= now < exp`, que implica
`exp > iat`; no se cuenta como kill ni como excepcion material.

La primera pasada encontro un problema de clasificacion del runner temporal;
se corrigio y repitio. Solo la pasada final se contabiliza. Manifiestos
antes/despues identicos para los 54 archivos Python de backend; comprobados
ademas contra disco por la revision independiente y la coordinacion.

Identificadores SHA-256 de la evidencia local final:

- Runner: `12af0b2b353ae559cb81c7f92a4652258ca9042a0390d7090dbd008bba46374b`.
- Resumen: `5a37f1016208e841ed3e3cefa61701839fa5155d9c8d06bc9e583b8fb3215ddf`.
- Manifiesto final: `4d05f7066f92f1eaabb8407181bc9cf82e6e670066a1975eac4471439454e695`.

## Gobernanza Y Limites

OpenSpec 1.8.0 existente: `corepack pnpm openspec:validate`, 29/29, exit 0.
`corepack pnpm jup:check -- --change jup-085-auth-session-contract`, exit 0.
`corepack pnpm jup:cleanup:check`, 497 archivos en QA, exit 0.
`git diff --check`, exit 0. Verificacion de limites de cada fase sin infracciones.
QA comprobo los 6 documentos y sus 8 enlaces locales, los hashes de 54 archivos
Python y los 3 hashes de evidencia local publicados arriba, sin bloqueos.
El registro posterior del resultado QA solo actualiza documentacion, sin cambios
de producto o tests. El resultado QA_BACKEND_PASS se limita al backend.

Estado al 10/09 (historico): frontend, lint/build/typecheck, CI y validacion funcional integral no se han
ejecutado como gates finales de esta entrega parcial. JUP-087 debe integrarse
y revalidarse antes del trabajo frontend. No se acredita reparacion de
RF-053-004/JUP-020 ni autorizacion tenant/JUP-086. No se declaran revisiones,
pairing, QA humana, publicacion, merge o archivo realizados por esta evidencia.

## Actualizacion Documental Del 23/09/2026

Los resultados anteriores no se han reejecutado. Se reconcilia la propuesta
con upstream `3a08d60` sin incorporar aun esos ocho commits a la rama local
`1ff8e07` ni modificar producto o tests. JUP-087/095/097 ya estan integradas;
JUP-020 ya corrigio RF-053-004. Esas entregas no convierten el QA parcial
del 10/09 en QA integral de JUP-085.

La decision expresa de Paris conserva JUP-097: consultas de perfil y tenants
paralelas y logout ante cualquier error actual de revalidacion `/me`.
La aprobacion de implementacion del residual revisado y CORS sigue pendiente.

Comandos ejecutados en el worktree de JUP-085 con las herramientas existentes:

| Comando / comprobacion | Resultado del 23/09 |
| --- | --- |
| `corepack pnpm openspec:validate` | exit 0; 29 passed, 0 failed |
| `node tools/jup-check.mjs --change jup-085-auth-session-contract` | exit 0; enlazado con Trello y completo estructuralmente |
| `node tools/jup-cleanup-check.mjs` | exit 0; 497 archivos |
| `git diff --check` | exit 0 |
| Resolucion de enlaces Markdown relativos | 8 destinos existentes en los 6 documentos |
| Comparacion SHA-256 antes/despues | 179 archivos versionados de apps mas el test nuevo preexistente, sin diferencias |

OpenSpec usa CLI local 1.8.0 y Corepack cacheado, sin instalar dependencias.
Los 29 items corresponden a la base antigua del worktree, no a los 33 de
develop. Revision independiente documental PASS, sin nuevos hallazgos;
limites de spec-planner y reviewer correctos. Pruebas funcionales y mutacion
no aplican a estos cambios de texto, pero siguen exigidas para el residual
de producto. QA documental independiente del 23/09: **QA_DOCS_PASS**, tras
repetir OpenSpec estricto (29/29), trazabilidad, higiene (497 archivos),
whitespace y enlaces (8/8); exit 0 en todos. Guard QA sin escrituras ni
infracciones. No es aprobacion final, pairing humano, publicacion de PR ni
cierre de tarjeta. El DoD funcional sigue pendiente de sus propios gates.
