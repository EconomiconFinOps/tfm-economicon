JUP: JUP-085
Trello: https://trello.com/c/Z8M443Hu

## Why

El contrato preparado en JUP-088/PR #19 ya esta integrado. JUP-085 completa
el residual observable de login, perfil, expiracion y logout de la demo MVP.
El incremento de tolerancia JWT de 5 s autorizado en el addendum siguiente
esta implementado: Red/Green y mutacion completados, REVIEW_PASS incremental;
QA_PASS acotado al incremento, registrado el 23/09 a las 16:33:02.775 UTC.
El residual aprobado de sesion y CORS esta implementado en el worktree sobre
HEAD `3a08d60` mas diff local: REVIEW_PASS de codigo; QA_BLOCKED_ENV por
RF-085-002, mitigacion temporal insuficiente; gate humano pendiente. Estado
actual en [review.md](review.md) y [evidencia incremental](../../../docs/evidence/JUP-085-validation.md#incremento-actual-tolerancia-jwt-de-5-s).
El gate pre-code del 23/09 esta resuelto por el registro literal al final;
ADR-0007 Accepted, sin cambios. Resultados anteriores al incremento de 5 s: backend 245 y frontend 235 PASS;
899 PASS / 34 SKIP totales, 215 casos residuales nuevos. Mutacion: 37 variantes,
35 detectadas, 2 equivalentes, 0 pendientes. RF-085-001 Fixed local, sin integrar;
reviewer cotejo 135 hashes y guard PASS. Detalle en [tasks.md](tasks.md). Esta
actualizacion solo sincroniza estado; no cambia el contrato ni reejecuta
producto. Los resultados previos no validan la nueva tolerancia; su evidencia
propia y el 8/8 de navegador del reviewer constan en los enlaces anteriores,
sin levantar el bloqueo ambiental ni cerrar hallazgos CORS.
Los 169 tests backend
(54 nuevos) y 13 variantes de mutacion (12 detectadas, 1 equivalente) de
[review.md](review.md) son evidencia historica del 2026-09-10, no reejecutada
ni validacion de la base actual o de este alcance revisado.

Fuentes leidas el 2026-09-10: descripcion completa de la tarjeta oficial del
export `CawMVPoy - economicon (10-09).json`, ultimo snapshot
2026-09-10 16:21:48 UTC, y seccion JUP-085 del plan de implementacion v1.3,
revisado el 2026-09-10. Trello oficial en vivo no fue accesible; el export es
una fuente fechada, no una comprobacion actual ni una aprobacion.

Base inspeccionada el 10/09: `origin/develop`,
`1ff8e071f83a58f630c496740d712e8c0e2cc443`, rama
`feat/JUP-085-auth-session-contract`, inicialmente limpia. Incluye JUP-053/PR #33.
Se conservan los roles propuestos en la tarjeta: Lucia Mateo, liderazgo;
Paris Arcos Martin, pairing/coautoria; Victor Mendez, revision; Alejandro Aguado,
validacion, pruebas y documentacion. No se acredita participacion realizada.

### Reconciliacion documental del 23/09/2026: antecedente pre-code

La instruccion recibida del usuario es respetar JUP-097 ("respetamos jup 097
es mas restrictivo") y actualizar la documentacion ("actualiza lo que sea
necesario"). Se conserva la politica integrada: `/me` y `/tenants` arrancan
en paralelo y cualquier error de la query de revalidacion `/me`, incluso
transitorio, llama a logout. "Mas restrictivo" describe esa politica de salida;
no acredita mayor seguridad ni constituye aprobacion general para implementar
el residual revisado. No se retira `/me` ni se revierte JUP-097.

Lectura anterior a la implementacion de la raiz principal, solo lectura: `develop` en
`3a08d60ddd48a8693a95025948bc941a0e54b7de`, con JUP-087/PR #29 (`1de7b16`),
JUP-095/PR #36 (`cb4edc3`) y JUP-097/PR #42 (`3a08d60`) integrados. El worktree
JUP-085 estaba en `1ff8e071`, ocho commits por detras. Posteriormente se avanzo
por fast-forward a `3a08d60`, preservando byte a byte los 15 archivos sucios
existentes entonces; la raiz principal develop quedo limpia, segun el orquestador.

Fuentes actuales: `apps/frontend/src/layouts/SessionGate.tsx`,
`services/api.ts`, `pages/LoginPage.tsx` (las dos ultimas bajo
`apps/frontend/src/`), `openspec/specs/frontend-api-layer/spec.md` y el archivo
`openspec/changes/archive/2026-09-21-jup-097-reconcile-api-layer/`.
El bloque de aprobacion del 10/09 permanece literal como registro historico:
su orden secuencial y sus referencias a PR #29 describen aquella propuesta,
no el comportamiento integrado del 23/09. No aprueba el residual revisado.

## Addendum: Tolerancia JWT De 5 Segundos

Registro documental: 2026-09-23 16:01:44 UTC. Instruccion explicita de Paris:

> ok implementa la medida de tolerancia y deja el reloj de cockrachDB

La autorizacion recibida se limita a 5 s mediante PyJWT: admitir `iat` hasta
`now + 5` inclusive y `exp > now - 5` (rechazar igualdad), con el mismo margen
nativo para `nbf` si aparece. Firma HS256, claims estrictos/requeridos,
usuario, TTL emitido y `exp > iat` se conservan. Por tanto puede aceptarse un
token menos de 5 s despues de expirar; `iat=now+4, exp=now-4` sigue rechazado.
No se atribuye el anterior margen cero a una eleccion humana especifica.

Alcance del incremento completado: `apps/backend/app/core/security.py` y pruebas focalizadas ya
existentes, segun design/tasks. Sin config nueva, dependencias ni endpoints;
Windows/WSL/Docker/reloj DB quedan excluidos por instruccion del usuario.
RF-085-002 sigue Open ambiental: esta tolerancia no arregla ni exceptua ese
riesgo. CORS/JUP-097 intactos; sin QA final, PR, merge, archivo, tracker o
participacion humana inferidos. Red/Green, mutacion y revision completados;
QA_PASS incremental registrado, sin levantar el bloqueo global. Este pase no
cambia registros de aprobacion.

## What Changes

- Conservar login con envoltorio `user` y `/me` con perfil directo; rechazar
  password vacia con `422`, credenciales incorrectas con `401` generico.
- Emitir y exigir `sub`, `iat`, `exp`, firma HS256 y TTL positivo configurable;
  cerrar casos de claims ausentes/malformados y usuario eliminado sin `500`
  causado por entrada del token ni detalles sensibles en errores. Aplicar el
  margen nativo de 5 s del addendum, sin cambiar emision ni relacion exp/iat.
- Conservar el consumidor `/me` y la identidad de servidor expuesta por
  `SessionGate`, ya entregados por JUP-097. Perfil y tenants se consultan en
  paralelo tambien al entrar al armazon tras login; no serializar el bootstrap.
- Mantener logout ante cualquier `profileQuery.isError`, incluidos red,
  `403`, `422`, `5xx` y parsing, sin convertirlos en errores recuperables que
  conserven sesion. No cambiar retries/refetch ni exigir logout antes de que
  la query entre en error como parte de esta reconciliacion documental.
- Implementar, conforme al gate residual ya registrado, validacion runtime acotada de
  storage/login/perfil, `401` global para consultas y mutaciones fuera de
  `/me`, limpieza y proteccion frente a respuestas de sesiones anteriores.
  Conservar sesion ante red/`403`/`422`/`5xx` solo fuera de `/me`; los errores
  estructurados no pueden debilitar su politica estricta.
- Reconocer que el queryKey de perfil ya incluye el token. No introducir una
  prohibicion de esa clave ni una migracion de caches como cambio implicito.
- Reutilizar las garantias de secretos y seed ya entregadas por JUP-053 y el
  runner/casos ya integrados de JUP-087, adaptados al armazon de JUP-095/097.
- Desarrollar la opcion 1, CORS en backend, elegida por Paris el 23/09/2026
  mediante respuesta "1", dentro de la propuesta JUP-085; proxy de mismo origen
  no seleccionado. Parametros, archivos y alcance completo aprobados en el
  registro del 23/09; implementados y REVIEW_PASS, con QA_BLOCKED_ENV. ADR-0007 Accepted.

## Capabilities

### New Capabilities

- `demo-auth-session`: contrato verificable del ciclo de autenticacion y sesion
  propia utilizado exclusivamente por la demo del MVP.

### Modified Capabilities

- None. Se respeta `frontend-api-layer` integrado por JUP-097 y se reutilizan
  las garantias de credenciales de JUP-053; no se modifican sus especificaciones.

## Impact

Esta actualizacion solo modifica proposal, design, tasks y el delta de este
cambio. ADR-0007 y su politica CORS no se editan. Preserva los cambios
previos de producto/pruebas y no edita review, evidencia ni hallazgos. No ejecuta
producto, sincroniza ramas ni cambia aprobaciones o estado externo.

JUP-053 es dependencia satisfecha: secretos solo en runtime, seed por opt-in,
password manual y cuentas existentes sin sobrescrito. No se reimplementan seed,
rotacion, redaccion o configuracion de secretos. Se mantiene TTL por defecto de
480 minutos; exigir `iat` ocasionara re-login de tokens demo antiguos sin ese
claim, sin migracion de datos ni revocacion remota.

[PR #29/JUP-087](https://github.com/EconomiconFinOps/tfm-economicon/pull/29)
ya esta fusionada en upstream; tambien JUP-095 y JUP-097. Esa base ya se
consume en HEAD `3a08d60`, con validaciones frescas comunicadas por el
orquestador; el PASS del 10/09 sigue separado como historia.
RF-090-003 figura Fixed por JUP-097: no se
reabre ni se atribuye su cierre a este trabajo.

El backend del worktree ya configura CORS; el commit base upstream no lo hacia.
RF-087-001 y RF-095-001 siguen Open hasta QA runtime estable. [design.md](design.md)
concreta la direccion elegida: middleware existente, allowlist JSON de origenes
exactos vacia por defecto, GET/POST, cabeceras del cliente y sin cookies.
[ADR-0007](../../../docs/adr/ADR-0007-backend-cors-policy.md) esta Accepted;
incluye limites de errores observables y compatibilidad HTTPS/HTTP. Se propone
dentro de JUP-085, sin nueva tarjeta ni asignaciones. Antecedente del 23/09, antes de mitigar el reloj:
Chromium normal sobre Compose aislado de cinco servicios registro login 500;
3 PASS y recarga 401; un 8/8 entre saltos de reloj con fingerprints de token
coincidentes, firma y TTL validos. Ese 8/8 no demuestra estabilidad.

RF-085-002 vuelve a Open: mitigacion temporal, sin sincronizacion mantenida.
El usuario excluye intervenir en Windows/WSL/Docker/reloj DB. Solo autoriza
la tolerancia JWT descrita; no resuelve RF-085-002 ni es excepcion de QA.
JUP-097 permanece intacto.
El registro del 10/09 sigue siendo historico; el gate del residual fue resuelto
por Paris a las 13:05:53 UTC del 23/09, sin cambiar roles ni habilitar publicacion.

Fuera de alcance: autorizacion/aislamiento por tenant de JUP-086, port visual
JUP-095, pipeline JUP-020 y RF-053-004, migraciones, cambios de CI, nuevas
dependencias, OAuth/OIDC, IdP, refresh, MFA, revocacion remota y hardening de
produccion. JUP-086 consume la identidad actual resuelta por este contrato.

<details>
<summary>HISTORICAL 2026-09-10 (10/09): Pre-code Approval del alcance original</summary>

Registro historico literal. No autoriza el alcance residual revisado el 23/09;
las habilitaciones y limites siguientes corresponden exclusivamente al 10/09.

## Pre-code Approval: APPROVED

Paris Arcos Martin aprobo iniciar el trabajo el 2026-09-10; decision registrada
a las 18:30:51 UTC tras presentar el alcance y sus consecuencias. Su respuesta
explicita confirma comenzar ("arranca"). La aprobacion tecnica no cambia los
roles de la tarjeta oficial.

Decision aprobada: alcance residual y escenarios de este cambio, incluida
restauracion mediante perfil directo de `/me` antes de tenants, limpieza ante
`401` ligada a la generacion de sesion y re-login de tokens anteriores sin
`iat`, manteniendo el TTL actual y el logout local sin revocacion. Se habilita
el ciclo de pruebas e implementacion backend; los limites de design.md siguen
vigentes. Las menciones a aprobacion pendiente en el diseno describen la
propuesta presentada, resuelta por este registro sin cambiar sus requisitos.

Validacion previa: OpenSpec estricto 29/29, trazabilidad JUP-085, higiene y
comprobacion independiente de limites de escritura correctas; cuatro documentos
OpenSpec modificados y ningun cambio de producto antes de esta aprobacion.

Recomprobacion del 10/09 a las 18:30 UTC: develop sigue en `1ff8e07`.
PR #29 sigue abierta y sin fusionar, ahora sin conflictos (`mergeable=true`),
head `746fd5dce2e3ef75c760f5095beda64af25fee3a`. La inspeccion anterior de
`1f2d809` queda como antecedente, no como estado actual de esa PR.

Condicion previa al Red/Green frontend: JUP-087 reconciliada con JUP-053,
integrada y validada, con commit consumido registrado. No se solicita autorizar
esa integracion desde este cambio.

Esta aprobacion no autoriza publicar PR, fusionar, archivar ni ampliar alcance.
No acredita participacion tecnica, pairing o revision humana realizados, ni
cierra RF-090-003 por anticipado. El gate final de QA sigue pendiente.

</details>

## Pre-code Approval: APPROVED (2026-09-23)

Paris Arcos Martin responde "aprobado" a la propuesta concreta presentada tras
validacion. Registro: 2026-09-23 13:05:53 UTC. Aprueba los parametros CORS,
ADR-0007 y el alcance residual de sesion de design.md: 401 global, limpieza y
descarte de respuestas antiguas, preservando consultas paralelas y logout ante
cualquier error de /me de JUP-097. Se aceptan los limites declarados de errores
externos a CORS y preflight sin metricas/logs de acceso interiores.

Se habilitan preparacion de la rama preservando el trabajo previo, pruebas
Red, implementacion Green, mutacion, revision y QA en las superficies descritas.
Validacion previa observada: OpenSpec 29/29, trazabilidad, higiene 498 archivos,
10 enlaces locales y guard spec-planner PASS en cinco documentos.

Las menciones PENDING/Proposed en el cuerpo de la propuesta, diseno, tareas y
escenarios describen la presentacion anterior; este registro resuelve ese gate
sin alterar requisitos. La aprobacion original del 10/09 sigue como historia.
No se autoriza ampliar alcance, cambiar roles, publicar PR, merge de la PR,
archivar OpenSpec ni modificar el Trello oficial. Gate humano post-QA pendiente.
