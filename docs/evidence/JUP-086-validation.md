# Evidencia JUP-086: Aislamiento Por Tenant

JUP: JUP-086
Trello: https://trello.com/c/bKxQK9HI

## Estado

26/09/2026: ratificacion detallada APPROVED, dos grupos pendientes acreditados
y **REVIEW_PASS tecnico**, sin cambios de producto ni hallazgos bloqueantes.
Inventario684 (328 backend+356 processor),111 nuevos de JUP-086 (60+51).
Ejecucion actual11 PASS (3 nuevos+8 regresiones),0 FAIL/ERROR/SKIP;681 PASS
anteriores reutilizados, no684 ejecuciones nuevas. **QA_PASS** del conjunto
acotado,26/09/2026, sin bloqueos ni excepciones.
RF-086-003 corregido localmente, aun sin integrar. Post-QA humano APPROVED
por Paris el26/09; autoriza publicar rama y PR contra develop, no merge ni
Trello. [Registro](../../openspec/changes/jup-086-tenant-isolation-contract/review.md#gate-post-qa-humano).
Preparacion de publicacion: origin/develop sigue en3a1001d tras fetch;
146 hashes de fuente coinciden con QA, sin cambios de producto o tests.

## Validacion acotada final

Alcance ratificado: [tabla vigente](../../openspec/changes/jup-086-tenant-isolation-contract/resource-matrix.md#aceptacion-acotada-vigente).
Base3a1001d mas diff local. Solo cambian dos modulos de test del backend:
`test_rabbitmq_publisher.py` (dos casos y control opt-in del peer existente)
y `test_rabbitmq_publisher_integration.py` (un caso SQLite y hook explicito
del orquestador). El modulo de test no ejecuta Docker ni un restart generico.
144/146 fuentes comparadas con el lote anterior intactas, incluido todo el
producto. Los15 cuerpos anteriores de esos modulos y681 IDs se conservan.
No casos ocultos en TEMP ni cambios de dependencias, limites o reloj.

| Caso nuevo | Observacion directa y limite |
| --- | --- |
| `test_same_backend_real_owned_restart_next_http_confirmed_no_replay[sqlite]` | Rabbit real reiniciado con identidad/StartedAt comprobados; mismo PID/app/publisher/owner. Publicacion previa confirmada y entrega previa unknown/HTTP503, siguiente HTTP202 confirmado, tres estados SQL scoped alice/tenant-a, generacion nueva, no replay y cleanup. SQLite real, no nueva ejecucion Cockroach. |
| `test_actual_pika_blocked_unblocked_resumes_once_and_close_is_terminal` | Pika recibe frames serializados Blocked/Unblocked del peer propio. Suspension0.35s, reanudacion una vez; otro ticket bloqueado cierra not_sent/stopping en0.180596s, resultado inmutable, no replay y cleanup. No alarma real de Rabbit. |
| `test_actual_pika_blocked_expiry_retires_inflight_without_replay` | Un envio esperando confirmacion y otro en cola. Retirada bloqueada3.001312s, unknown/connection_lost antes de confirm5s; ticket pendiente cierra not_sent/stopping. Inmutabilidad, no replay, EOF y limpieza de owner/helpers. |

Se mantienen heartbeat30s, confirm5s, blocked3s, ticket10s, close5s y tick0.1s.
No parche temporal en estos casos. La regresion historica de heartbeat
acelerado permanece aparte, sin convertirla en prueba de idle30s.

Contexto: WSL Ubuntu, CPython3.12.3, Pika1.4.4 y pytest9.1.1; copias temporales
del codigo local auditadas por hashes. Comandos desde PowerShell:

```powershell
wsl -d Ubuntu -- /tmp/jup086-linux-validation-20260926-1519/bin/python -B /mnt/c/Users/Trabajo/AppData/Local/Temp/jup086-bounded-20260926/run.py peer
wsl -d Ubuntu -- /tmp/jup086-linux-validation-20260926-1519/bin/python -B /mnt/c/Users/Trabajo/AppData/Local/Temp/jup086-bounded-20260926/run.py restart
wsl -d Ubuntu -- /tmp/jup086-linux-validation-20260926-1519/bin/python -B /mnt/c/Users/Trabajo/AppData/Local/Temp/jup086-bounded-20260926/run.py collect
wsl -d Ubuntu -- /tmp/jup086-linux-validation-20260926-1519/bin/python -B /mnt/c/Users/Trabajo/AppData/Local/Temp/jup086-bounded-20260926/run.py sensitivity
wsl -d Ubuntu -- /tmp/jup086-linux-validation-20260926-1519/bin/python -B /mnt/c/Users/Trabajo/AppData/Local/Temp/jup086-bounded-20260926/audit.py
wsl -d Ubuntu -- /tmp/jup086-linux-validation-20260926-1519/bin/python -B /mnt/c/Users/Trabajo/AppData/Local/Temp/jup086-bounded-20260926/postgreen_audit.py
```

JUnit: peer8 PASS/exit0 y Rabbit3 PASS/exit0. Collection328+356/exit0;
collection-only XML no cuenta ejecuciones. Sensitivity: pytest exit1,
un FAIL semantico esperado,0 ERROR/SKIP; su driver comprueba ese resultado.
El operador en memoria elimina solo `_blocked_at is None` de `_tick` y
falla en `Blocked publisher sent before Unblocked`. No es un defecto del
producto original ni fallo de importacion. Coder GREEN/NOOP, tester
post-Green MUTATION_PASS por identidad de fuentes/artefactos, sin rerun.
38 variantes historicas detectadas reutilizadas +un fallo dirigido separado;
no se afirma39 distintos ni una campana historica nueva.

Artefactos locales en `C:/Users/Trabajo/AppData/Local/Temp/jup086-bounded-20260926/`:
`peer-baseline.json`, `restart-baseline.json`, sus `junit.xml`/`stdout.txt`,
`runtime-*.json`, `collect-*/stdout.txt`, `suspend-sensitivity.json`,
`suspend-sensitivity/junit.xml`, `sensitivity-source.json`, `hash-audit.json`,
`hashes-current.json`, `preservation-audit.json`, `artifact-hashes.json`,
`postgreen-audit.json`, `postgreen-artifact-hashes.json` y ambos handoffs.
Registran argv/cwd completos, SHA256, resultados y las copias Linux usadas.
Auditorias exit0; manifests originales34 entradas intactas.

El driver restart salio1 despues de pasar los tests, solo por comparar mapas
de labels Docker en distinto orden. `cleanup.json` conserva el false original;
`cleanup-audit.json` normaliza las claves y demuestra inventario equivalente.
Se corrigio el auditor TEMP sin repetir tests ni ocultar el primer resultado;
`run.py` es fuente reproducible actual, no transcripcion del driver anterior.

Rabbit propio `cbd2629dc1d12e2a6bd3a9531e1201f13b6d46b438f880f47da9e3b1192aaf1e`,
imagen instalada `sha256:e582c0bc7766f3342496d8485efb5a1df782b5ce3886ad017e2eaae442311f69`,
127.0.0.1:25686, tmpfs y credenciales sinteticas; sin mounts/descargas.
`identity.json`, `docker.jsonl` y `restart-proof.json` prueban comprobacion
de ID completo/label/imagen/puerto antes de restart/stop/rm. Retirado solo
ese ID; los cinco contenedores anteriores siguen detenidos e intactos.
`remaining-processes.json` y aserciones prueban fin de comandos/owners/helpers.
No prune, volumen compartido, datos del proyecto ni reloj modificados.

Reutilizacion: el [lote real681](#validacion-con-servicios-reales) sigue
aplicable al producto intacto; los ocho casos afectados se repitieron.
397 complementarios previos (235 frontend+59 Azure+91 Node+12 colaboracion),
lint/tipos/build frontend PASS con aviso heredado bundle>500kB: paths intactos
contra HEAD, sin nuevas ejecuciones. Cuatro PASS TLS Windows/loopback previos
auditados por script/XML/log, seis hashes/helpers y runtime3.12.13/Pika1.4.4;
no TLS Linux/Rabbit. Riesgos opcionales de la tabla siguen no verificados:
combinaciones de caida/alarma, plateau Linux, outage SQL y unknown->worker E2E.

Guards tester (dos modulos), coder NOOP, tester post-Green y reviewer PASS.
Primera invocacion del guard coder omitio AllowedPath y no evaluo el control;
se repitio correctamente, exit0/cero cambios, preservando el error y su
registro corrector. No violacion de rol ni escritura de producto.
Documentos/evidencia sincronizados tras reviewer. Gates repetidos sobre
estos documentos: `corepack pnpm openspec:validate`34/34, `node tools/jup-check.mjs --all`11,
`node tools/jup-cleanup-check.mjs`658 y `git diff --check`, todos exit0.
OpenSpec usa herramientas instaladas, red/telemetria deshabilitadas.
Guard del orquestador limita nueve documentos; plan1.35 mantiene identicos
los encabezados/orden de37 pasos y cinco etapas.

QA final readonly: **QA_PASS**, sin bloqueos ni excepciones;146 fuentes,
34 artefactos originales y cuatro post-Green coincidentes, cuatro copias
Linux y681 IDs/15 cuerpos previos preservados. Nueve documentos/108
referencias Markdown auditadas sin errores. Guard QA exit0, cero cambios;
DoD perfil code/stage qa exit0, sin eventos o artefactos faltantes. No es
DoD final ni aprobacion humana. Auditoria `postgreen_audit.py` ejecutada en
memoria via WSL `-B -c` sin su escritura de informe; ningun archivo editado.
Intentos iniciales Corepack/WSL limitados por entorno pasaron al reintentar
con acceso autorizado. No nuevas suites, mutantes o servicios en QA.
Post-QA aprobado posteriormente segun el registro vigente; publicar no
acredita CI remoto, revision humana de PR, merge ni cierre de la tarjeta.

## Reconciliacion documental anterior

26/09/2026, reconciliacion documental autorizada: **REVIEW_PASS documental**,
sin cambios de producto ni de pruebas. La [aceptacion acotada vigente](../../openspec/changes/jup-086-tenant-isolation-contract/resource-matrix.md#aceptacion-acotada-vigente)
sustituye las demandas exhaustivas anteriores, no las garantias funcionales.
Se conserva la evidencia de681 PASS/108 nuevos/38 variantes detectadas;
ninguna prueba funcional o mutacion se ha vuelto a ejecutar en este ajuste.

Reviewer verifica reutilizacion de los cuatro PASS TLS locales del25/09:
script TEMP, XML y log disponibles, seis hashes de producto coincidentes,
helpers importados iguales a la copia guardada; la diferencia de la fixture
DNS solo registra LC_CTYPE. Runtime documentado: CPython3.12.13/Pika1.4.4.
Esto acredita TLS Windows/loopback, no TLS Linux ni RabbitMQ real. Comando y
artefactos originales permanecen en [Validacion DNS Local](#validacion-dns-local).
No se exige duplicar estos casos ni se suman al inventario versionado681.

Pendientes funcionales concretos: reinicio de Rabbit aislado con el mismo
backend (recuperacion scoped, sin replay, cierre), y Blocked/Unblocked del
publisher (suspension/reanudacion, expiracion y cierre acotados). Las otras
combinaciones son validacion opcional no realizada, con riesgos residuales
de plataforma/integracion descritos en la tabla, no garantias probadas.
Ratificacion detallada antes de nuevos codigo/tests, QA de codigo y aprobacion
humana final siguen pendientes. RF-086-003 permanece Open; no hay dispensa.

Validaciones documentales observadas: `corepack pnpm openspec:validate`
34/34; `node tools/jup-check.mjs --all` 11; `node tools/jup-cleanup-check.mjs`
658; `git diff --check`, todos exit0. OpenSpec uso herramientas instaladas
con red/telemetria deshabilitadas tras EPERM inicial del sandbox. Guard
spec-planner: exactamente seis documentos; reviewer: cero cambios. Plan1.34
conserva37 pasos/cinco etapas/orden. **QA documental PASS** tras auditar
sincronizacion, aprobaciones y limites de evidencia; guard QA exit0, cero
cambios. No pruebas ni mutaciones nuevas. El dictamen global sigue pendiente
de los dos grupos runtime, ratificacion y cierre de QA de codigo; este PASS
documental no concede una exencion ni aprobacion humana final.

## Estado anterior a la reconciliacion de criterios

26/09/2026, tras el reinicio manual de Docker: **681 PASS, 0 FAIL/ERROR/SKIP**
en Linux (325 backend + 356 processor). Misma seleccion: 108 nuevos, sin
restauraciones ni casos adicionales. **REVIEW_PASS acotado**, tres defectos
de preparacion/aserciones de tests corregidos; producto sin cambios.
Balance revisado: **38 variantes distintas detectadas**, ninguna pendiente
ni superviviente actual. No son 38 ejecuciones nuevas. La aceptacion global
sigue incompleta por escenarios aun sin cobertura versionada; no QA PASS.

QA del26/09 confirma PASS tecnico acotado y **QA_FAIL / BLOCKED_ACCEPTANCE**
global; BLOCKED_ENV resuelto. Revisa681 IDs,146 hashes,38 detecciones y orden
del plan. Guard readonly PASS. Su unica correccion documental era identificar
como historico el bloque de consolidacion en tasks.md; se ha rotulado asi.
DoD stage qa exit0 solo acredita requisitos de entrada a QA, no aceptacion
global ni gate humano final. OpenSpec34/34, trazabilidad11, higiene658 y
diff-check pasan tras actualizar los documentos.

## Validacion con servicios reales

Paris comunica "he reiniciado docker intentalo ahora". Docker version confirma
Engine28.0.4/Desktop4.40.0; el error de acceso inicial era del sandbox, y la
consulta autorizada devuelve exit0. No fue necesaria la recuperacion propuesta
del socket OTel: no se movio ni borro. Cinco contenedores previos de JUP-085
permanecen detenidos e intactos. Se usan tres instancias nuevas, con datos
tmpfs, sin montajes del proyecto, credenciales aleatorias de prueba, puertos
127.0.0.1 no estandar y las imagenes fijadas ya instaladas, sin descargas.
Cockroach24.1.11, RabbitMQ3.13.7 y PostgreSQL17.11/pgvector; el cluster aislado
se marca processor-integration-tests antes de ejecutar los fixtures.

Primera pasada real conservada: backend323 PASS/2 FAIL y processor353 PASS/
3 FAIL, total676 PASS/5 FAIL, sin omisiones. De los58 SKIP anteriores,53
pasaron y5 fallaron. Dos tests suponian heartbeat2 aunque Pika negociaba30;
tres E2E omitian queue.start() al usar directamente ASGITransport. Los cuatro
mutantes RF003-D03/C01/C02/B15 fueron detectados; V01 sobrevivio al caso que
aceptaba un DBAPIError posterior como rechazo. No se atribuye un fallo de
producto a esas preparaciones defectuosas ni se ocultan los resultados.

Se corrigieron solo tres archivos de tests, sin cambiar IDs ni parametros:
- Publisher integration: idle con TuneOk30 real y espera62s; post-idle202,
  estado queued y cuatro heartbeats del broker. El caso ACK perdido acelera
  heartbeat2 solo para su URL de proxy, conserva confirm5 y exige un heartbeat
  genuino dentro de la ventana de publicacion. Mantiene unknown, entrega,
  recuperacion y no-replay; no acredita el timing de produccion con ese2.
- Processor integration: queue.start() dentro del try protegido por el
  finally existente; se conservan202 y todas las comprobaciones posteriores.
- Processor vector: el caso existente exige PermissionError y conserva sus
  snapshots. No modifica el helper generico ni restaura el caso historico.

| Ejecucion tras corregir tests | PASS | FAIL | SKIP | ERROR | Exit | Segundos |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| V01 baseline reforzado | 1 | 0 | 0 | 0 | 0 | 0,246 |
| V01 mismo mutante | 0 | 1 | 0 | 0 | 1 | 0,264 |
| Linux backend completo | 325 | 0 | 0 | 0 | 0 | 128,047 |
| Linux processor completo | 356 | 0 | 0 | 0 | 0 | 62,272 |

Los681 IDs previos coinciden; los58 casos antes omitidos ahora pasan. No sumar
el baseline/mutante al inventario. Pasan HTTP/cola/worker/retrieval con dos
tenants, replay completado, revocacion permanente, rollback/redelivery por
caida vectorial, aislamiento Cockroach, CAS y retorno mandatory de RabbitMQ.
Windows no se repitio; el WinError10053 historico sigue sin causa establecida.

V01 sustituye una sola vez WHERE knowledge_documents.tenant_id =
excluded.tenant_id por WHERE TRUE en una copia TEMP. El baseline rechaza con
PermissionError; el mutante produce IntegrityError/UniqueViolation al insertar
un chunk duplicado, distinto del rechazo de autorizacion exigido. Confirma
el enmascaramiento previo por rollback. El snapshot posterior no se alcanza
en el mutante; si se comprueba en baseline y suite. Se conserva su intento
superviviente anterior. Balance38 =33 detecciones previas +4 del lote real
anterior +V01 recien detectado. La prueba de herencia de entorno es separada.
Coder NOOP, tester post-Green y reviewer confirman146 hashes actuales,143
fuentes protegidas intactas incluidas93 de producto; R1 y su cuerpo intactos.

Artefactos bajo C:/Users/Trabajo/AppData/Local/Temp:
- S: jup086-live-services2-d0deaea65bf6402daf2758742e259742; primeros JUnit y
  mutaciones en linux/, linux-processor/, linux-mutations/; owned-services.json
  y versions.json documentan el aislamiento. No publicar sus archivos de
  credenciales generadas service-environment.private.json/rabbit.env/vector.env.
- A: jup086-live-testfix3-c408d88df24a47d4806907552b95b445; linux-attempt2/
  contiene results.json, los cuatro JUnit/logs de la tabla, collection-audit,
  exact-three-path.diff, edit-audit y hashes-after-edit/after; hashes-before
  queda en A. Handoff detallado:
  jup086-live-testfix3-tester-handoff.md. Copia Linux:
  /tmp/jup086-live-testfix3-uwa8j7ro/copy.

Comando del lote corregido: wsl.exe -d Ubuntu --exec
/tmp/jup086-linux-validation-20260926-1519/bin/python -B
/mnt/c/Users/Trabajo/AppData/Local/Temp/jup086_live_testfix3.py.
Usa pytest tests por servicio y el selector V01 existente, -B, -q, --tb=short,
-p no:cacheprovider, -o junit_family=legacy, basetemp/JUnit unicos. Limites
120s baseline/mutante y480s por suite. Python3.12.3/pytest9.1.1/Pika1.4.4;
solo cuatro opt-ins de servicios propios, sin dotenv o credenciales heredadas.
Exit0 del lote corregido; pytest mutante exit1 esperado. No timeouts ni
limpieza forzada; todos los procesos de pruebas terminaron. Servicios propios
retenidos temporalmente hasta QA, no servicios de desarrollo compartidos.

Cierre posterior: se verificaron los tres IDs y etiquetas owner/run, datos
tmpfs y ausencia de mounts antes de docker stop --timeout 30 y docker rm
solo de esos IDs. Ambos comandos exit0; Rabbit y PostgreSQL finalizaron0,
Cockroach137 durante la parada acotada: no se acredita cierre gracioso de
Cockroach. Esta retirada de servicios es distinta del cleanup de procesos
pytest, que no requirio terminacion forzada. Los contenedores desechables
quedaron retirados; una nueva lista confirma solo los cinco JUP-085 previos
detenidos. Sin prune, eliminacion de volumenes o datos del proyecto.

Intentos conservados: el aprovisionamiento rechazo SET y SHOW en una misma
transaccion; se separaron, sin recrear contenedores. El preflight del lote
corregido detecto una linea vacia final perdida y se repuso antes de pytest.
No repeticion de suites hasta verde: una pasada antes y otra despues de los
tres cambios concretos; V01 tiene dos intentos separados por el refuerzo.

Queda aceptacion sin completar/versionar: handshakes TLS, recursos Linux
repetidos, restart/NACK/bloqueo-recuperacion-cierre del broker, desconexion
HTTP, outage SQL, unknown ejecutado por worker y probes concurrentes. No son
SKIP pendientes de Docker ni garantias acreditadas por681 PASS. RF-086-003
sigue abierto; sin ampliacion implicita de casos, dispensa o publicacion.

## Estado anterior a los servicios reales

26/09/2026, validacion posterior: **Linux623 PASS/58 SKIP**, Windows focal35
PASS y backend316 PASS/9 SKIP. 108 nuevos/681 total sin incremento. Correccion
de compatibilidad solo en dos archivos de test; producto y heredados intactos.
REVIEW_PASS acotado. Docker no arranca por un socket temporal bloqueado;
servicios reales, cinco variantes, TLS versionado y recursos Linux repetidos
siguen pendientes. No se afirma QA PASS ni cierre de JUP-086.

QA readonly del 26/09/2026, registrado a las 16:00 UTC: auditoria documental
acotada PASS, sin correcciones; **QA_FAIL global, BLOCKED_ACCEPTANCE /
BLOCKED_ENV**. Verifica los JUnit, 681 IDs, 146 hashes actuales y el orden
de 37 pasos/5 etapas del plan. Guard QA exit0, sin cambios ni violaciones.
DoD stage qa exit1: falta mutation PASS o excepcion aprobada; no se concede
dispensa. Siguen pendientes los 58 casos de integracion, cinco mutantes y
los escenarios de aceptacion descritos abajo. La recuperacion limitada de
Docker requiere la autorizacion solicitada. No hay aprobacion post-QA.

## Validacion Linux y entorno

Paris pide completar validaciones y autoriza arrancar Docker con servicios
aislados. Ubuntu estaba activo con Python3.12.3 pero sin dependencias.
Se creo `/tmp/jup086-linux-validation-20260926-1519` usando
`python3 -B -m venv --without-pip`; se instalaron solo los requirements-dev
de backend y processor en ese venv, mediante el zipapp oficial de
[PyPA](https://pip.pypa.io/en/stable/installation/#standalone-zip-application),
PyPI y wheels binarios, con versiones fijadas al inventario Windows.
No paquetes globales, dependencias nuevas del producto ni lockfiles cambiados.
Pytest9.1.1/Pika1.4.4 coinciden; Python Windows3.12.13/Linux3.12.3.
Install-report.json queda en el venv. Constraints temporal SHA256:
`3DA8ABC4D4F5B6D0D7444225102AC16D065F567024622BEF662781D1E631E796`.
Zipapp temporal SHA256:
`91D5FD9F6F25549FD839C60536C6F1B945316CE3588D34A605635B6071C91526`.

El primer focal Linux dio34 PASS/1 FAIL,49,651s, exit1: el hijo contiene
LC_CTYPE aunque Popen recibe env vacio. Es coherente con la coercion
regional [documentada por CPython](https://docs.python.org/3.12/using/cmdline.html#envvar-PYTHONCOERCECLOCALE).
Se corrige solo el test existente y el marcador de su fixture: en Unix,
LC_CTYPE opcional con valor C.UTF-8/C.utf8/UTF-8; ninguna otra clave adicional.
Las keys y valores enviados a Popen siguen siendo EXACTAMENTE los minimos
anteriores (vacio Linux/SystemRoot Windows), y se conservan no-secret,
app_modules, PID, callback y cleanup. Producto sin cambios.

| Ejecucion posterior a la correccion | PASS | FAIL | SKIP | ERROR | Exit | Segundos |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Linux focal existente | 35 | 0 | 0 | 0 | 0 | 49,484 |
| Linux backend completo | 316 | 0 | 9 | 0 | 0 | 55,216 |
| Linux processor completo | 307 | 0 | 49 | 0 | 0 | 5,056 |
| Windows focal existente | 35 | 0 | 0 | 0 | 0 | 61,838 |
| Windows backend completo | 316 | 0 | 9 | 0 | 0 | 70,190 |
| Mutante de herencia de entorno, Linux | 0 | 1 | 0 | 0 | 1 | 0,189 |

No sumar focales ni plataformas al inventario: Linux confirma los681 node IDs
previos (325+356); Windows los325 de backend, sin repetir processor.
Los58 SKIP no son PASS. No hubo timeouts, teardown errors o limpieza forzada.
Se usaron hijos reales y getaddrinfo productivo para loopback en los casos
Pika existentes; otros modos de fallo se inyectan en el hijo. Esto no prueba
TLS handshake ni plateau repetido de FD/recursos Linux.

Mutacion adicional, solo copia temporal y un intento: sustituir una vez
`env=self.environment)` por `env=dict(os.environ))`. El test existente falla
en su asercion no-secret: secret_in_env=True. Baseline real solo registra
LC_CTYPE=C.UTF-8. Una deteccion semantica nueva separada del balance previo
de38 variantes (33 detectadas/5 NOT_RUN); no full mutation PASS ni waiver.
Coder NOOP y tester post-Green cotejan146 hashes; reviewer confirma ausencia
de regresion bloqueante y mantiene R1 cerrado. 144 fuentes sin cambio en
esta correccion, incluidas93 de producto; solo dos archivos de test cambian.
El cuerpo publisher restituido mantiene su hash historico.

Artefactos TEMP Windows:
`jup086-linux-testfix3-312c183fdecc430e8fdd82c3ca7170ee` (A).
`A/linux/results.json` y `A/windows-attempt2/results.json` contienen argv,
cwd, exits, trazas y cleanup. JUnit/logs por focal, full-backend/full-processor
y inherit-environment-mutant; collection-audit.json en cada plataforma.
hashes-before/after-edit y edit-audit.json prueban los dos cambios exactos;
hashes-after por plataforma confirman ausencia de drift. Copia Linux:
`/tmp/jup086-linux-testfix3-c7lrcey2/copy`, reports en su directorio hermano.
Handoff: `jup086-linux-testfix3-tester-handoff.md`; inventario de pendientes:
`jup086-live-validation1-linux-inventory.md`. Primer Red:
`jup086-linux-existing-l5233zyj`, sin sobrescribirlo.

Comandos: `python -B -m pytest TARGET -q --tb=short -p no:cacheprovider
-o junit_family=legacy --basetemp=TEMP --junitxml=REPORT.xml` con TARGET tests,
los35 focales (resolver/publicador/handoff TLS) o el caso de entorno existente.
Sin TEST_URL, dotenv del proyecto o credenciales heredadas; cwd/PYTHONPATH
por servicio. Limites Linux180s focal/210s suites/30s mutante; Windows210s.
Launchers externos: `jup086_linux_testfix3.py windows` y el mismo con linux,
usando los interpretes temporales indicados. No nuevos tests ocultos.

Intentos no acreditados como fallos funcionales: preflight detecto una linea
vacia final perdida y se repuso antes de ejecutar; launcher Windows inicial
termino0xC000013A sin casos, conservado en A/windows. Un unico cambio del
launcher temporal a hidden-only permitio las ejecuciones Windows validas.
El wrapper Linux termino1 despues de los JUnit correctos por exigir la palabra
literal AssertionError; pytest habia renderizado `E assert ... and not True`.
El reviewer confirma la deteccion semantica desde JUnit, sin repetir el mutante;
mutation-adjudication.json conserva la distincion. No se ocultaron intentos.

### Bloqueo Docker y aceptacion restante

Consulta no aislada por el sandbox confirma docker-desktop detenido y Ubuntu
activo. Tras arranque autorizado, Docker abre error-dialog y el motor sigue
sin pipe dockerDesktopLinuxEngine. Docker version exit1; docker info devuelve
error incluso con exit0, por lo que no se contabiliza exito. CLI start dice
already running mientras status dice stopped.
Informe local backend.error.json del26/09 15:11:41 UTC: OTel manager no puede
retirar `C:/Users/Trabajo/AppData/Local/Docker/run/userAnalyticsOtlpHttp.sock`;
el sistema informa que el archivo no es accesible. Archivo de0 bytes fechado
24/09, no datos de base de datos. No se deduce su causa OS mas profunda.
Se ha pedido autorizacion adicional para cerrar Docker, apartar UNICAMENTE
ese socket conservandolo y reiniciar: **PENDING**. No se ha movido/borrado,
no se han creado servicios, reiniciado Ubuntu ni alterado volumenes/reloj.

Quedan58 casos existentes dependientes de servicios y cinco mutantes ya
mapeados a esos casos. Ademas faltan completar/versionar TLS real, plateau
Linux repetido y escenarios de restart/NACK/block-recovery-shutdown,
desconexion HTTP, outage SQL, unknown ejecutado por worker y probes
concurrentes. No son todos simples SKIP ni quedan resueltos solo con Docker.
No hay autorizacion inferida para ampliar el numero de casos ni excepcion.

## Estado anterior a la validacion Linux

26/09/2026: recorte y restitucion de un caso aprobados y aplicados.
Conservados108 de577 nuevos, retirados469 (81,3%); total681, incluidos569
de base y4 netos adaptados. Regresion final623 PASS/58 SKIP, cero FAIL/ERROR;
primer fallo intermitente processor conservado abajo. Producto/heredados
intactos. **REVIEW_PASS acotado, R1 resuelto**: el caso recuperado detecta
el fallo deliberado de prioridad cleanup/spawn. Balance33 detecciones,
cero supervivientes conocidos y5 variantes no ejecutadas. Mutacion global,
Linux y aceptacion real siguen pendientes, sin excepcion ni QA PASS.
La propuesta238 nunca se implemento.

QA readonly, registro26/09/2026 14:55 UTC: ajuste local completo y R1 cerrado;
**QA_FAIL global, BLOCKED_ACCEPTANCE / BLOCKED_ENV**. Confirma inventario,
146 hashes, JUnit,76 enlaces/32 anchors y plan sin cambio de orden.
DoD stage qa exit1: falta mutation PASS o excepcion aprobada por los cinco
operadores no ejecutados. Linux, TLS real versionado y escenarios reales
pendientes; el fallo intermitente heredado permanece documentado.
Referencia operativa680 hallada en design.md corregida a681. Guard QA
exit0, cero cambios; no ejecuciones funcionales ni servicios iniciados.
No se solicita aprobacion final mientras la aceptacion siga incompleta.

## Consolidacion aplicada

Paris autoriza recuperar el unico parametro `publisher` con "aprobado",
registro26/09/2026 14:24:18 UTC en proposal.md. Se usa el cuerpo historico,
sin cambiar helpers/defaults, producto, heredados ni los107 casos retenidos.
Inventario325 backend+356 processor=681;108 nuevos (60 aislamiento+48 RF003).
Los680 node IDs anteriores y sus parametros permanecen. Solo cambia
test_managed_resolver.py en esta restitucion;145 de146 fuentes intactas,
incluidas93 de producto y52 de otros tests/helpers. Coder NOOP, tester
post-Green y reviewer confirman los146 hashes finales, sin mas cambios.

| Ejecucion de restitucion | PASS | FAIL | ERROR | SKIP | Exit |
| --- | ---: | ---: | ---: | ---: | ---: |
| Resolver sin mutar, copia TEMP | 14 | 0 | 0 | 0 | 0 |
| m33 exacto, copia TEMP | 13 | 1 | 0 | 0 | 1 |
| Backend completo | 316 | 0 | 0 | 9 | 0 |
| Processor completo inicial | 306 | 1 | 0 | 49 | 1 |
| Un diagnostico individual autorizado | 1 | 0 | 0 | 0 | 0 |
| Una repeticion completa processor autorizada | 307 | 0 | 0 | 49 | 0 |

Pareja final de suites completas:623 PASS/58 SKIP,681 casos distintos.
Los reruns, baselines y mutantes no aumentan el inventario. De108 nuevos,
89 PASS/19 SKIP; los573 protegidos aportan534 PASS/39 SKIP. Los58 SKIP
siguen siendo51 Cockroach,5 pgvector y2 RabbitMQ segun primer motivo;
no acreditan aceptacion ni disponibilidad actual de Docker.

El fallo inicial es `test_http_redirect_does_not_forward_bearer_token`,
ConnectionAbortedError/WinError10053 esperando una respuesta HTTP loopback,
antes de sus aserciones de seguridad. Se conserva el informe exit1. Unico
diagnostico y unico rerun completo posteriores exit0, sin cambios, skips,
mayor timeout ni aserciones relajadas. Causa no establecida: no se presenta
como fuga de token demostrada ni como incidencia probada inocua. Reviewer
mantiene esta limitacion visible para QA; no reabre R1 ni concede waiver.

m33 retira una vez la condicion REAPING entre plazas en una copia TEMP de
managed_resolver.py; el producto del worktree no cambia. El baseline14 pasa,
y el unico fallo mutado es el caso recuperado: `Spawn overtook pending
cleanup`, previous_unreaped `[34580]` frente a `[]`. Cuerpo historico SHA256
`6932d0f5003cb3c0e7c9db1f2423b1b0928a6537ee85d3db3faad778f58d246d`.
Revision independiente **REVIEW_PASS acotado; R1 cerrado**.
Balance de38 variantes:33 detecciones, cero supervivientes conocidos y5
NOT_RUN_BLOCKED_ENV. Son32 detecciones previas revisadas, no reejecutadas,
mas un m33 nuevo. No full mutation PASS, equivalencias ni excepcion.

Artefactos bajo TEMP: `jup086-108-restore-fd75ee9a2cef4f08996761599b85df61`.
`body-and-collection-audit.json` y `final-body-hash-audit.json` acreditan
seleccion/cuerpo/integridad; hashes-before/after conservan146 entradas.
`regression-results.json` contiene argv/exits de primeras suites y los
full-backend/full-processor.xml/.log permanecen intactos.
`m33/results.json`, baseline.xml/.log y m33-restored-resolver-module.xml/.log
conservan operador, baseline y fallo. `processor-diagnostic/results.json`
y sus focused-redirect-once/full-processor-after-focused-once.xml/.log
separan el diagnostico y el unico rerun. Handoffs externos:
`jup086-108-restore1-tester-handoff.md` y
`jup086-108-mutation-audit1-tester-handoff.md`.

Python3.12.13/Pika1.4.4/pytest9.1.1 existentes, Windows, sin instalaciones.
Comando: `python -B -m pytest TARGET -q --tb=short -p no:cacheprovider
-o junit_family=legacy --basetemp=PREFIX-tmp --junitxml=PREFIX.xml`.
TARGET es tests, tests/test_managed_resolver.py o el node ID exacto del
redirect; argv resueltos en los JSON citados. Cwd/PYTHONPATH por servicio,
PYTHONDONTWRITEBYTECODE=1, sin variables heredadas terminadas TEST_URL.
JUnit:10,354s baseline,10,042s m33,62,809s backend,7,983s processor inicial,
0,627s diagnostico y11,041s processor final. Limites externos60/210/30s
para resolver/suites/diagnostico. Seis subprocessos de test terminados,
sin timeout ni limpieza forzada; handles/hijos propios comprobados.
Guard restitucion un path PASS; coder, tester post-Green y reviewer cero
cambios. No se revalida Docker ni se arrancan servicios compartidos.

Gates tras sincronizar la restitucion: `corepack pnpm openspec:validate`
34/34, `node tools/jup-check.mjs --all` 11 cambios,
`node tools/jup-cleanup-check.mjs` 658 archivos y `git diff --check`, exit0.
OpenSpec requirio repetir con acceso autorizado a la instalacion existente
tras EPERM del sandbox al leer pnpm; sin descargas. Guard orquestador PASS,
exactamente siete documentos. Plan externo v1.31 conserva cinco etapas y
37 pasos/JUP en el mismo orden; copia v1.30 recuperable en TEMP.

### Historia del recorte de 107 casos

El bloque siguiente conserva resultados anteriores a recuperar el caso;
32/1/5 y REVIEW_FAIL fueron sustituidos por la re-review descrita arriba.

Paris aprueba107 casos con "me parece aceptable", registrado26/09 a
13:34:53 UTC en proposal.md. Solo cambian los13 modulos de la matriz.
Identificadores y valores parametrizados conservados coinciden exactamente
con la seleccion. Cuerpos/aserciones retenidos y helpers/fixtures no cambian.
Sin hooks de deseleccion, nuevos SKIP ni bucles que oculten casos.
Auditoria:133 archivos protegidos identicos (93 producto,40 tests/helpers).
Las fases posteriores de mutacion y revision conservan los146 hashes.

| Ejecucion completa actual | Casos | PASS | SKIP | FAIL/ERROR | Exit |
| --- | ---: | ---: | ---: | --- | ---: |
| Backend | 324 | 315 | 9 | 0/0 | 0 |
| Processor | 356 | 307 | 49 | 0/0 | 0 |
| Total | 680 | 622 | 58 | 0/0 | 0 |

De los107 nuevos conservados,88 PASS y19 SKIP. Los573 casos protegidos
(base569 mas4) aportan534 PASS/39 SKIP; no se recortaron. Los motivos de
SKIP reportan51 Cockroach,5 pgvector y2 RabbitMQ; algunas integraciones
requieren varias dependencias y muestran solo la primera ausente.
No se provisionan servicios ni se revalida Docker en esta fase.

Dos Red en copias TEMP: retirar el predicado tenant al consultar un job y
retirar prematuramente el registro de publisher. Cada baseline1 PASS/exit0;
cada mutante1 FAIL/exit1, sin errores/skips ni mutacion del repositorio.
Coder NOOP Green confirma que no hace falta cambiar producto y reutiliza
los JUnit completos tras comprobar hashes, sin repetirlos innecesariamente.

### Mutacion y revision actuales

38 variantes planificadas: **32 detectadas,1 superviviente y5 no ejecutadas
por entorno**.34 intentos de mutacion: el superviviente se ejecuto dos veces.
La primera seleccion de3 casos y la repeticion con las13 pruebas actuales
del resolver pasan aun retirando la prioridad de REAPING entre plazas.
Baseline del modulo completo13 PASS. Esto demuestra un hueco del recorte,
no que el producto sin mutar falle. La revision lo clasifica Medium/en scope
y bloquea aceptar la consolidacion; [detalle y restitucion](../../openspec/changes/jup-086-tenant-isolation-contract/review.md#revision-de-la-consolidacion).

El tester acredito inicialmente30 detecciones y dejo2 fallos de runtime
sin contabilizar. La revision acredita ambos causalmente: entregar antes
de crear/limpiar el hijo produce IndexError; leer sobre el presupuesto
produce gaierror y TypeError en vez de respuestas validas. Baselines verdes,
mutaciones validas y fallos de comportamiento, no errores de importacion o
entorno. No se necesitan nuevas pruebas solo para cambiar la excepcion.
Los resultados crudos conservan la clasificacion preliminar; este dictamen
y review.md registran su adjudicacion, sin alterar logs ni repetir hasta pasar.

Los5 operadores no ejecutados requieren carrera/conflictos Cockroach o
lectura/escritura pgvector. Sus5 casos baseline omitidos estan registrados;
no se cuentan como detecciones ni equivalentes. La muestra incluye permisos,
cotejo del payload persistido, rechazo/retry, costes, CAS, resultados de
publicacion, generacion, secretos, limites/plazos y cleanup DNS. No es
mutacion exhaustiva ni acredita TLS handshake, Linux o toda la aceptacion.

### Comandos y artefactos del recorte

Python3.12.13/Pika1.4.4 existentes; Windows, cada servicio como cwd/PYTHONPATH.
PYTHONDONTWRITEBYTECODE=1; variables heredadas terminadas TEST_URL retiradas.
Regresion: `python -B -m pytest tests -q --tb=short -p no:cacheprovider
-o junit_family=legacy --basetemp=TEMP --junitxml=REPORT.xml`.
Duracion pytest:75,21s backend y12,45s processor. Limite externo210s/suite.
Colecciones completas y valores auditados antes/despues, sin alterar items.

Artefactos locales recuperables, fuera del repositorio:

- `jup086-lean107-fa4d1a4641d74a74bdfedcf1dfaa65ad`: inventarios antes/despues, selection/expected/rewrite-proof/collection-audit/final-audit JSON, full-backend/full-processor JUnit y logs; argv/exits en regression-commands.json. Red valido en retained-red-attempt2/results.json.
- `jup086-107-mutation-301da1d0942f490b95cfad66c368c6a9`: plan.json con reemplazos exactos, results.json con argv/exits/trazas y reports por variante; hashes-before/after. m33-full-retained-module contiene baseline y segunda supervivencia del modulo completo.
- Runners temporales existentes de esta fase: `python -B <TEMP>/jup086_107_mutation.py` y `python -B <TEMP>/jup086_107_mutation_followup.py`. Exit0 significa auditoria terminada, no mutation PASS. No agregan tests funcionales ocultos al recuento.

La primera invocacion Red con launcher separado termino antes de colectar
(0xC000013A,0 casos); se conserva y no cuenta. Una repeticion acotada con
lanzamiento oculto normal produjo los dos Red validos. Mutacion:39 procesos
de prueba terminados, cero timeouts o limpiezas forzadas. Todo cambio de
producto se limito a copias temporales, restauradas al acabar cada variante.
Guard tester13 paths PASS; coder, tester-mutacion y reviewer cero cambios.
Una invocacion coder-guard sin AllowedPath fallo por uso; se repitio con
el path aprobado y confirmo cero cambios. El registro local corrige el PASS
prematuro; no hubo violacion de frontera ni cambio de producto.

OpenSpec34/34, trazabilidad11, higiene658 y diff check observados exit0.
La evidencia anterior de883 PASS/267 SKIP y29 mutantes se conserva abajo
como historia. No se ejecuta nuevo QA hasta resolver el bloqueo de revision.

## Historia previa al recorte

**Correccion DNS local implementada y REVIEW_PASS tecnico, 25/09/2026.**
Green y mutacion acotados comprobados. Auditoria QA completada con QA_FAIL
por aceptacion pendiente (BLOCKED_ACCEPTANCE / BLOCKED_ENV), sin nuevo
defecto de producto identificado ni excepcion concedida.
RF-086-003 sigue Open. Sin commit/push/PR, Trello, merge, archivo, cambios de
dependencias, reloj ni servicios compartidos. La aprobacion pre-code de Paris
de 14:51:40 UTC permanece intacta; no se reutiliza como aprobacion post-QA.

## Preparacion de la reduccion

Historia de planificacion anterior a aprobar/aplicar el recorte; los
PENDING y afirmaciones de ausencia de cambios siguientes pertenecen a esa fase.

La [seleccion de casos](../../openspec/changes/jup-086-tenant-isolation-contract/resource-matrix.md#seleccion-practica-de-pruebas)
conserva 65 nuevos en backend y 42 en processor: 107. Los totales propuestos
son 324 backend y 356 processor. Las 13 filas y sus selectores se cotejaron
contra los inventarios de coleccion existentes: 107 coincidencias, ningun
selector ausente o duplicado. Incluye parametrizaciones y opt-ins/SKIP.
No se crean cupos ficticios para aceptacion futura ni se cuenta una funcion
parametrizada como un caso. Los pendientes futuros cambiaran el total.

La direccion actual de Paris, "correcto adelante", autoriza preparar el
recorte orientado a unos 87 casos, no aceptar una seleccion mayor sin verla.
La propuesta conserva controles tenant/creator/subscription en operaciones
distintas, regresiones de registro y cierre DNS, mensajes invalidos,
rollback, secretos y resultados de publicacion. Reduce cruces de motor,
estado, campo y causa; no vuelve a probar cada cableado de ruta ni todas
las variantes IPC/OS. La matriz detalla esas perdidas de muestreo y el
reuso de pruebas heredadas. Ni esta seleccion ni las anteriores demuestran
un minimo global o equivalencia completa. Regresion, mutacion y revision
deben contrastarla; un hueco confirmado exige decidir su restitucion.

Esta fase solo inspecciona fuentes/inventarios existentes y modifica
documentacion. No ejecuta suites ni mutacion ni acredita nuevo Green/QA.
Una copia recuperable conserva las pruebas previas; 146 fuentes Python de
producto/tests comprobadas sin cambios. Guard de planificacion PASS,
exactamente cuatro documentos y cero violaciones. Comandos observados:
`corepack pnpm openspec:validate` (34/34),
`node tools/jup-check.mjs --all` (11 cambios) y
`node tools/jup-cleanup-check.mjs` (658 archivos), todos exit 0.
El intento inicial OpenSpec fallo con EPERM al leer una dependencia ya
instalada; se repitio con acceso autorizado al mismo runtime, sin descargar
ni instalar. Son gates documentales, no aceptacion de la reduccion.
Linux, TLS real versionado y escenarios con servicios reales siguen
pendientes, sin nueva comprobacion Docker ni excepcion de aceptacion.
Gate de edicion de tests PENDING.

## Validacion DNS Local

Historia del25/09, anterior al recorte; no son los resultados de la suite680.

Base 3a1001d mas diff de trabajo JUP-086. Python 3.12.13, Pika 1.4.4,
pytest 9.1.1 existentes, Windows. Coder modifica solo rabbitmq_queue.py y
los nuevos managed_resolver.py/dns_resolver_child.py; la correccion de la
segunda revision modifica solo los dos primeros. main/SQL/API/processor y
contratos de aislamiento no cambian en este addendum.

| Comprobacion del25/09 | Resultado | Exit |
| --- | --- | ---: |
| Suite backend completa | 517 PASS, 133 SKIP, 0 FAIL/ERROR; 128.222 s JUnit | 0 |
| Suite processor completa | 366 PASS, 134 SKIP, 0 FAIL/ERROR; 13.311 s | 0 |
| Mutacion actual, copia temporal | Baseline 79 PASS; 29/29 mutantes detectados, sin errores de coleccion ni excepciones | 0 runner; 1 cada mutante |
| TLS local temporal con Pika/producto/hijo real | 4 PASS: valido, hostname incorrecto, CA no confiable, TLS establecido con AMQP retenido y close | 0 |
| Recursos Windows, incluido en backend | 10 ciclos DNS reales; 8 muestras tras calentamiento: 346 handles en todas; sin hijos/threads retenidos | 0 |
| Gobernanza Node, sin cambios | 91 PASS, 0 FAIL/SKIP | 0 |
| Segunda revision tecnica y guard | REVIEW_PASS local; cero cambios del reviewer | 0 guard |
| Docker, comprobacion de solo lectura 16:48 UTC | Pipe dockerDesktopLinuxEngine ausente; no se inicio ni recupero el motor | 1 |

Las dos suites suman 1.150 casos distintos: **883 PASS y 267 SKIP**.
Backend omite 126 CockroachDB, 3 pgvector y 4 RabbitMQ; processor omite
124 CockroachDB, 8 pgvector y 2 RabbitMQ. No son aceptacion aprobada.
Los cuatro casos TLS temporales no estan incluidos en el total versionado;
no sumar pruebas focales repetidas, baselines de mutacion ni pasadas anteriores.

### Comandos y trazabilidad

Desde apps/backend y apps/processor respectivamente, con PYTHONPATH del
servicio, PYTHONDONTWRITEBYTECODE=1 y variables opt-in TEST_URL retiradas:

```text
python -B -m pytest tests -q --tb=short -p no:cacheprovider -o junit_family=legacy --basetemp=REPORT-tmp --junitxml=REPORT.xml
node --test tools/*.test.mjs
```

En PowerShell, el glob Node se expandio a los archivos reales antes de
ejecutar. Cada REPORT es unico en TEMP; stdout/stderr y JUnit se inspeccionaron
por tester, orquestador y reviewer. Acceso autorizado al runtime existente,
sin instalacion. Limites externos: backend 210 s, processor/TLS 90 s;
sin timeout ni comandos pendientes.

Prefijos de evidencia local (cada uno con .xml/.log), no archivos versionados:

- jup086-dns-owner-tests1-final-backend-0d0f3d7de7554f7dafafc71d20e2fd6f
- jup086-dns-owner-tests1-processor-93241f1ccd5d46eab9d4037fdbad79b1
- jup086-dns-owner-tests1-tls-ea659673aa45487eb1023d9ae3a26166
- jup086-dns-owner-tests1-mutation-d160093977204572b0d052edda347991

El ultimo directorio conserva results.json, reemplazos y comandos exactos
por mutante, JUnit y logs. El runner temporal se invoco con
`python -B <TEMP>/jup086-dns-owner-tests1-mutate.py`; las cuatro pruebas TLS,
con `python -B -m pytest <TEMP>/jup086_dns_owner_tests1_tls.py` y las mismas
opciones de reporte. No se copian herramientas personales al repositorio.

### Red, correcciones y mutacion

Red DNS inicial: 46 casos, 43 FAIL (4 semanticos y 39 entrypoints aun
ausentes, estos ultimos excluidos como Red semantico), 3 PASS, 0 ERROR/SKIP.
La implementacion detecto y corrigio un conhost real por hijo Windows:
CREATE_NO_WINDOW solo no bastaba; CREATE_NO_WINDOW | DETACHED_PROCESS evita
esa consola adicional y conserva stdhandles redirigidos. El censo real
posterior muestra solo los hijos directos y su terminacion/reap.

Una prueba pedia reemplazo tras cerrar pipes, antes de liberar la plaza.
Se corrigio esperando el evento done, sin relajar la ausencia de solapamiento
ni la supresion de callbacks cancelados. Primera pasada Green DNS: 509
backend/366 processor PASS y 21 mutantes distintos en 22 intentos; una
laguna de plazo del waiter se reforzo y su mutante original quedo detectado.
Son antecedentes, no cifras adicionales actuales.

La segunda revision reprodujo un fallo de registro: close fallo al llegar
a 5 s, DNS ya habia terminado y se permitian dos owners. Red focal:
1 FAIL semantico y 2 PASS, cero errores/skips. La correccion conserva el
registro mientras el hilo siga vivo o Pika no tenga limpieza acreditada
por su owner; no lee objetos Pika desde el thread del registro. Pruebas
actuales cubren registros activo/cache, hilo vivo con prueba de limpieza,
hilo muerto sin esa prueba, referencias retenidas, cierre ajeno y reinicio
tras limpieza. Mantiene resultado unknown inmutable y no replay.

La primera suite completa posterior dio 511 PASS, 1 FAIL y 1 error de
teardown del mismo caso, 133 SKIP. La fixture no reconocia el aborto Windows
10053. Solo ese codigo se clasifica ahora como terminal, conservando las
comprobaciones de limpieza del producto; otros errores siguen fallando.
El reporte fallido se conserva: jup086-dns-owner-tests1-backend-44b85599e4ab43dab43d883283c1dc2e.
La pasada focal posterior observo 10053 correctamente; la suite final
observo reset/EOF, no se afirma otra reproduccion natural de 10053.

Mutacion actual: los 21 casos DNS se repiten sobre el codigo corregido y
se anaden ocho: retirar con owner vivo, ignorar fin del hilo, ignorar prueba
Pika, reutilizar prueba antigua, certificar conexion abierta, descartar
sesion no verificada, permitir liberar a un no-owner y olvidar registro
activo al cerrar DNS. **29 variantes/29 intentos, 29 detecciones semanticas**,
sin supervivientes, equivalentes, invalidos ni excepciones. Es muestra de
riesgo, no cobertura exhaustiva. Los 34 mutantes del publicador original y
los 21/22 historicos no se suman a este lote.

Solo se mutaron copias TEMP. Censo de cleanup con handles activos y
comprobacion de parentesco/lifetime; cero terminaciones forzadas o timeouts.
Se conservaron hashes de producto. La limitacion del primer runner historico
(PIDs ya terminados en su censo) queda documentada: tampoco realizo
terminaciones forzadas; el runner actual no reutiliza esa receta.

### Plataforma y limites

TLS usa el OpenSSL ya instalado solo para certificado/clave sinteticos
temporales y stdlib SSL en un peer propio. No instala dependencia ni cambia
almacenes de confianza. Certificado/clave eliminados y ausencia de PEM
verificada independientemente. DNS real en hijo mapea el nombre sintetico
a loopback; SNI/validacion mantienen el hostname original. TLSv1.3 en los
casos positivos, cero AMQP en los rechazos. No es RabbitMQ real.

El plateau de diez ciclos es evidencia Windows acotada, no duracion
ilimitada ni prueba Linux. Linux sigue sin ejecutar, incluidas identidad
PID, FD y posible coercion LC_CTYPE del interprete con env suministrado vacio.
No se debilitan assertions ni se concede excepcion especulativa.
Faltan servicios reales, idle/restart/ACK-loss/NACK/Return/blocked y carreras
SQL/API/worker de la matriz. Los escenarios combinados de tiempos e IPC
restantes deben completarse; no se afirma una prueba exhaustiva.
QA no aprueba la aceptacion; aprobacion humana post-QA pendiente.

### Auditoria QA del 25/09

Resultado registrado a 17:17 UTC: **QA_FAIL**, por evidencia de aceptacion
incompleta, no por un nuevo fallo reproducido de producto. Auditoria de solo
lectura: los JUnit, los 30 reportes de mutacion (baseline mas 29 variantes)
y los seis hashes coinciden con los resultados anteriores. No se repitieron
las suites, mutantes ni la comprobacion Docker; todos los comandos terminaron.
OpenSpec 34/34, trazabilidad 11, higiene 658 y diff check: exit 0. Cero cambios
o violaciones del rol; sin inconsistencias documentales actuales observadas.

Quedan para tester la aceptacion Linux con proceso real, los escenarios
combinados DNS/IPC/start/cleanup restantes y las pruebas con RabbitMQ,
CockroachDB y pgvector aislados. El entorno Docker no esta disponible segun
la comprobacion de 16:48 UTC; no se autoriza recuperarlo o cambiar servicios
compartidos. No todos los casos pendientes se reducen a ejecutar los 267 SKIP.
Los fallos que aparezcan vuelven a coder o tester segun su origen, seguidos
de las comprobaciones afectadas, revision, evidencia y QA de nuevo.
RF-086-003 y las tareas 4.12/4.14 permanecen abiertas. Sin publicacion ni
aprobacion post-QA; la revision tecnica local PASS no sustituye la aceptacion.

### Integridad revisada

SHA256 del producto comprobado (paths bajo apps/backend/app):

| Path | SHA256 |
| --- | --- |
| services/rabbitmq_queue.py | CE531D63738DA49B4258F4ADB63B1EB869E4C6EAD1DC5447703683B3D9727681 |
| services/managed_resolver.py | 9969F27E688722F060563C5317C51C9143E1EF6FE4C847812920B130556A7F27 |
| services/dns_resolver_child.py | 9732A5CB4142C385E7ACBF904F0933D8E969C215B19626DDFD584B0CC3EB0492 |
| main.py | 751FB8DF1B08605B0E62C7A15DE613EF0C4FBEE4C7872E5B32A84148AB5A2C8C |
| db/database.py | 2C7F588FB6DE52B9D22E8884DFE75895B7AF2D95EC4C3EB4433C67FD2BB2241F |
| api/routes/jobs.py | 04C53C18CE45E47B18D6A1AC01B2AE918BFA1B4B25514C0B2B0089CB4E2FF4FD |

Los ultimos tres no cambiaron durante DNS; child no cambio en la correccion
del registro. Guards de cada fase pasan, sin ediciones fuera de sus paths.
La revision tecnica automatizada no acredita pairing/revision/QA humanos.

Validacion documental final del orquestador, 25/09/2026 17:09 UTC:
`corepack pnpm openspec:validate` 34/34; `node tools/jup-check.mjs --all`
11 cambios; `node tools/jup-cleanup-check.mjs` 658 archivos;
`git diff --check` sin errores. Todos exit 0, con herramientas existentes,
red/telemetria OpenSpec desactivadas. Auditoria de nueve documentos:
77 destinos Markdown locales y 28 anclas, cero errores; no prueba enlaces
externos. Plan v1.26 conserva exactamente cinco etapas y 37 encabezados PASO
en el mismo orden que v1.25. No se infiere QA de estos checks documentales.

## Historia de preparacion y validaciones anteriores

Gate detallado DNS **APPROVED** por Paris, registro 25/09/2026 14:51:40 UTC
en proposal.md; addendum Accepted. Se autoriza empezar Red/correccion del
detalle, sin nuevos resultados aun. Aclaracion: cap DNS por proceso, no
limite de tenants/jobs; sin cuotas o garantia medida de equidad. REVIEW_FAIL,
dos Red y aceptacion real pendiente no quedan resueltos por la aprobacion.
Los estados pre-code PENDING siguientes son historia de preparacion.

Preparacion documental posterior del 25/09: propuesta DNS detallada completa,
**READY_FOR_PRE_CODE_GATE; aprobacion detallada PENDING**. Paris autoriza
documentar proceso terminable y excepcion interna Pika con "adelante, pero
documenta todo lo necesario" (registro 14:03:35 UTC). No es implementacion,
pruebas, nueva QA ni permiso de recuperar Docker. El guard de spec-planner
pasa con seis documentos cambiados y ningun path de producto/tests.
El bloqueo de redaccion anterior queda resuelto; REVIEW_FAIL y dos Red DNS
siguen vigentes. No se ha observado una averia DNS real del entorno: las
regresiones retienen deliberadamente el resolver para comprobar su limpieza.

Historico inmediato: preparacion autorizada a 12:58:26 UTC, interrumpida al
confirmar la advertencia no-publica de AbstractIOServices de Pika 1.4.4
(`nbio_interface.py:26-32`, comprobacion 13:08:00 UTC). Aquella fase guard
spec-planner PASS con cero cambios no es la propuesta ahora completada.

**RF-086-003 implementado localmente, no terminado. REVIEW_FAIL /
pre-code DNS PENDING; BLOCKED_ENV para servicios reales.** Registro original
del orquestador 25/09/2026 10:49:57 UTC. Se mantienen dos regresiones DNS
en Red; no se han debilitado ni omitido. No hay QA nueva, aprobacion post-QA
ni publicacion. Los estados inferiores del 24/09 son historia, no una
excepcion reutilizable para este incremento. El estado original BLOCKED_DESIGN
evoluciona a propuesta lista para aprobacion, no a producto corregido.

### Validacion documental del addendum DNS

Orquestador, 25/09/2026; worktree JUP-086 sobre 3a1001d mas diff local, sin
commit nuevo. Propuesta en ADR-0009 y cinco documentos OpenSpec: direccion y
riesgo interno aceptados para redactar, detalle de implementacion no aprobado.
Supervisor unico/dos plazas publisher-probe, IPC/secretos/PID, cleanup, plazos,
limite OS y siete paths futuros constan en diseno y matriz. Sin ejecucion de
hijos DNS, pruebas funcionales, procesos de aplicacion ni nuevos mutantes.

| Comando/comprobacion documental observado | Resultado | Exit |
| --- | --- | ---: |
| `corepack pnpm openspec:validate` | 34/34 | 0 |
| `node tools/jup-check.mjs --all` | 11 cambios enlazados | 0 |
| `node tools/jup-cleanup-check.mjs` | 654 archivos | 0 |
| `git diff --check` | Sin errores | 0 |
| Guard spec-planner del addendum | Seis paths documentales; cero violaciones | 0 |

Corepack fallo inicialmente con EPERM leyendo su cache en sandbox; se repitio
con acceso autorizado a herramientas existentes, OPENSPEC_TELEMETRY=0,
COREPACK_ENABLE_NETWORK=0 y el binario OpenSpec ya instalado en el monorepo.
Sin instalaciones, red o cambios de manifests. Los resultados documentales
no acreditan compatibilidad runtime, Red/Green, revision de producto o QA.

## Incremento RF-086-003

Autorizacion: Paris, registro 08:31:11 UTC, contrato ampliado y ADR-0009
Accepted. Python 3.12.13, pytest 9.1.1, Pika 1.4.4 instalados, sin actualizar
dependencias. Cuatro paths de producto cambiados: publisher, main/lifespan,
database y jobs; sin migraciones, frontend ni nuevo cambio de processor.

Implementacion local: owner con I/O/heartbeats, admision 16/uno en vuelo,
reserva 10 s, confirms 5 s, reconexion y aborto mediante delegado interno de Pika. Resultados explicitos
confirmed/not_sent/rejected/unknown, INSERT publish_pending y finalizacion
CAS por job/tenant/creador; 202 solo confirmado, sin pisar progreso del worker.
Esto no acredita los escenarios reales pendientes ni limpia DNS bloqueado.

| Comprobacion observada | Resultado | Exit |
| --- | --- | ---: |
| Red inicial incremental | 23 fallos semanticos; 41 firmas ausentes excluidas | 1 |
| Primera regresion completa offline, antes del Red DNS | Backend 441 PASS / 133 SKIP; processor 366 PASS / 134 SKIP | 0 |
| Mutacion incremental acotada | 34 variantes detectadas, 35 intentos; uno invalido excluido antes de repeticion correcta | 0 del runner; 1 por deteccion |
| Revision independiente | REVIEW_FAIL; dos probes reproducen helpers DNS vivos | 0 de probes, no aceptacion |
| Red DNS posterior, seleccion stalled_dns | 2 FAIL, 0 PASS/ERROR/SKIP, 54 deselected; 6.88 s | 1 |
| Regresion complementaria sin cambios | Frontend 235, Node 91, Azure 59, colaboracion 12 PASS | 0 |
| Frontend tipos/lint/build | PASS; aviso heredado bundle 767.57 kB >500 kB | 0 |

807 PASS y 267 SKIP son casos distintos de las dos suites completas anteriores;
no sumar reruns, baselines de mutacion ni pruebas DNS como aprobadas. Backend
RF003: 107 PASS/55 SKIP (97 de comportamiento, nueve diagnosticos/viabilidad,
uno del proxy); resto 334/78. Processor RF003: ocho PASS/ocho SKIP de autoridad
pending/unknown; resto 358/126. Los 12 casos de producto/Pika con peer TCP propio
validan setup/cierre, ACK/NACK/Return, incertidumbre, heartbeats sinteticos y
probe; no sustituyen RabbitMQ. Los 397 complementarios tampoco prueban DNS.

Correcciones durante desarrollo: receta directa SelectConnection/delegado
interno verificada mecanicamente contra Pika 1.4.4, nueve doubles antiguos adaptados sin
quitar aserciones, y carrera de resultado terminal del owner corregida bajo
lock (tres casos y mutante). Abort se exige dentro de un tick 100 ms mas
200 ms de margen de scheduling y antes de reutilizar generacion, no en el
mismo instante que despierta el waiter. Errores de fixture/protocolo e imports
no se contaron como Red o mutantes detectados.

Mutacion en copias TEMP: 18 decisiones publisher, ocho SQL, seis API y dos
lifespan; 34 detecciones semanticas, cero supervivientes/equivalentes.
Primer intento lifespan invalido por StartupError excluido; asercion reubicada
fuera del contexto manteniendo el requisito, luego deteccion valida.
Baselines 62 antes/despues y uno antes/despues para esa repeticion. Reviewer
leyo cada JUnit/resultado y verifico los 91 hashes de producto intactos.
La cobertura es acotada y anterior a descubrir DNS, no prueba de ausencia
de defectos. Nueva remediacion obliga a repetir lo afectado.

DNS bloqueante: reviewer y tester usan RabbitMQQueue/Pika reales, reteniendo
solo socket.getaddrinfo mediante Event, sin acceso externo. El punto de
retencion del ensayo es publico; eso no hace publicos los interfaces del producto.
Cierre inmediato deja un helper no daemon; despues de setup de 5 s y backoff
de 1 s hay dos simultaneos. Tester observa cierres de 0.234/0.218 s, pero
hilos vivos. Finalmente libera/une todos y restaura getaddrinfo; cero escapes
del ensayo. Coder confirma en fuentes instaladas que cancel no interrumpe la
consulta OS. Esto concuerda con la [semantica de Timer.cancel de Python](https://docs.python.org/3/library/threading.html#threading.Timer.cancel).
Remedio DNS propuesto en [review](../../openspec/changes/jup-086-tenant-isolation-contract/review.md#rf-086-003);
direccion documentada, gate detallado pendiente y ninguna correccion aplicada.

Entorno: Docker Desktop Linux Engine no disponible (pipe ausente). El intento
de arranque no lo recupero; no reset, borrado de datos/socket, cambio de reloj,
.env ni servicios compartidos. Se solicito decision sobre recuperacion, sin
respuesta registrada. Opt-ins preparados pero no ejecutados: inactividad real,
ACK perdido/Return, Cockroach CAS/concurrencia y membership del worker.
Faltan tambien escenarios reales completos de restart en el mismo proceso,
NACK por limite de cola, bloqueo/recovery/cierre, unknown ejecutado por worker,
desconexion HTTP y caida de finalizacion SQL. TLS y probe simultaneo no
verificados. No es un bloqueo exclusivamente ambiental: falta trabajo de
pruebas ademas de la decision/correccion DNS.

### Comandos Y Artefactos Incrementales

Desde apps/backend o apps/processor, PYTHONPATH al servicio correspondiente,
PYTHONDONTWRITEBYTECODE=1, variables terminadas en TEST_URL retiradas y runtime
aislado existente `%TEMP%/jup086-20260924-0031895a-py312/Scripts/python.exe`.
Invocacion de cada suite completa, con prefijo P indicado a continuacion:

```text
python.exe -B -m pytest tests -q --tb=short -p no:cacheprovider -o junit_family=legacy --basetemp=<P>-tmp --junitxml=<P>.xml
```

Wrapper subprocess con limite 240 s y captura a P.log; backend final 60.39 s,
processor 12.54 s. Prefijos reales bajo `%TEMP%`:

- `jup086-rf086003-green-tests2-backend-verified-ebbe41d4e0d7409287c690f6a64bf1c8`
- `jup086-rf086003-green-tests2-processor-4b40e2a40cfd4ae0a93ce4fc74814d42`
- DNS: mismo argv sustituyendo `tests` por `tests/test_rabbitmq_publisher.py -k stalled_dns`, limite 60 s; P=`jup086-rf086003-dns-red1-353d0ecc7b2c49768020f35fd203772a`.

Mutacion: `%TEMP%/jup086-mutation-b91dszng` y `jup086-mutation-lyc4fok4`,
results.json, JUnit por intento, output.txt y source-hashes-before/after.json;
comandos exactos y sustituciones en results.json. Wrapper reproducido en
`%TEMP%/jup086-rf086003-green-tests2-commands.md`. Handoffs auxiliares locales:
`jup086-rf086003-green-tests2-handoff.md`, `jup086-rf086003-review1-handoff.md`,
`jup086-rf086003-dns-red1-handoff.md` y `jup086-rf086003-dns-feasibility-handoff.md`.
Estos archivos no se incorporan al producto; esta evidencia versionable
conserva conclusiones, comandos, resultados y limites sin depender de su enlace.
Guards spec-planner/tester/coder/reviewer PASS en cada fase; reviewer y coder
de factibilidad no editaron. QA del incremento no iniciada por REVIEW_FAIL.

## Registro De Preparacion Del Incremento

Pre-code incremental APPROVED por Paris, registro 25/09 08:31:11 UTC en
proposal.md; ADR-0009 Accepted. Empieza Red; aun sin resultados nuevos.
Los pendientes pre-code/ADR que siguen son el registro de preparacion.

25/09/2026: RF-086-003 incorporado a JUP-086 por Paris mediante opcion 2,
registro 08:11:57 UTC. **Incremento pendiente de implementacion y validacion**;
el aplazamiento previo queda sustituido. Contrato ampliado y ADR-0009 Proposed;
nuevo pre-code pendiente tras validar documentos. No se reutilizan los
896 PASS/65 mutantes ni el QA anterior como evidencia de esta correccion.
Los resultados siguientes son historia comprobada del alcance original;
Red/Green/mutacion/revision/QA afectadas se repetiran tras aprobacion.

Validacion documental del incremento, registro 25/09/2026 08:28:23 UTC:
`corepack pnpm openspec:validate` 34/34; `node tools/jup-check.mjs --all`
11 cambios; `node tools/jup-cleanup-check.mjs` 651 archivos; `git diff --check`,
todos exit 0. Corepack requirio ejecucion escalada tras EPERM del sandbox,
con red y telemetria desactivadas, sin instalaciones. Comprobacion PowerShell
de diez documentos: 71 enlaces locales y 12 anclas, cero errores; no comprueba
destinos externos. Guard de spec-planner: siete documentos, cero violaciones.
Ninguna prueba funcional nueva ni aceptacion QA del publicador en este registro.

Estado historico anterior a la ampliacion:

24/09/2026. **Green, mutacion y REVIEW_PASS tecnico** tras corregir
RF-086-001/002. Paris aprueba aplazar RF-086-003 (registro 24/09, 21:23:36 UTC);
sigue Open, fuera de alcance y sin corregir. QA actual:
**PASS_WITH_APPROVED_EXCEPTIONS**, disposicion e integridad verificadas;
el QA_BLOCKED_APPROVAL anterior queda como historial.
Aprobacion humana final pendiente. Los apartados "Primer" y la primera
campana de mutacion conservan el historial anterior a remediacion.
Base `3a1001db857191f7abb6bb025e2fe8b04a50fe56`, rama
`feat/JUP-086-tenant-isolation-contract`, sin commit nuevo ni publicacion.

[Propuesta aprobada](../../openspec/changes/jup-086-tenant-isolation-contract/proposal.md),
[revision y hallazgos](../../openspec/changes/jup-086-tenant-isolation-contract/review.md),
[matriz](../../openspec/changes/jup-086-tenant-isolation-contract/resource-matrix.md)
y [ADR-0008](../adr/ADR-0008-tenant-isolation-boundaries.md).
Paris aprobo pre-code el 24/09 a 19:04:10 UTC. No se atribuyen pairing,
revision o validacion humana a las ejecuciones automatizadas.

## Red Inicial

Sin modificar producto, despues de la aprobacion:

| Seleccion sin solapamiento | Fallos | PASS | SKIP |
| --- | ---: | ---: | ---: |
| Backend tenant, SQLite | 19 | 46 | 7 |
| Processor tenant, SQLite | 40 | 5 | 11 |
| Ingesta reconciliada, SQLite | 1 | 4 | 0 |
| Total | 60 | 55 | 18 |

Exit 1 en las selecciones con fallos. Fallos semanticos: selectores, autoridad,
creador ausente en el envelope, hijos/propietarios, jobs manipulados/revocados,
replay, conflictos y rowcounts de costes, logs y conteos globales de health.
Los 18 skips indicaban firmas scoped aun no implementadas, no defectos
demostrados ni pruebas correctas. Se sustituyeron por exigencias que fallan
si desaparece el contexto obligatorio.

Baseline backend Python 3.12: 259 PASS. Processor Python 3.12, excluyendo
los seis casos de ingesta anteriores y las nuevas suites: 270 PASS/34 SKIP
opt-in. El baseline completo anterior en Python 3.10 fue 276 PASS/34 SKIP.
La ejecucion Python 3.10 del simulador no pudo recoger tests por `datetime.UTC`;
fue un fallo de entorno, no Red. Se preparo Python 3.12 aislado.
La primera integracion processor se interrumpio sin resultado global;
no se contabiliza como aceptacion. Solo se limpiaron las bases de la fixture.

## Primer Green Completo

Python 3.12.13, pytest 9.1.1. Todas las opciones de integracion real activadas:

| Suite / grupo sin solapamiento | PASS | FAIL / ERROR / SKIP |
| --- | ---: | --- |
| Backend existente | 259 | 0 / 0 / 0 |
| Backend nuevos casos tenant | 153 | 0 / 0 / 0 |
| Processor existente | 304 | 0 / 0 / 0 |
| Processor ingesta reconciliada | 10 | 0 / 0 / 0 |
| Processor nuevos casos tenant | 148 | 0 / 0 / 0 |
| Total backend + processor | 874 | 0 / 0 / 0 |

Backend 412 casos en 72.17 s; processor 462 en 319.14 s; exit 0.
Incluye usuarios/tenants distintos, ASGI HTTP autenticado, RabbitMQ real,
CockroachDB y pgvector reales, retrieval/citas scoped, replay, rechazos
permanentes, concurrencia vectorial y terminacion de una conexion PostgreSQL
seguida de rollback y reentrega correcta. No hay proveedor de modelo real.

La primera pasada de coder produjo 16 fallos de tests backend por omitir
`requester_id`, cinco de integracion por interpretar un log de cierre como
respuesta y ocho regresiones con mocks o expectativas de contrato obsoletos.
Tester corrigio esas pruebas sin cambiar producto ni habilitar llamadas sin scope.
Las fixtures propias reutilizan schema migrado y limpian solo sus datos,
reduciendo DDL repetido sin quitar escenarios ni debilitar las guardas.

Desde cada servicio, en procesos separados por el paquete `app`:

```powershell
$env:JUP086_COCKROACH_TEST_URL = '<URL admin local desechable marcada>'
$env:PROCESSOR_COCKROACH_TEST_URL = $env:JUP086_COCKROACH_TEST_URL
$env:JUP086_VECTOR_TEST_URL = '<URL admin pgvector local desechable>'
$env:JUP086_RABBITMQ_TEST_URL = '<URL RabbitMQ local desechable>'
python -B -m pytest -p no:cacheprovider tests -q --tb=short --disable-warnings --basetemp <temporal-unico> --junitxml <reporte-junit>
```

Se usaron los contratos de seguridad de las fixtures: nodo Cockroach marcado
`processor-integration-tests`, puertos loopback no estandar, bases/colas
generadas y eliminacion solo tras acreditar su creacion. Sin .env real,
migraciones compartidas, secretos de usuario ni cambios de reloj.

## Mutacion Dirigida

60 variantes distintas, 62 ejecuciones; **55 detecciones semanticas,
cinco equivalentes y cero supervivientes pendientes**. No es cobertura
exhaustiva del proyecto ni un porcentaje general de cobertura.

| Grupo | Variantes | Detectadas | Equivalentes |
| --- | ---: | ---: | ---: |
| Backend: selector, membership, creador, mensajes, retrieval | 15 | 13 | 2 |
| Processor: creador/permisos, correlacion, estados, cola y logs | 21 | 21 | 0 |
| Costes: conflictos, scope, rowcounts y propagacion | 17 | 15 | 2 |
| Vector: ownership, reemplazo y transaccion | 5 | 4 | 1 |
| Salud y contrato de dependencias | 2 | 2 | 0 |

- B09/B10: los otros predicados implican igualdad entre tenant padre/hijo.
- C03/C04: el UPDATE scoped final rechaza y revierte la operacion no autorizada.
- V05: el upsert condicional ya bloqueo/autorizo el padre en esa transaccion.
- V01/V02: las pruebas de reemplazo vacio detectan los casos inicialmente
  enmascarados. Se conservan los intentos previos; no se suman como variantes.
- No se cuentan errores de sintaxis, importacion o setup como detecciones.
  Reviewer cotejo la clasificacion final contra JUnit y acepto las equivalencias.

Se mutaron solo copias temporales. Baselines temporales antes/despues:
78 backend, 80 processor, cuatro en seguimiento vectorial. Mutaciones SQL
en SQLite; Green completo separado sobre CockroachDB. Los 91 archivos Python
de producto y 98 hashes de producto/documentos permanecieron intactos.
Artefactos auxiliares locales: `%TEMP%/jup086-mutation-7s05kxzl/final-report.json`,
JUnit por variante, `classified-results.json` y seguimiento
`%TEMP%/jup086-mutation-0dv71kw_`. El reporte contiene sustitucion exacta,
comando, test que detecta cada mutante, salida, intentos previos y versiones.
No se incorporan herramientas o estado personal al repositorio.

## Gates Adicionales

| Validacion en esta ejecucion | Resultado | Exit |
| --- | --- | ---: |
| Frontend, sin cambios | 235 PASS, 39 archivos | 0 |
| Azure cost API | 59 PASS | 0 |
| Gobernanza/topologia Node | 91 PASS | 0 |
| Colaboracion | 12 PASS | 0 |
| Frontend lint / tipos / build | PASS; aviso heredado de bundle >500 kB | 0 |
| OpenSpec estricto tras sincronizar docs | 34/34 | 0 |
| Trazabilidad | 11 cambios | 0 |
| Higiene antes de este archivo | 647 archivos | 0 |
| Corpus y bateria JUP-069 | PASS; 28 consultas/7 categorias, no respuestas LLM | 0 |
| Formato del diff | PASS | 0 |

Total de casos distintos de estas suites y el primer Green: **1271**.
No incluye repeticion de suites, selecciones, mutantes, OpenSpec o smoke.
No es CI remoto; los siete checks de GitHub se comprobaran tras publicar.

Comandos adicionales: `corepack pnpm install --frozen-lockfile`;
`corepack pnpm --filter @finops/frontend test`, `typecheck`, `lint`, `build`;
`python -B -m pytest -p no:cacheprovider tests -q --basetemp <unico>`
desde Azure cost API; `node --test tools/*.test.mjs` (en PowerShell se
expandio la lista de archivos); `python -B -m unittest discover -s
tools/collaboration/tests -v`; `corepack pnpm openspec:validate`;
`node tools/jup-check.mjs --all`; `node tools/jup-cleanup-check.mjs`;
`node tools/assistant-corpus.mjs validate`;
`node tools/validation-questions.mjs validate`; `git diff --check`.
Instalaciones aisladas de requisitos ya declarados, sin cambios a dependencias
o lockfile. Los avisos de lint antiguos no se presentan como corregidos aqui.

## Arranque Y Smoke Linux

Red Docker interna propia, cinco contenedores desechables, sin servicios
compartidos ni puertos publicados efectivos. Dockerfiles actuales, dependencias
cacheadas, usuario no privilegiado, aplicaciones read-only y datos temporales.
Backend arrancado antes de processor: no demuestra arreglada la carrera
entre migradores de JUP-096.

```text
docker build --pull=false --tag jup086-smoke-20260924-backend:local apps/backend
docker build --pull=false --tag jup086-smoke-20260924-processor:local apps/processor
docker exec jup086-20260924-runtime-backend python -B /validation/smoke.py --base-url http://localhost:8000 --document /validation/document.md --tenant tenant-core --tenant tenant-growth --timeout 90
```

Script existente `scripts/smoke_document_ingestion.py` y corpus publico montados
read-only. Exit 0: login HTTP 200, dos ingestas HTTP 202 completadas en dos
tenants del mismo usuario demo; dos documentos, **38 chunks y 38 embeddings**
mock de dimension 8, metadata preservada. SHA-256 del contenido:
`de44836434bb9b7522d4fc3a1128b2cb97f08d7a2af8a916f5e894a7d9f185c0`.
Los usuarios distintos y los negativos corresponden a las suites de integracion,
no a este smoke positivo.

Backend y processor healthy; ambos `/metrics` HTTP 200. Processor `/health`:
`{"status":"ok","services":{"database":"ok","rabbitmq":"ok","vector_store":"ok"}}`.
Los 14 archivos de producto modificados coincidieron por SHA-256 con la imagen
en ejecucion. Imagen backend
`sha256:1fc9bd5c4dd396b10b01c61b09d2f76424a655cd74983dc477fcdacff340f31d`;
processor `sha256:0c62cae85cd81b5c13696b43235508eb3efba2087ba8c0081935451f11d38718`.
Estos hashes y resultados son anteriores a la remediacion del reviewer.

## Limites Y Pendientes

RF-086-001/002 corregidos y re-revisados. RF-086-003 sigue Open con aplazamiento
expreso aprobado por Paris; no confundir esa disposicion con su correccion
ni con aprobacion final post-QA o autorizacion de publicacion.
RF-085-002 queda abierto fuera de alcance: sin cambios ni garantia de estabilidad
del reloj. No se cierra JUP-035 por la normalizacion JSONB de la lectura tocada.
No se implementan KPIs JUP-026, tools JUP-084, gestor tenant-suscripcion,
nuevas identidades, migraciones, dependencias o cambios frontend.
CLI permanece administrativo de confianza. No atomicidad distribuida entre
stores, cancelacion inmediata en curso ni politica nueva de retries.
No commit, push, PR, cambios en Trello, merge o archivado autorizados.

## Remediacion Y Resultado Actual

Tester anadio `tests/test_tenant_isolation_malformed_queue.py` antes del fix:
22 casos, **15 FAIL semanticos / 7 PASS / 0 SKIP**, exit 1. Doce fallos por
surrogates high/low en id, tenant y creador sobre SQLite/Cockroach; tres por
profundidad JSON, con broker real. Seis controles UTF-8 validos y un control
de transporte transitorio pasaban. Un error inicial de fixture fue corregido
y excluido del Red. Baseline focalizada anterior: cinco PASS.

Coder cambio solo `app/tasks/ingest.py` y `app/clients/rabbitmq_queue.py`:
UTF-8 estricto antes de SQL y captura de `RecursionError` al decodificar,
sin restriccion ASCII/UUID. Nuevo modulo: 22 PASS; regresion jobs/ingest/
worker/metricas: 76 PASS, sin skips, exit 0. Comandos desde processor:

```text
python -B -m pytest -p no:cacheprovider tests/test_tenant_isolation_malformed_queue.py -q --tb=short --basetemp <unico>
python -B -m pytest -p no:cacheprovider tests/test_tenant_isolation_jobs.py tests/test_ingest_task.py tests/test_worker_tracing.py tests/test_ingest_failure_metrics.py -q --tb=short --basetemp <unico>
```

Tester repitio las suites completas con el comando y opt-ins descritos arriba:
**backend 412 PASS (50.906 s), processor 484 PASS (270.804 s)**, exit 0,
cero fallos/errores/skips. Processor: 304 existentes + 10 reconciliados + 148
tenant + 22 de remediacion. Total actual backend/processor: **896**; con las
397 pruebas adicionales de codigo no modificado: **1293 casos distintos**.
No sumar selecciones, repeticiones, smoke o mutantes.

Cinco mutantes nuevos, todos detectados por aserciones de comportamiento:
omitir encode, aceptar Unicode invalido, restringir a ASCII, retirar captura
de profundidad y omitir descarte. P05/P06/P21 reejecutados, todos detectados.
Acumulado: **65 distintos / 70 ejecuciones / 60 detectados / 5 equivalentes**,
sin supervivientes pendientes. Baselines TEMP 31 antes y 31 despues; despues
22 casos reales PASS sobre el producto original. Cero ediciones de producto
durante mutacion, 101 hashes producto/documentos intactos y guard PASS.

Reporte local `%TEMP%/jup086-mutation-2vp4ffjr/report.json`: comandos completos,
cwd, versiones, sustituciones y JUnit de cada intento. Runner auxiliar
`%TEMP%/jup086-mutation-findings-2.py`, Python 3.12.13. Reviewer contrasto
los ocho XML de mutacion y los JUnit completos; RF-086-001/002 Fixed local,
REVIEW_PASS tecnico. El resto de variantes conserva su evidencia anterior.

Smoke repetido tras reconstruir processor, imagen
`sha256:7c909207cd2c0bfb902ca2756f7210b76c6ea5eefa465d400e70230981a5a185`.
Los 14 hashes producto/imagen coinciden. El mismo script completa dos jobs
(`8e80a487-9b00-4c69-9aee-60e1a1feacc7` y
`d63ddc9e-7404-4d91-98de-b928a1d91014`), 38 chunks y 38 embeddings, exit 0.
Ambos health y metrics HTTP 200; processor health sigue sin conteos globales.
Validadores tras fixes: OpenSpec 34/34, trazabilidad 11, higiene 650 archivos,
diff check exit 0. No es CI remoto ni aprobacion humana.

## RF-086-003: Publicador Inactivo Heredado

Estado vigente: **Open, en alcance** desde la decision de Paris del 25/09,
registro 08:11:57 UTC. [Contrato propuesto](../../openspec/changes/jup-086-tenant-isolation-contract/design.md#rf-086-003-option2-contrato-propuesto)
y [ADR-0009](../adr/ADR-0009-rabbitmq-publisher-lifecycle.md), aun Proposed.
No hay correccion ni prueba funcional nueva. Se conservan debajo la observacion
del fallo y el aplazamiento historico del 24/09, ahora sustituido. La revision
y QA de la ampliacion permanecen pendientes, igual que la aprobacion final.

El primer intento del smoke anterior termino con exit 1: login 200, ingesta
503 a 20:48:57 UTC por `StreamLostError`/conexion cerrada. RabbitMQ habia
cerrado esa conexion a 20:07:34.829152 UTC por falta de heartbeats (timeout 60 s).
Job `b9d02dc1-8d02-49da-948a-70acd0fd4d3d`, tenant-core, `queued` sin publicar,
comprobado por SQL en la base desechable. El siguiente intento, sin cambios,
completo los dos jobs. El smoke positivo no borra el resultado negativo.

`git diff 3a1001db857191f7abb6bb025e2fe8b04a50fe56 --
apps/backend/app/services/rabbitmq_queue.py apps/backend/app/api/routes/jobs.py`
vacio (exit 0). El publicador reutiliza conexion, `ping()` usa otra y el
endpoint persiste antes de publicar. Reviewer clasifica Medium, preexistente
y fuera de alcance JUP-086. Paris responde **"aplaza el finding"**, registrado
el **24/09/2026 a 21:23:36 UTC**: aplazamiento **APPROVED**, fuera de JUP-086.
Permanece abierto, no se modifica ni declara resuelto. Riesgo conocido:
primer POST tras inactividad puede fallar 503 y dejar un job queued sin enviar.
Alcance futuro por acordar; no hay nueva JUP, persona o fecha asignados ni
actualizacion externa. No autoriza publicacion ni aprobacion final post-QA.

## QA Y Cierre Del Entorno Desechable

QA independiente anterior: **QA_BLOCKED_APPROVAL**, unico bloqueo de cierre la
disposicion entonces pendiente de RF-086-003. Primer intento interrumpido por limite de ejecucion
sin resultado; reanudacion completa los checks sin editar archivos.

- `corepack pnpm openspec:validate`: 34/34, exit 0.
- `node tools/jup-check.mjs --all`: 11 cambios, exit 0.
- `node tools/jup-cleanup-check.mjs`: 650 archivos, exit 0.
- `git diff --check 3a1001db857191f7abb6bb025e2fe8b04a50fe56`: exit 0.
- `node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs`: 19 PASS,
  exit 0; subconjunto de las 91 pruebas Node, no sumarlo a los 1293 casos.
- Inspeccion PowerShell inline de destinos Markdown y titulos de anclas:
  nueve documentos, 56 enlaces locales y ocho anclas, cero errores. No se
  consultaron destinos externos; no es un validador general de Markdown.
- 75 JUnit cotejados con los dos reportes: 896 PASS, cero fallos/errores/skips;
  65 variantes, 60 detectadas y cinco equivalentes. Sin repetir todo el lote.
- Guards qa-1/qa-2: cero cambios/violaciones. DoD automatizado code/qa exit 0;
  no sustituye QA_PASS ni las aprobaciones humanas.

Tras el aplazamiento aprobado: sincronizar documentos y verificar que los
hashes de producto/pruebas siguen iguales; QA no exige repetir suites sin
cambios de codigo. No hay aprobacion final ni publicacion autorizada.

La sesion principal retiro los ocho contenedores propios (tres de fixtures y
cinco del smoke) y su red interna, comprobando primero cada ID y etiqueta
de propiedad. Exit 0; imagenes, reportes y snapshots conservados. No se
limpiaron recursos compartidos, volumenes del usuario ni otros worktrees.
Los contenedores de prueba ya no estan ejecutandose; futuras pruebas reales
requeriran recrear infraestructura desechable, no usar las URLs antiguas.

## QA Historico Tras Aplazamiento Aprobado

Dictamen independiente: **PASS_WITH_APPROVED_EXCEPTIONS**. Alcance incremental
limitado a RF-086-003; no se modifica producto ni se repiten suites.
Nueve documentos consistentes; 31/31 fingerprints identicos entre snapshots
QA (14 archivos de producto y 17 de pruebas). Los 92 hashes de producto del
manifest del tester tambien coinciden. HEAD/base permanecen en `3a1001d`.

`corepack pnpm openspec:validate`: 34/34, exit 0. El primer intento termino
por EPERM de Corepack; repetido con ejecucion escalada, red deshabilitada y
sin instalaciones. `node tools/jup-check.mjs --all`: 11 cambios, exit 0.
`git diff --check 3a1001db857191f7abb6bb025e2fe8b04a50fe56`: exit 0.
DoD code/qa y guard QA exit 0, cero escrituras/infracciones.

Permanecen validas las 896 pruebas y 65 mutaciones acreditadas previamente.
RF-086-003 sigue Open, aplazado por Paris, sin reparar el riesgo descrito.
La aprobacion humana post-QA sigue PENDING; no se ejecuta DoD final ni se
publica rama, PR o tracker. Sin procesos QA pendientes.
