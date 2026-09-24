## Estado actual del 23/09/2026

Incremento JWT de 5 s implementado: baseline 245 PASS; Red 252 PASS / 7 FAIL;
Green backend 259 PASS (+14 netos). Mutacion incremental: 7/7 detectadas,
incluido BE1 KILLED, sin equivalentes ni supervivientes; REVIEW_PASS.
Reviewer: navegador 8/8 sobre imagen `03904ecbf021`, sin intervenir relojes.
Auditoria QA incremental PASS (6.4), 23/09 a las 16:33:02.775 UTC; bloqueo ambiental y gate humano
post-QA sin resolver. Resultados propios, sin sumar rondas ni reejecutar suites
ajenas; detalle en [review](review.md) y
[evidencia incremental](../../../docs/evidence/JUP-085-validation.md#incremento-actual-tolerancia-jwt-de-5-s).

### Ronda anterior del 23/09 (historica, margen cero)

La tabla y los checks completados de 1-5 pertenecen a la ronda anterior;
no acreditan el incremento de 5 s.
HEAD `3a08d60`; aprobacion literal en proposal.md a las 13:05:53 UTC y ADR-0007
Accepted. Residual/CORS implementados. Resultados recibidos del orquestador,
no reejecutados por este pase documental:

| Validacion | Resultado comunicado |
|---|---|
| Red residual | 59 fallos CORS y 70 frontend iniciales; 2 regresiones RF-085-001 Red a Green |
| Green | Backend 245 PASS; frontend 235 PASS |
| Casos nuevos | 76 CORS + 139 frontend = 215 residuales; 54 backend historicos retenidos |
| Mutacion residual | 37 variantes, 35 detectadas, 2 equivalentes, 0 pendientes |
| Navegador runtime | Pasadas funcionales PASS, incluida QA posterior; no resuelven QA_BLOCKED_ENV. Detalle e historial en review/evidencia enlazados |
| Compatibilidad Settings | pydantic-settings 2.3.4: 76 CORS PASS; 2.15: 245 backend PASS; sin cambio de dependencias |
| Regresiones de la sesion principal | Processor 266 PASS / 34 skips; Azure 58 PASS; Node 83 PASS; colaboracion 12 PASS |
| Calidad | Lint, typecheck y build PASS |
| Total distinto de pruebas | 899 PASS / 34 SKIP; sin sumar reruns, mutantes, OpenSpec ni navegador |
| Revision | REVIEW_PASS; 135 hashes y guard PASS; RF-085-001 Fixed local, sin integrar |

Cuatro fixtures legacy corregidas sin ampliar alcance: una en
`apps/frontend/src/layouts/SessionGate.test.tsx`, dos en
`apps/frontend/src/routes.integration.test.tsx` y una en
`apps/frontend/src/pages/LoginPage.test.tsx`; ajustes de datos/mocks al contrato.
QA_BLOCKED_ENV, gate del 23/09 a las 15:35:35 UTC: Windows volvio a error 2
(informacion horaria obsoleta) a las 15:34:54 UTC, pese a muestras sin retrocesos
y navegador PASS. RF-085-002 Open: mitigacion temporal insuficiente, no estable.
Fuentes historicas: [review](review.md) y [evidencia](../../../docs/evidence/JUP-085-validation.md#revalidacion-qa-tras-mitigacion-2309),
que conservan la mitigacion y resultados previos como historia. El usuario
excluye cambios de reloj Windows/WSL/Docker/DB y autoriza solo leeway JWT de 5 s.
No resuelve RF-085-002 ni exceptua QA; JUP-097 intacto. CORS Open y gate humano
post-QA pendiente.

## 1. Preparacion documental

- [x] 1.1 JUP-085 inventariar el login, `/me`, JWT y almacenamiento frontend heredados.
- [x] 1.2 JUP-085 definir request, response, claims, TTL, errores y limites de la auth demo.
- [x] 1.3 JUP-085 contrastar descripcion oficial completa del export 10/09, plan v1.3, base con JUP-053 y reutilizacion/colisiones de PR #29 mediante lectura; distinguir implementacion observada de pruebas pendientes.
- [x] 1.4 JUP-085 validar OpenSpec estricto y trazabilidad en el worktree el 10/09; registrar comandos reales, exitcodes y limitaciones historicos.
- [x] 1.5 JUP-085 reconciliar estos cuatro documentos por lectura de upstream `3a08d60` el 23/09, conservando JUP-097, la aprobacion historica y todos los cambios locales previos.
- [x] 1.6 JUP-085 recibir del orquestador resultados del 23/09: guard limitado a los cuatro documentos PASS, OpenSpec 29/29 y trazabilidad PASS (exit 0). Ver reconciliacion documental en review.md; no es validacion funcional ni aprobacion de codigo.

Validacion documental observada el 2026-09-10, tras redactar los cuatro
artefactos: `corepack pnpm openspec:validate`, exit 0, 29 passed / 0 failed;
`corepack pnpm jup:check -- --change jup-085-auth-session-contract`, exit 0,
`[OK]` enlazado con Trello y completo estructuralmente. Se uso CLI OpenSpec
1.8.0 existente via PATH y pnpm cacheado, con permiso de lectura del entorno,
sin instalaciones. `git diff --check` no presento errores. No son resultados
de pruebas de producto ni aprobacion. La comprobacion independiente posterior
de limites de escritura paso sin infracciones; la aprobacion esta en proposal.md.

## 2. Gate y prerequisitos

- [x] 2.1 JUP-085 obtener decision humana explicita sobre alcance/scenarios, adelanto acotado de `/me`, re-login por `iat` obligatorio y limites de logout; aprobacion registrada en proposal.md el 10/09 a las 18:30:51 UTC.
- [x] 2.2 JUP-085 consumir JUP-087/PR #29, JUP-095/PR #36 y JUP-097/PR #42 por fast-forward a HEAD `3a08d60`, preservando byte a byte los 15 archivos sucios previos. Validaciones frescas comunicadas por el orquestador; sin duplicar runner.
- [x] 2.3 JUP-085 gate humano del residual revisado resuelto por el registro literal de Paris en proposal.md, 23/09/2026 13:05:53 UTC; validacion runtime, persistencia/perfil discrepante, limpieza/generacion y `401` global fuera de `/me`, con los paths descritos.
- [x] 2.4 JUP-085 recoger direccion CHOSEN por Paris el 23/09, respuesta "1": CORS backend dentro de esta propuesta, proxy de mismo origen no seleccionado. Es eleccion de direccion, no aprobacion de parametros ni implementacion.
- [x] 2.5 JUP-085 politica concreta, superficies y ADR-0007 aprobados tras validacion segun registro literal en proposal.md, 23/09/2026 13:05:53 UTC; ADR Accepted. Incluye JSON/origenes exactos, default vacio, HTTPS production/HTTP dev-test, metodos/cabeceras, sin cookies, cableado FastAPI y limite de 500/preflight sin metricas interiores.

## 3. Red, solo tras aprobacion

3.1 y 4.1 conservan el trabajo backend del 10/09. El residual se ejecuto tras
el gate del 23/09 y la sincronizacion; sus resultados historicos figuran arriba.
Este turno solo actualiza la documentacion del incremento y la valida.

- [x] 3.1 JUP-085 ampliar schema/JWT y rutas HTTP con exito, `422` sanitizado, credenciales `401`, bearer ausente/malformado/duplicado, firma/algoritmo/claims/tiempos invalidos, exp exacta y usuario eliminado; aislar DB/config y comprobar perfil directo.
- [x] 3.2 JUP-085 cubrir validacion de storage/login/perfil y limpieza; preservar `/me` y `/tenants` paralelos incluso tras login, identidad de servidor, logout ante cualquier error de query `/me` (incluidos transitorios) y descarte de tenants concurrentes tras fallo. Diferenciar error de query e intento previo a retry sin cambiar politica JUP-097.
- [x] 3.3 JUP-085 cubrir `401` global en consultas/mutaciones fuera de `/me`, conservacion ante `403`/`422`/red/`5xx` solo fuera de `/me`, login/health publicos y respuestas diferidas de sesion vieja (incluido `/me`) tras logout/nuevo login con usuario/token iguales; cubrir perfil discrepante y ambos ordenes de resolucion perfil/tenants.
- [x] 3.4 JUP-085 registrar fallo Red por gap y escenario; conservar como regresiones los casos ya satisfechos, sin falsificar fallos o contar placeholders.
- [x] 3.5 JUP-085 tras gate/sincronizacion, cubrir en nuevo `apps/backend/tests/test_cors.py` y, si hace falta, `test_secret_config.py`: lista valida/ausente/[]/malformada/wildcard/null, HTTP segun entorno, fallo StartupError sin input; preflight sin JWT permitido/denegado por origen/metodo/cabeceras, auth intacta, peticiones y 200/401/403/422/500 sanitizado con/sin Allow-Origin segun design.md, mas limite del 500 exterior. Reutilizar regresiones nativas de app/state/overrides/import/lifespan/metricas/tracing, sin refactor global.

## 4. Green, solo tras Red validado

- [x] 4.1 JUP-085 validar password no vacia, emitir/exigir claims y TTL positivo, mapear entradas invalidas a `401` sin ocultar fallos de DB; conservar HTTP y JUP-053.
- [x] 4.2 JUP-085 implementar el residual aprobado, con status HTTP, contratos/generacion y limpieza idempotente; conservar bootstrap paralelo y politica estricta `/me`. No migrar implicitamente su queryKey con token ni atribuir estas garantias a JUP-097.
- [x] 4.3 JUP-085 ejecutar matriz Green y regresiones de secretos/seed/frontend; no cambiar politica de credenciales, CI, tenant auth o pipeline.
- [x] 4.4 JUP-085 solo tras 2.5 y Red, incorporar CORS existente y Settings en `apps/backend/app/main.py`/`core/config.py`, paso por `docker-compose.yml`, ejemplos en `.env.example` y documentacion en backend README/runbook raiz segun paths de design.md. No editar/copiar `.env`, retirar secretos ni anadir dependencias, runner, CI, migraciones o seed.

## 5. Ronda previa completada; QA_BLOCKED_ENV

- [x] 5.1 JUP-085 completar mutacion residual de contratos/limpieza/status/generacion, paralelismo y logout por errores transitorios de `/me`, distinguiendo el `403` de otros endpoints: 37 variantes, 35 detectadas, 2 equivalentes, 0 pendientes. Ronda backend del 10/09 conservada como historia; revision de codigo REVIEW_PASS.
- [x] 5.2 JUP-085 verificar backend/frontend, lint, build, typecheck, OpenSpec estricto, trazabilidad e higiene sobre `3a08d60`: pruebas/calidad comunicadas PASS arriba; OpenSpec estricto 33/33, trazabilidad e higiene (615 archivos) PASS en la sincronizacion anterior del 23/09, sin reejecutar producto. Los wrappers `corepack pnpm` fallaron por EPERM antes del check; se ejecutaron los mismos entrypoints instalados con `node`, exit 0, con permiso de lectura fuera del sandbox para OpenSpec.
- [x] 5.3 JUP-085 entregar evidencia funcional y revision tecnica de login, restauracion, expiracion y logout, con navegador real en stack canonico de puertos separados, tras gate 2.5, seguridad normal y sin proxy. Preservar `/me`/`tenants` paralelos y logout ante cualquier error de query `/me`, incluso transitorio, con retries intactos; reutilizar tests frontend nativos. Evidencia y review runtime entregados por el orquestador, incluido el REVIEW_PASS ambiental previo y el dictamen QA_BLOCKED_ENV posterior. Esta entrega completa 5.3, no acredita QA final PASS ni estabilidad del reloj. RF-087-001/RF-095-001 siguen Open hasta completar QA; no inferir cierre de RF-087-002 historico, JUP-020 ni ampliar JUP-086.
- [ ] 5.4 JUP-085 obtener validacion y gate humano final con participacion acreditada, sin inferir pairing/revision/QA de los roles propuestos. Publicacion, operaciones Git, tracker y archivo requieren autorizacion separada.

Antecedente historico backend del 10/09: 54 casos nuevos; Red 22 failed / 124 passed en la
seleccion con regresiones; Green completo 169 passed. Mutacion: 13 variantes, 12 detectados,
1 equivalente, sin supervivientes no equivalentes. Revision tecnica backend
PASS y QA backend PASS. Ver review.md y evidencia enlazada para resultados y limites.
Los items 3.4, 4.3 y 5.1 se completaron en la ronda residual del 23/09,
no por reutilizar estos resultados historicos. Review/evidencia actuales ya
consolidados por el orquestador; QA final bloqueada y gate humano pendiente.

## 6. Incremento autorizado: leeway JWT de 5 s

6.1-6.4 completados con evidencia incremental propia; QA_PASS acotado a leeway=5,
sin levantar QA_BLOCKED_ENV global ni cerrar RF-085-002. No se cambian
aprobaciones ni resultados historicos; 5.4 permanece pendiente.

- [x] 6.1 JUP-085 Red focalizado en `apps/backend/tests/test_security_utils.py` y `apps/backend/tests/test_auth_api.py`, con reloj fijo: iat hasta now+5 pasa, mayor falla; exp mayor que now-5 pasa, igualdad o inferior falla; nbf opcional respeta el mismo margen nativo. Mantener negativos/tipos/claims requeridos/firma/usuario/TTL; rechazar exp<=iat, incluido iat=now+4, exp=now-4, antes del lookup. Actualizar expectativas anteriores de margen cero; registrar Red solo por diferencias semanticas reales y preservar controles ya satisfechos.
- [x] 6.2 JUP-085 Green minimo en `apps/backend/app/core/security.py`: `jwt.decode(leeway=5)` nativo, constante local opcional; conservar HS256/require, tipos estrictos, negativos y exp>iat. Ejecutar focalizadas y regresion backend con entorno existente; sin otras superficies de producto, config, dependencias o relojes.
- [x] 6.3 JUP-085 mutacion dirigida incremental: omitir/cambiar el 5, alterar fronteras iat/exp/nbf y retirar exp>iat deben detectarse. Reevaluar BE1: su equivalencia historica por iat<=now<exp ya no aplica; el caso cruzado debe detectar su retirada. No trasladar el recuento ni equivalencias anteriores al nuevo ciclo.
- [x] 6.4 JUP-085 review y QA incrementales del diff, fronteras y regresiones, con resultados propios; conservar JUP-097. Verificar el flujo afectado en QA sin operar relojes; RF-085-002 sigue Open/out of scope y puede mantener el bloqueo ambiental. No declarar QA final PASS ni autorizar PR/merge/archivo/tracker; 5.4 sigue pendiente.
