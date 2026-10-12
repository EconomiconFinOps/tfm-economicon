# JUP-035: checkpoint required-documentation-v1 offline

Nota del 12/10/2026: esta evidencia conserva un ensayo historico y sus rutas
locales; esos recibos no son accesibles desde otro checkout. La
[guia reproducible](../validation/JUP-035-chat-reproduction.md) usa entradas
versionadas y el chat vigente. No sustituye ni revalida este resultado.

## Autorizacion y alcance

Paris aprueba el ciclo required nativo / recuperacion tenant-safe backend /
resultado privado HMAC / none final estricto, comunicado en este chat autonomo
12/10/2026 06:40 Canary. Correccion de fixtures separada autorizada 07:05:10.
Un Desarrollador; roles humanos no alterados; sin Git/publicacion/inferencia.
Revision/base: HEAD 954b44298ccd94994f3ac420a3aec55c32eeb521 del worktree
e5-battery-corrections-worktree; cambios ajenos y previos conservados.

## Comportamiento

- Una operacion/intento/dispatch, una busqueda maxima, dos peticiones modelo.
- search_documentation acepta solo query, sin scope ni tenant del modelo.
- Contexto inicial inmutable, sin corpus prefetch. Backend recupera con el tenant
  autenticado, filtros y proveedor existentes. Extension separada, budgeted.
- Resultado correlacionado al tool_call_id, al claim original y al intento vivo;
  rechaza HMAC ausente, tenant ajeno, identificador incorrecto y repeticion.
- Misma tools y esquema completo en ambas peticiones, required despues none.
- Deadline comun; retrieval/embedding/espera bounded y cancelacion comprobada
  antes de continuar. No segundo dispatch ni SDK nuevo.
- FinOpsResponse 1.0 publico intacto; financial_metrics_allowed solo desde billing.
- Suma consumo reportado de ambas llamadas; ausencia de coste no se estima.
- Validadores/citas existentes y persistencia atomica del par intactos.
- Mock explicito mock-direct-v1 conserva flujo determinista sin proveedor real.

## Evidencia offline

Expediente externo exclusivo:
`C:/Users/Trabajo/.codex/visualizations/2026/09/07/01a07c55-c454-7bb3-8053-cbf2ad70d2ec/e5-context-compression-evidence/restart-20261011/jup069-real-battery/corrections/`.
Prefijo de checkpoints/logs: `requiredtool-20261012-`.

- design-spec.log: OpenSpec estricto exit0; design guard solo spec PASS.
- red-processor-authorized.log, red-backend-authorized.log, red-private.log y
  red-operations.log: fallo por comportamiento ausente, conservados.
- red-processor.log: Docker denegado, exit125; NO es Red valido.
- green-processor.log y green-backend.log: FAIL por fixtures incompletas,
  conservados. green-affected-processor.log: 67PASS/1FAIL contrato fixture viejo.
- fixture-correction-before-guard.json: PASS tests-only, cuatro archivos.
- fixture-green-processor.log: 74PASS/1deselected (legacy delayed_first de31s).
- fixture-green-backend.log: 37PASS; warnings existentes registrados.
- mutation-baseline-processor.log: 5PASS focales.
- mutation-baseline-backend.log: 3PASS focales (fuente/vacio/plazo expirado).
- mutation-processor.json y mutation-backend.json: cinco mutantes detectados
  por AssertionError/exit1, no errores de importacion/sintaxis. Copias temporales:
  required->auto, primer consumo omitido, correlacion id omitida, tenant ajeno,
  prefetch reintroducido. mutation-before-guard.json: solo dos tests modificados.
- resource-backend.log y resource-processor.log: payload/conteo identicos para
  financial false/true y continuacion. Variable29 inicial,100 continuacion;
  total con reservas9824. No prueba de compatibilidad universal del proveedor.

Promptversion `jup-035.chat.v3:d9b6946f56baf5ed2172ab4f116e3c57f45f68b1db387d74c16ec48ff5a279bc`.
Assembler SHA256 `d2196e1a83244f6fee7b4c672e03666ee58b408be6201963bf2b792de4969337`.
Esquema publico SHA256 `baf067ac8fe35a693848012c5358cb1c6ab8883ebaa02a63166b00f7d8298018`.
Historial v2 y archivo OpenSpec no reescritos.

## Pendiente y limites

Entrega local para revision independiente, no autoaceptacion. Parent congelara
fuentes antes de construir imagenes y ejecutar UNA operacion real. Comprobar
corpus efectivamente recuperado, sustento de afirmaciones/citas, scope, intento
unico, coste agregado, par unico y reapertura. Un vacio correcto puede abstenerse.
Las pruebas offline usan fuentes/proveedores sinteticos; no acreditan recuperacion
real ni cumplimiento semantico del modelo. No full28 ni JUP-070 formal en esta revision.

Parent comunica TOTAL ronda .29USD, baseline .338851568, upstream .599458076,
gasto .260606508/restante .029393492. Reserva .012 por llamada: preflight conjunto
.024 para dos LLM y margen de embedding solo si coste verificable. No ampliar
topes/reintentos; detener ante incertidumbre contable/cancelacion/fallo.
