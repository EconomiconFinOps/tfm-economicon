# JUP-122 / PR130: dos correcciones de revision

Fecha: 14/10/2026, Atlantic/Canary. Rama `feat/JUP-122-chat-engineering`,
HEAD conservado `28ee5b1c44389aa8643c1c4deca6c0c834c09f7d`, base aportada
por PM `c30a7d0f28c04cae757b424222b34b232814303e`. Cambios locales, sin commit,
push ni publicacion. No sustituye Revision/Validacion JUP-122 oficiales.

## Alcance y contrato aprobado

Solo los dos cambios bloqueantes de la review de Victor `5523121308`:

1. `prepare` asigna `CHAT_PRIVATE_SUBNET` y `PROCESSOR_CHAT_PRIVATE_IP`
   por slot: A `172.30.35.0/24`, `.35.3`; B `172.30.36.0/24`, `.36.3`.
   Conserva HMAC, red interna, puerto privado sin publicar, loopback y
   releases inmutables. No modifica el agente instalado en DockerServer.
2. Paris aprobo antes de producto/tests `GET /assistant/capabilities`,
   autenticado y autorizado por tenant, con respuesta cerrada
   `{"chat_enabled": boolean}` y `Cache-Control: no-store`. Se obtiene del
   estado efectivo del backend, sin cargar el runtime ni escribir datos.
   Solo una respuesta valida true monta el acceso/panel. La consulta se
   aisla por generacion de sesion, usuario y tenant; no se reutilizan
   resultados de otra identidad. El envio comprueba de nuevo el estado
   antes de crear conversacion o generar. False, fallo o respuesta invalida
   no producen POST ni un estado de envio incierto.

Una lectura de disponibilidad no garantiza atomicidad frente a un reinicio
concurrente; las guardas 503 y la autorizacion existentes permanecen intactas.
No se modifica `/health`, el modelo, las dependencias, los prompts o la calidad
semantica de B. Las diez observaciones no bloqueantes quedan fuera del alcance.

## Archivos

- CD: `tools/cd/deploy.py`, `tools/cd/test_deploy.py` y
  `docs/deployment/dockerserver-cd.md`.
- Backend: `app/api/routes/chat.py`, `app/schemas/chat.py` y
  `tests/test_chat_disabled_jup122.py`, dentro de `apps/backend`.
- Frontend: `services/chat.ts`, `hooks/useChatCapabilities.ts`,
  `components/chat/ChatAvailability.tsx`, `components/chat/useChatSession.ts`
  y `layouts/Layout.tsx`, dentro de `apps/frontend/src`.
- Pruebas: `chat-capabilities-jup122.test.tsx` cubre el contrato real HTTP.
  Las ocho suites existentes de panel, titulos, resumen, recuperacion,
  solicitudes guardadas, borrado, captura y anomalias declaran su fixture
  de runtime habilitado mediante `chat-enabled-runtime.ts`. Conservan todas
  sus aserciones; la prueba de preparacion espera ahora el inicio de su POST
  controlado despues de la consulta asincrona nueva.
- OpenSpec design/spec/tasks y un unico tema/fila de continuidad.

## Resultados focales

| Comprobacion | Resultado y limite |
| --- | --- |
| Red de redes CD | Nueva regresion detecta variables ausentes sobre producto anterior |
| Green test_deploy | 19/19 PASS |
| Suite CD afectada | 56 PASS, 2 omitidas POSIX heredadas en Windows; 58 casos |
| init/prepare y Compose reales | Ambos slots correctos; HMAC intacto, puertos loopback, internal, chat false, retry inmutable |
| Coexistencia real de redes | .35/24 y .36/24 simultaneas, internal; retiradas al terminar |
| Red backend | 6 fallos nuevos por ruta ausente, 4 pruebas previas PASS |
| Green backend | 32/32 PASS; endpoint y operaciones existentes con SQLite/processor controlado |
| Red frontend | 10 fallos nuevos por acceso incondicional/ausencia de preflight |
| Green frontend afectado | 120/120 PASS, 16 archivos, cero omisiones |
| Sensibilidad CD | Ignorar slot provoca fallo de nueva regresion; mutante detectado |
| Sensibilidad disponibilidad | Forzar true en backend provoca fallo del estado false; mutante detectado |
| Navegador | Off/on/off PASS; frontend construido y rutas reales, SQLite/processor controlado; no full stack Docker |
| Typecheck | tsconfig.json, tsconfig.test.json y tsconfig.node.json PASS |
| Lint | 0 errores, 1 aviso previo en ChatPresentation.tsx:101 |
| Build | PASS; avisos de tamano de chunk/import dinamico conservados |
| CD workflow/topologia | 40/40 PASS |
| OpenSpec estricto, trazabilidad e higiene | PASS; recibos finales fuera de Git |

Navegador con login real sintetico: en off no aparece el acceso y no hay POST
del asistente ni conversaciones vacias. En on aparece y una pregunta produce
un POST de conversacion, un POST de generacion, una llamada al processor
controlado y exactamente una pareja usuario/asistente persistida. En off
de nuevo desaparece y no crecen los datos. Capturas inspeccionadas en desktop
1440x960 y mobile 390x844 (modo off); cero errores JavaScript del recorrido.
Esto no acredita embeddings/RAG/modelos reales, que no pertenecen a este fix.

## Reproduccion minima

```sh
python -m unittest discover -s tools/cd -p 'test_*.py' -v
corepack pnpm docker:validate
node --test tools/cd-workflow.test.mjs
cd apps/backend
python -m pytest tests/test_chat_disabled_jup122.py tests/test_chat_operations_jup035.py -q
cd ../frontend
corepack pnpm test -- tests/chat-capabilities-jup122.test.tsx tests/chat-panel-jup035.test.tsx tests/chat-titles-jup035.test.tsx tests/chat-summary-jup035.test.tsx tests/chat-recovery-jup035.test.tsx tests/chat-saved-requests-jup035.test.tsx tests/chat-deletion-jup035.test.tsx tests/chat-screen-jup035.test.tsx tests/chat-anomalies-screen-jup035.test.tsx src/layouts --maxWorkers=2
corepack pnpm typecheck
corepack pnpm lint
corepack pnpm build
cd ../..
corepack pnpm openspec:validate
corepack pnpm jup:check -- --change jup-122-chat-engineering
corepack pnpm jup:cleanup:check
```

Para el render real, ejecutar `deploy.init` y `prepare` sobre un root
desechable para dos SHA de prueba, slots 0/1; leer en memoria el Compose
generado y comprobar subnet/IP/internal/loopback/HMAC, sin imprimir secretos.
Crear ambas redes internas con esos pools libres, etiquetas propias e IDs
registrados; inspeccionar ambas a la vez y retirar solo las redes propias
vacias. No retirar redes ajenas ni desplegar en DockerServer.

## Fallos conservados y pendientes

Los recibos originales no se sobrescriben. La preparacion local requirio
permisos para Vite, entorno Python y Docker. El helper de render tuvo una
invocacion relativa incorrecta y una asercion confundiendo puerto publico
8001 con privado 8003; el de inventario encontro Config null en redes sin
IPAM. Se corrigieron solo esos helpers. La primera adaptacion de fixtures
frontend cargo sus mocks despues de Layout; despues una prueba intentaba
liberar el POST antes de la consulta asincrona. No se rebajaron aserciones.
El primer navegador fallo por binario Playwright ausente; se reutilizo
Chrome instalado con perfil temporal. Una carpeta temporal propia vacia
retenida por el cwd de Windows se retiro tras verificar su ruta y contenido.

La coexistencia estuvo bloqueada por una red ajena 172.30.0.0/16. PM la
retiro con autorizacion expresa de Paris y verifico que estaba vacia;
este ejecutor no altero recursos ajenos. Redes propias y dos servicios HTTP
de prueba retirados, puertos 48790/48791 libres. Sin gateway, claves, IA
real ni gasto. No se repiten SQL nativo, suites generales o bateria 28.

La evidencia primaria local conserva comandos, SHA256 de stdout/stderr,
capturas, scripts de preparacion y diff en el directorio
`jup122-review-fixes-20261014`, fuera del repositorio. Las evidencias previas
de A conservan sus resultados y limites; no se presentan como nuevas.
Pendiente del PM: controles independientes y autorizaciones de commit/push,
CI del nuevo commit, entrega a Victor/Lucia y reviews humanas. No se
solicita levantar Request changes sobre un diff aun no publicado.
