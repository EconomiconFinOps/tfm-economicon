# Revision JUP-085

## Autorizacion De Publicacion Para Revision

Registro del 23/09/2026 a 17:15:32 UTC. Paris Arcos Martin solicita:
"ok publica, pr y hazme el mensaje para pedir aprobacion y merge en el grupo".
Autoriza commit, push de la rama JUP-085 y PR contra `develop`. Se publica
como borrador para revisar el resultado y los pendientes, no como entrega
lista para merge. Esta autorizacion sustituye las referencias anteriores a
publicacion no autorizada, sin reescribir las validaciones historicas.

QA_PASS incremental de tolerancia JWT y REVIEW_PASS de codigo conservados.
QA_BLOCKED_ENV global y RF-085-002 Open siguen visibles; no se interpreta
esta orden como aceptacion formal del riesgo ambiental ni aprobacion final
post-QA. El reloj se deja intacto. Aprobacion humana final, revision del grupo
y CI remoto pendientes al preparar la publicacion. No se autoriza ejecutar
merge, archivar OpenSpec ni actualizar Trello. Roles originales conservados,
sin atribuir pairing, revision o validacion humana no acreditados.

## Incremento Actual: Leeway JWT De 5 s

**REVIEW_PASS incremental**, sin nuevos defectos bloqueantes. Base `3a08d60`
mas diff local, sin commit/PR. Aprobacion especifica de Paris registrada en
proposal.md el 23/09/2026 a 16:01:44 UTC: tolerancia fija 5 s, dejar relojes
intactos. No se atribuye a la aprobacion general previa la eleccion de cero.

Revision del cambio de una linea `jwt.decode(leeway=5)`, tests afectados y
cuatro documentos OpenSpec. Se conservan firma/HS256, claims/tipos estrictos,
usuario actual, TTL, `exp > iat`, JUP-097 y CORS. Futuro inclusivo hasta 5 s
y gracia de expiracion exclusiva de 5 s; el riesgo de esa gracia fue explicado.

Baseline 245 PASS; Red 252 PASS/7 fallos semanticos; Green y regresion final
259 PASS (+14 netos), 12 warnings existentes. Siete mutantes detectados,
cero equivalentes/supervivientes. BE1 deja de ser equivalente y se detecta
en dos casos; la clasificacion previa se conserva solo como historia.
Guards de cada fase PASS; reviewer no escribio en repositorio. Revision de
resultados backend/mutacion, sin repetir suites ajenas ni sumarlas de nuevo.

Pasada propia real 8/8 entre 16:23:15.692 y 16:23:20.082 UTC: login,
preflight, billing, recarga, logout, JWT invalido/expirado y origen denegado.
Fingerprints coincidentes, firma y TTL 28.800 s correctos. Imagen backend
`03904ecbf021dcb3c798247ed56a6e0f46dd367af8cfc67b20e095a262586c6a`,
hash de security dentro del contenedor igual al local. Relojes no operados.

**QA_PASS incremental**, registrado a 16:33:02.775 UTC: OpenSpec 33/33,
trazabilidad, higiene, diff y preparacion PASS. QA cotejo 55 hashes backend,
48 enlaces, Red/Green/mutacion y evidencia de navegador sin repetir suites
ni runtime; guard sin escrituras. RF-085-002 High/out
of scope permanece Open; esta pasada puntual no levanta QA_BLOCKED_ENV ni
prueba estabilidad sostenida. Se retira la propuesta de ajuste persistente
por decision del usuario. El leeway no corrige CockroachDB; no se atribuye
el 500 a esa causa sin prueba, ni error horario obsoleto a un fallo de app.
RF-087-001/RF-095-001 y otros hallazgos conservan su estado. Ver
[evidencia incremental](../../../docs/evidence/JUP-085-validation.md#incremento-actual-tolerancia-jwt-de-5-s).

Gate post-QA humano PENDING: decision, aprobador y fecha final pendientes.
No implica pairing/validacion humana, publicacion, merge, archivo ni tracker.

## Estado Previo: 2026-09-23 (Historico, Margen Cero)

**REVIEW_PASS de codigo; QA_BLOCKED_ENV por caducidad de sincronizacion Windows.** Base
`3a08d60ddd48a8693a95025948bc941a0e54b7de` mas diff local en
`feat/JUP-085-auth-session-contract`, sin commit nuevo ni PR. El gate pre-code
de Paris a las 13:05:53 UTC sigue vigente; no se ampliaron requisitos.

RF-085-001 esta corregido localmente y revisado: clearSessionMutations elimina
referencias de cache, aplica gcTime Infinity solo a objetos retirados y cancela
su timer con destroy. El desmontaje de observadores ya no rearma esos timers.
Se mantienen el descarte de respuestas antiguas, la politica de JUP-097 y todos
los caminos de limpieza. No se desactiva el GC de mutaciones activas.

El reviewer cotejo 135 hashes; backend 245 y frontend 235 correctas. Las dos
regresiones nuevas fallaron antes de la correccion y pasan despues. Mutacion
dirigida final: 37 variantes, 35 kills semanticos, 2 equivalentes justificados,
sin supervivientes pendientes. Guard de cada ronda sin infracciones.

La primera ejecucion independiente del navegador paso 8/8 entre saltos de reloj,
con firma y TTL 28.800 s correctos, y token emitido/persistido/transmitido
identico por fingerprint. No borra las dos ejecuciones anteriores fallidas
(login 500, recarga 401). CockroachDB registra retrocesos de 2-3 s repetidos:
RF-085-002 bloqueo QA runtime fiable; no exigio cambiar el contrato JWT.

Tras autorizacion explicita de Paris se resincronizo Windows con su fuente
existente sin reinicios ni cambios de configuracion o producto. Re-review
ambiental entre 15:17:58.480 y 15:21:03.649 UTC: 741 muestras, 185.169 s,
cero retrocesos y maxima divergencia realtime/monotonico 0.729 ms. Tres
pasadas de ocho escenarios reales: 8/8 cada una, separadas por 35 s; sin
nuevos eventos de reloj CockroachDB ni 500. Windows leap 0, stratum 5, error 0.
Guard PASS sin escrituras. RF-085-002: mitigado localmente, durabilidad abierta
durante el sondeo prolongado del host y futuras suspensiones; no es solucion
permanente ni excepcion. Permitio retomar QA. Ver evidencia para comandos,
mediciones, transitorios y conservacion de todos los fallos anteriores.

RF-087-001/RF-095-001 tienen correccion CORS implementada y evidencia funcional,
pero conservan Open hasta completar QA estable. RF-087-002 y los otros
residuales ajenos no se cierran. Ver [evidencia actual](../../../docs/evidence/JUP-085-validation.md).

Limites: las promesas abandonadas retenidas externamente siguen pending; no se
aborta transporte ni se deshacen operaciones del servidor. Retries de mutaciones
programados antes de logout requeririan otro analisis si se habilitan en el
futuro; produccion los mantiene deshabilitados. Los query retries de JUP-097 no
cambian. BE1 y FE1 son equivalentes por las razones de la evidencia, no
excepciones de comportamiento. Mutacion dirigida, no exhaustiva.

La documentacion/evidencia se consolida tras este dictamen para el control QA.
QA final **BLOCKED**; gate post-QA humano **PENDING**, sin excepcion aprobada.
No se acredita pairing, revision o validacion humana; no hay autorizacion de
publicacion, merge, archivo ni cambios de tracker.

## Revalidacion QA Tras Mitigacion: 23/09

**QA_BLOCKED_ENV**, gate registrado a 15:35:35.747 UTC: Windows regreso a
error 2 (informacion horaria obsoleta), confirmado a 15:34:54.304 UTC.
No reaparecieron retrocesos ni defectos funcionales. La pasada QA real fue
8/8 entre 15:30:56.991 y 15:31:01.093 UTC; 741 muestras durante 185.172 s
sin retrocesos, maxima divergencia 3.091 ms y cero nuevos avisos CockroachDB.
La sincronizacion automatica mantenida sigue sin acreditarse; RF-085-002
vuelve a Open con mitigacion temporal documentada, sin excepcion.

OpenSpec 33/33, trazabilidad, higiene, corpus y whitespace PASS; ocho docs,
40 enlaces, 135 fuentes, 140 artefactos y cinco hashes coincidentes. Suite
899/34 y mutacion revisadas, no reejecutadas; guard QA PASS sin escrituras.
El orquestador solicito entonces ajustar persistentemente el sondeo Windows.
No aplicado; la decision posterior de Paris excluye esa intervencion. Esta
ronda historica no acredita el incremento JWT ni autoriza publicar o cerrar.

## Auditoria QA Anterior Del 23/09

Resultado independiente **QA_BLOCKED_ENV**. OpenSpec 33/33, trazabilidad,
higiene (615 archivos), corpus y whitespace: exit 0. Verificados ocho
documentos/31 enlaces, 135 hashes de fuente, 140 hashes de artefactos y cuatro
publicados. Suites y mutacion cotejadas, no reejecutadas por QA. Sin escrituras
ni nuevas incidencias de producto. Una omision de registros consolidados de
limites se completo a partir de las comparaciones PASS ya ejecutadas; el control
de preparacion para QA paso despues, sin convertirlo en QA funcional PASS.
RF-085-002 bloqueaba ese resultado, sin excepcion ni gate humano final.

## Primera Revision Del Residual: 2026-09-23 (Historica)

**REVIEW_FAIL** sobre `3a08d60ddd48a8693a95025948bc941a0e54b7de` mas diff
local, 30 archivos revisados incluidos los no versionados. RF-085-001, Medium
en alcance, bloquea QA: las promesas abandonadas de api.ts dejan mutaciones
pending y su GC reprograma temporizadores indefinidamente tras logout, aun
con cache vacia. Reproducido durante tres ciclos en diagnostico aislado y en
Chromium con la UI real/respuestas sinteticas; no se ejecuto ingesta backend.
Debe corregirse sin permitir callbacks/retries de otra generacion.

El reviewer cotejo 135 hashes y la evidencia de backend 245, frontend 233,
CORS 76 con cada version Settings y ocho recorridos reales. No reejecuto esas
suites. Acepto las dos equivalencias de mutacion; 34 kills dirigidos no
detectaban este defecto de ciclo de vida. Guard sin escrituras: PASS.
No se establecieron otros bloqueos JWT/CORS/contratos dentro del alcance.

Una configuracion hipotetica con retries de mutaciones habilitados puede
recapturar generacion al reintentar trabajo anterior. Produccion los tiene
deshabilitados; no se agrega ese escenario como requisito nuevo ni se cambia
la politica de query retries de JUP-097. El transporte no se aborta y logout
no revoca operaciones ya recibidas por el servidor.

Se retorna a tester para regresion Red y a coder para la correccion acotada.
Revision posterior, evidencia consolidada, QA final y aprobacion humana:
**PENDING**. Sin publicacion, merge, archivo o participacion humana acreditada.

## Historial Previo

## Estado

- Actualizacion: 2026-09-10, 19:15 UTC.
- Resultado tecnico: **REVIEW_BACKEND_PASS**, sin hallazgos bloqueantes en el
  subconjunto backend aprobado. No equivale a cierre completo de JUP-085.
- Base: `1ff8e071f83a58f630c496740d712e8c0e2cc443`, `origin/develop`.
- Rama: `feat/JUP-085-auth-session-contract`; cambios locales sin commit ni PR.
- Aprobacion previa de Paris: [proposal.md](proposal.md), 18:30:51 UTC.
- Evidencia: [JUP-085-validation.md](../../../docs/evidence/JUP-085-validation.md).
- Resultado QA: **QA_BACKEND_PASS**; frontend, QA integral y aprobacion final pendientes.

## Alcance Revisado

Cuatro archivos de producto: schema de login, seguridad JWT, TTL y dependencia
de identidad. Cuatro archivos de pruebas: schema, utilidades JWT, API auth y
configuracion TTL. Se revisaron tambien los escenarios y el diff completo,
incluido el nuevo test HTTP sin seguimiento Git.

Password no vacia y literal, claims obligatorios/estrictos, HS256 y reloj,
Bearer unico sin distinguir mayusculas, perfil directo actual, usuario eliminado
y errores genericos. Fallos de DB conservan el error de servicio sanitizado.
No se modificaron get_active_tenant, rutas, seed, DB, secretos, .env, CI,
dependencias ni frontend. JUP-053 se conserva; sin ADR o migracion nuevos.

## Gates Backend

| Comprobacion | Resultado observado |
| --- | --- |
| OpenSpec previo y tras aprobacion | 29/29, exit 0 |
| Trazabilidad JUP-085 | PASS, exit 0; completitud estructural, no funcional |
| Red anterior a producto | 22 fallos de comportamiento / 124 correctos; exit 1 |
| Green seleccionado con regresiones | 146 correctos, exit 0 |
| Backend completo | 169 correctos, exit 0; repetido en revision independiente |
| Mutacion dirigida | 12 detectados, 1 equivalente, 0 supervivientes no equivalentes |
| Limites de escritura | Preparacion, aprobacion, tests, codigo, mutacion y revision sin infracciones |
| Integridad tras mutacion | 54 archivos Python identicos antes/despues y contra el disco revisado |
| Higiene antes de estos dos documentos | 495 archivos, exit 0 |
| Whitespace | git diff --check, exit 0 |

Los 146 casos seleccionados estan incluidos en los 169 del backend, no se
suman. Hay 54 casos nuevos. Ningun placeholder frontend se cuenta como prueba.

## QA Backend

QA independiente sin bloqueos en el subconjunto backend: 169 pruebas correctas,
29 validaciones OpenSpec, trazabilidad, higiene de 497 archivos y whitespace,
todos con exit 0. Se comprobaron 8 enlaces locales en los 6 documentos de la
entrega, los hashes de 54 archivos Python y los 3 hashes de evidencia local.

El resultado se registro el 2026-09-10 a las 19:15:39 UTC. No acredita cierre
integral, preparacion para PR ni aprobacion humana. El registro posterior de
este resultado solo actualiza documentacion, sin cambios de producto o tests.

## Hallazgos Y Limites

Revision tecnica automatizada independiente sin hallazgos accionables dentro
del alcance backend. Esto no acredita revision, pairing ni validacion humana
de los responsables propuestos en Trello.

Se probaron las versiones instaladas indicadas en la evidencia, no todo el
rango permitido por requirements. Las 12 advertencias observadas se refieren
a claves sinteticas cortas y al adaptador datetime de SQLite; no son errores
de la suite ni cambios en credenciales de runtime.

Mutacion dirigida, no exhaustiva. El caso equivalente conserva la firma,
claims requeridos/tipos y `iat <= now < exp`, lo que ya implica `exp > iat`.
No se cuenta como detectado ni requiere omitir una conducta no cubierta.

## Pendientes Integrales Registrados El 10/09 (Historicos)

- PR #29/JUP-087 estaba abierta, sin fusionar y sin conflictos a las 18:30 UTC,
  head `746fd5d`. Consumir solo su resultado integrado y revalidado.
- Implementar y probar restauracion /me, invalidacion 401, logout y respuestas
  tardias del frontend. Preservar el trabajo de JUP-087 y coordinar JUP-095.
- Completar mutation frontend, lint, build, typecheck, QA funcional integral,
  CI, revision humana y las aprobaciones/operaciones de cierre correspondientes.
- RF-053-004 permanece en JUP-020; esta entrega no demuestra ingesta documental
  completada. Autorizacion por tenant sigue en JUP-086.

## Aprobacion Post-QA

**PENDING.** No se ha solicitado ni registrado aprobacion final de JUP-085.
Publicar PR, fusionar y archivar requieren autorizacion explicita independiente.

## Reconciliacion Documental Del 23/09/2026

Revision independiente: **REVIEW_PASS**, limitada a proposal/design/tasks/spec
reconciliados y coherencia del plan externo. Comparacion por lectura contra
`develop` en `3a08d60ddd48a8693a95025948bc941a0e54b7de`; este worktree sigue en
`1ff8e071f83a58f630c496740d712e8c0e2cc443`, ocho commits por detras. No se ha
fusionado, publicado ni revalidado el producto resultante.

- Se conserva JUP-097: `/me` y `/tenants` en paralelo, tambien tras login,
  y logout ante cualquier error de la query actual de `/me`, incluidos fallos
  transitorios. No se cambia su politica de retries ni su queryKey por inferencia.
- Paris autoriza respetar ese comportamiento y actualizar documentacion. El gate
  pre-code del residual revisado sigue **PENDING**; el permiso del 10/09 es historico.
- CORS (`RF-087-001`/`RF-095-001`), validacion runtime, limpieza/generacion y
  `401` global fuera de `/me` siguen pendientes de decision y comprobacion.
- PR #29/JUP-087, #36/JUP-095 y #42/JUP-097 ya estan integradas en upstream.
  RF-090-003 esta Fixed por JUP-097; RF-053-004 se corrigio en JUP-020/PR #34.
  No son reparaciones ni pruebas nuevas de esta entrega.

| Comprobacion documental del 23/09 | Resultado |
| --- | --- |
| Guard spec-planner | PASS; solo cuatro documentos autorizados |
| Guard reviewer | PASS; sin escrituras |
| OpenSpec estricto | 29/29, exit 0 sobre este worktree antiguo |
| Trazabilidad JUP-085 | PASS, exit 0; estructura, no cierre funcional |
| Higiene | 497 archivos, exit 0 |
| Whitespace | `git diff --check`, exit 0 |
| Enlaces Markdown relativos | 8 destinos comprobados en 6 documentos |
| Integridad | 179 archivos de apps/pruebas sin cambios durante esta actualizacion |

Pruebas de producto y mutacion nuevas: **N/A en esta actualizacion exclusivamente
documental**. No se aplica esa excepcion a la entrega funcional JUP-085 ni se
declara su DoD completo. Las 169 pruebas y mutacion anteriores siguen siendo
evidencia del 10/09. QA documental independiente de esta reconciliacion:
**QA_DOCS_PASS** el 23/09, tras comprobar los seis documentos, OpenSpec 29/29,
trazabilidad, higiene de 497 archivos, whitespace y 8/8 enlaces relativos,
todos con exit 0. Guard QA: cero escrituras e infracciones. Los hashes y
readbacks externos son evidencia del coordinador, no reejecucion del agente QA.
El DoD funcional sigue incompleto; QA integral y aprobacion final: **PENDING**.
