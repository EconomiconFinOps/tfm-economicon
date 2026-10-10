# JUP-108: comprobacion local de Compose

- Fecha: 2026-10-08.
- Rama: `feat/JUP-108-litellm-compose`; base `2f9a5f530c9fe3b60007ba5060c189133e353bf6`.
- Estado: cambios locales sin commit de entrega. Esta evidencia no equivale a
  revision tecnica ni validacion funcional independientes.
- Alcance: perfil `ai` opcional en el Compose principal, gateway y PostgreSQL
  dedicados, claves virtuales separadas y arranque mock conservado.
- Docker Compose: `v2.34.0-desktop.1`. Los ensayos iniciales descritos a
  continuacion no usaron OpenRouter ni llamadas pagadas. La campaña real
  posterior y su consumo se registran en la consolidacion final de este
  documento. Los proyectos de JUP-047 no se modificaron.

## Resultados

| Comprobacion | Resultado |
| --- | --- |
| `node --test tools/docker-topology.test.mjs tools/llm-gateway-config.test.mjs tools/litellm-compose.test.mjs` sin opt-ins | 42 passed, 3 skipped; los omitidos son los tres Docker optativos, ejecutados por separado. |
| OpenSpec `validate --all --strict --no-interactive` | 53 passed, 0 failed. |
| `node tools/jup-check.mjs --change jup-108-litellm-compose` | OK. |
| `node tools/jup-cleanup-check.mjs` | OK, 908 archivos tras la correccion. |
| `git diff --check` y sintaxis AST del fixture Python modificado | OK. |
| Build Docker habitual de backend, processor, Azure Cost API simulada y frontend desde esta rama | 4/4 imagenes construidas. La capa `pip install` se reutilizo de cache; el frontend emitio el aviso existente de bundle >500 kB. |
| Suite Python del processor en contenedor temporal con `requirements-dev.txt` y `email-validator` para el productor backend | 448 passed, 57 skipped, 330 avisos de deprecacion; Python 3.12. |
| Mutacion temporal `backend.depends_on.litellm.required: false` en `compose.ai.yml` | La prueba de dependencia obligatoria fallo; restaurado a `true`, volvio a verde. Sustituye la mutacion anterior que fijaba el comportamiento opcional incorrecto. |
| Mutacion temporal sin guardia `OPENROUTER_API_KEY` del gateway | La prueba de rechazo de secretos ausentes fallo; guardia restaurada, volvio a verde. |

La prueba optativa `JUP108_DOCKER_FAKE=1` de
`tools/litellm-compose.test.mjs` paso en un proyecto desechable con ambas redes
internas y un proveedor simulado. Confirmo: secreto upstream ausente rechazado,
salud del gateway, embedding con clave del backend, chat denegado a esa clave,
chat con clave del processor, clave invalida denegada, acceso desde las redes de
ambos consumidores y persistencia de clave y registros de gasto tras recrear
gateway y PostgreSQL. Las 11 comprobaciones fueron verdaderas y el proyecto,
sus redes y volumenes se retiraron. El recibo saneado quedo en el directorio
temporal `jup108-compose-YQs0no` de esta maquina.

La prueba optativa `JUP108_DOCKER_MOCK=1`, indicando explicitamente las cuatro
imagenes de aplicaciones mediante `JUP108_MOCK_*_IMAGE`, paso en otro proyecto
desechable: nueve servicios arrancados, ningun contenedor LiteLLM, backend
saludable y limpieza completa. Puertos propios en loopback y credenciales
sinteticas. El primer intento uso imagenes locales de otras ramas; el segundo
uso las cuatro imagenes construidas desde este checkout y volvio a pasar las
cuatro comprobaciones. Recibo final saneado: `jup108-mock-4eEehW` en el
directorio temporal de esta maquina. Las imagenes finales fueron
`jup108-local-backend:smoke` (`4d1d9c7e`),
`jup108-local-processor:smoke` (`0a4e1fbd`),
`jup108-local-azure:smoke` (`ef3b5c7f`) y
`jup108-local-frontend:smoke` (`3e451a3c`).

La primera pasada de pytest en la imagen de produccion, con solo pytest
instalado, dio 442 passed, 57 skipped y seis fallos de subprocess al importar
el productor backend sin sus dependencias de test. Al instalar
`requirements-dev.txt` del processor y `email-validator` en un contenedor
temporal, la suite completa paso. No se modificaron requisitos de produccion
ni el Python del host por esta diagnostica.

## Correcciones tras revision local

Paris autorizo aplicar los dos hallazgos: `required: false` dejaba arrancar
consumidores con el gateway no saludable, y la guia no prevenia reutilizar una
tabla vectorial mock de ocho dimensiones al seleccionar 1536.

- Red: la prueba corregida de topologia fallo contra la dependencia opcional
  anterior (34 passed, 1 failed). Green: se retiro esa dependencia del Compose
  base y se anadio `infra/litellm/compose.ai.yml` con salud obligatoria para los
  dos consumidores. Las instrucciones reales aplican ambos archivos y `ai`.
- `JUP108_DOCKER_HEALTH=1 node --test tools/litellm-compose.test.mjs`: 1 passed,
  2 skipped. Docker ejecuto dos consumidores sinteticos con las dependencias
  del override: ninguno arranco con gateway no saludable, ambos arrancaron
  con gateway saludable. Red interna sin modelos ni credenciales. Limpieza
  completa; recibo `jup108-health-MLq0o0` en el directorio temporal.
- Repeticion del gateway con el override real: 11/11 comprobaciones verdaderas,
  claves separadas, rechazo de secreto ausente y persistencia conservada.
  Limpieza completa; recibo `jup108-compose-KoFTN7` en el directorio temporal.
- Repeticion del mock con las cuatro imagenes de este checkout: 4/4
  comprobaciones verdaderas, nueve servicios sin gateway y backend saludable.
  Limpieza completa; recibo `jup108-mock-8gEN5f` en el directorio temporal.
  La invocacion conjunta con `JUP108_DOCKER_FAKE=1` y `JUP108_DOCKER_MOCK=1`
  dio 2 passed y 1 skipped (salud, ejecutada por separado).
- La guia prescribe un proyecto `economicon-ai` con volumenes nuevos y
  `.env.ai` ignorado, conservando el proyecto mock sin `down -v`. Exige
  inicializar/reingerir en el nuevo entorno; no promete migracion ni modifica
  los datos existentes. Se comprobo que Git ignora `.env.ai`.
- No se cambiaron aplicaciones, modelos ni dependencias Python durante estas
  correcciones; la suite Python indicada arriba corresponde a la pasada
  anterior y no se ha repetido por este cambio de Compose/documentacion.

## Limites pendientes

- No se realizo un build `--no-cache`; las cuatro imagenes del codigo actual
  se construyeron con el mecanismo de cache habitual. El intento anterior con
  `--network none` habia impedido reutilizar la capa de `pip install` y no
  representaba el procedimiento normal.
- El test Python optativo de LiteLLM requiere Docker desde pytest y no se
  habilito dentro del contenedor de regresion. Su caso quedo omitido como tal;
  la prueba Node optativa comprobo el gateway real con upstream simulado, pero
  no sustituye todas las aserciones de ese test Python.
- Faltan revision tecnica y validacion funcional independientes sobre la
  entrega final, aprobacion final, archivado autorizado y cualquier paso de
  publicacion. No se ha creado PR ni se ha escrito en GitHub o Trello.


## Consolidacion tecnica previa a revision independiente — 08/10/2026

HEAD y base local comprobados: `2f9a5f530c9fe3b60007ba5060c189133e353bf6`, rama `feat/JUP-108-litellm-compose`, cambios sin commit. El worktree comparte el Git comun de `C:/Repositorios/tfm-economicon-1`; adaptador local heredado por esa identidad, no por nombre. Proceso `CONTRIBUTING.md` 2026-09-30/JUP-100. PM encargo esta consolidacion a las 22:42:41 Atlantic/Canary y confirmo la tarjeta y criterios oficiales a las 22:44:00. Roles confirmados: Paris liderazgo, Victor pairing, Alejandro revision, Lucia validacion. No se atribuye participacion humana por asignacion.

La implementacion, revision y validacion previas proceden del mismo chat autor bajo la excepcion comunicada por PM. Son evidencia del autor y **no independientes**. Los resultados favorables anteriores no cierran las tareas 3.2/3.3 ni autorizan archivo, Git o publicacion. La aprobacion final humana permanece pendiente.

### Evidencia final recibida del autor

| Campaña o comprobacion | Resultado y limite |
| --- | --- |
| Tests Node afectados, con salud habilitada | 43 PASS/2 SKIP segun entrega del autor; no sumar a la campaña inicial 42/3. |
| Gateway sintetico y mock habilitados | 2 PASS/1 SKIP segun autor; salud ejecutada por separado. No equivalencia total al opt-in Python. |
| Bloqueo por salud, `jup108-health-wBqixC` | Ambos consumidores sinteticos bloqueados con gateway no saludable y habilitados con salud; limpieza true. |
| Gateway con upstream simulado, `jup108-compose-Qq2WZ6` | 11/11 comprobaciones true: claves/scopes, redes, rechazo, persistencia de claves y gasto tras recreacion; limpieza true. |
| Mock, `jup108-mock-VvY9jO` | 4/4 comprobaciones true, nueve servicios sin gateway, backend saludable, imagenes locales de esta entrega; limpieza true. |
| Gateway/OpenRouter real final, `jup108-live-xsaz0kow` | PASS_REAL_GATEWAY_CHAT_AND_EMBEDDING; chat HTTP200/0,797 s y embedding HTTP200/1,032 s con 1536 valores finitos no nulos; claves independientes, rechazo de scope/clave invalida, claves persistentes y logs saneados; limpieza true. |
| Primer ensayo real, `jup108-live-kev6oml2` | INCOMPLETE conservado: chat y embedding respondieron, pero el comprobador selecciono registros de peticiones rechazadas de coste cero. Addendum contable preservado, sin nuevas inferencias; ensayo final corrigio solo el comprobador temporal. |
| Regresion processor | 448 PASS/57 SKIP, anterior a correcciones Compose/documentacion; no nueva ejecucion ni exito de casos omitidos. |
| Controles de entrega | OpenSpec53/53, trazabilidad, higiene y diff-check correctos segun autor; no representan CI remota ni bateria global nueva ejecutada por TL. |

En ambos ensayos reales hubo cuatro inferencias, 84 tokens y coste atribuido total de `0.000064405 USD`. Cada ensayo: chat 25 tokens de entrada/10 de salida y embedding 7 tokens. El coste se apoya en respuesta de chat, tarifa registrada de embeddings y SpendLogs locales; el contador upstream compartido no se concilio. No se afirma factura conciliada ni coste cero del primer ensayo. El ensayo final observo gasto real almacenado **antes** de recrear; la persistencia del gasto **despues** de recrear solo se acredito con upstream simulado. Las claves reales si conservaron validez tras recreacion.

La autorizacion de gasto de aquellos ensayos no se extiende a esta preparacion ni a nuevos ejecutores. No se hicieron llamadas nuevas durante la consolidacion. La evidencia real cubre exclusivamente endpoints del gateway, no chat web, FinOpsResponse completo, RAG, datos de costes, disponibilidad continua ni DockerServer.

### Criterios oficiales y evidencia disponible para la verificacion independiente

Fuente oficial transmitida por PM: [JUP-108](https://trello.com/c/0MANNZZ4), lectura de 08/10/2026 22:44:00 Atlantic/Canary. La tabla identifica comprobaciones candidatas; **no constituye dictamen de aceptacion independiente**.

| Criterio oficial | Evidencia disponible / pendiente |
| --- | --- |
| 1. Un comando documentado del Compose principal activa el perfil de IA y levanta LiteLLM, su PostgreSQL y consumidores necesarios, sin conexiones manuales entre proyectos. | Guia y override `infra/litellm/compose.ai.yml`, topologia efectiva 9/11 y recibos sinteticos; ejecutar instrucciones en validacion independiente, sin proveedor pagado. |
| 2. El arranque simulado sigue funcionando sin credenciales OpenRouter ni obligacion de levantar gateway. | Recibo mock final 4/4; comprobar configuracion/arranque documentados sin secretos AI. |
| 3. Backend y processor alcanzan LiteLLM con claves virtuales independientes; peticion autorizada y rechazo clave invalida. | Recibo sintetico 11/11 y real final; comprobar separacion y autorizacion sin gastar. |
| 4. Gateway conecta PostgreSQL y conserva claves tras recrear contenedores manteniendo volumen. | Claves persistentes en recibos sintetico/real; gasto persistente posterior solo sintetico. |
| 5. Aliases, imagenes fijadas y controles seguridad existentes conservados, sin secretos versionados ni exposicion publica PostgreSQL/administracion gateway. | Revision de Compose/configuracion y controles afectados; contrastar pin/aliases y superficies de red. |
| 6. Instrucciones reproducibles de arranque/configuracion; pruebas afectadas añadidas/ajustadas y evidencias enlazadas; llamadas reales con autorizacion/presupuesto. | README/runbook, campañas del autor e indice de recibos; validacion independiente pendiente. No nuevas llamadas pagadas autorizadas. |
| 7. OpenSpec y documentacion actualizados; cambio archivado segun flujo; PR vinculada con revision y validacion independientes antes integrar. | OpenSpec activo y evidencia consolidada; revision/validacion independientes, aprobacion final, archivo autorizado, PR y reviews humanas siguen pendientes. |

Reutilizar JUP-023/JUP-050 integradas y respetar JUP-078, sin configuraciones divergentes. Se conserva guia de proyecto/volumen nuevo para pasar de mock8 a embedding1536; no migrar ni borrar volumenes existentes. Fuera de alcance: modelos, presupuestos, contratos IA, negocio, administracion de claves y despliegue DockerServer.

### Procedencia y limites de integridad

Se conservaron copias exactas de los siete informes/recibos saneados en el paquete externo TL `jup108-pre-review-20261008/receipts`, con origen y SHA256 en `receipt-index.json`. Los recibos no contienen credenciales. Sus hashes son:

- `jup108-live-xsaz0kow/validation-summary.md`: `097590e83ea85d06c8d1cc21cc88fc2fa617d2508d5a7ecf60a08a63248777da`.
- `jup108-live-xsaz0kow/receipt.json`: `3228aa1c4d2bdf5843cbe05971e09b0be3d1c6bbb0811a6736b5839d409c54fa`.
- `jup108-live-kev6oml2/receipt.json`: `c50e470a925a40176630cc94ee82aa3cdb9f23a36ba075f5a901480f5f3182fe`.
- `jup108-live-kev6oml2/accounting-addendum.json`: `84fe7db3bcf4c9db703bed14727a9f7283a6eb9307ec6fa16bc6a699b25a9726`.
- `jup108-health-wBqixC/receipt.json`: `776e71c4b3f463b6ad39cbf02cbd675d2ba8ae2a6212d59005859dc0dfd43da7`.
- `jup108-compose-Qq2WZ6/receipt.json`: `ae21ba48b33a4667a795c02583327d576f10c775abe03c16f4008fcf3f4d40ba`.
- `jup108-mock-VvY9jO/receipt.json`: `5c9db324018facdc1f7159ed2556d3bae4af18ffa89a7db14dae7bde42f45070`.

Los baselines del autor `jup108-review-corrected-20261008.json` (SHA256 `c38204d1cd5cf22cad764d1c395661d55af4274c5328d2eb382e35b005d2778b`) y `jup108-validation-20261008-original.json` (`a33ec6c8251f2e6e43c518c6c85d02787228d4bee5ec4442110c002b48bdaf70`) se conservan sin reemplazar y no son originales independientes del PM. PM debe crear/conservar su referencia y hash antes de cada despacho independiente y contrastarla al retorno/prepublicacion. Los controles son conductuales; no se afirma sandbox de lectura.

Se mantienen todos los limites iniciales: build habitual con cache, Python optativo Docker omitido por CLI/socket y no sustituido completamente por Node, casos SKIP no validados, sin CI remota nueva. La revision debe comprobar cobertura de mutaciones frente al diseño y vigencia de campañas; esta consolidacion no inventa operadores ni dispensa pruebas requeridas. Preparacion documental concluida; pendiente despacho Revisor con original PM, seguido secuencialmente de Validador. Solo despues se presenta resultado para aprobacion final y pasos autorizados de archivo/publicacion.


## Reconciliacion autorizada con JUP-047 — 08/10/2026

**Estado actual:** HEAD/base `ff2ea6be12abf1bea4789791c34efb46c3b55aa8`, rama `feat/JUP-108-litellm-compose`; delta JUP-108 sin commit de entrega. Esta seccion supersede solo el estado operativo anterior, no sus resultados/hashes/limitaciones. Revision focal y validacion independiente sobre esta combinacion todavia pendientes; aprobacion final humana nueva, DoD, archivo/PR/reviews humanas siguen gates separados.

Paris autorizo literalmente «updatea develop y reconcilia la rama de la108 para que añada los cambios de la047», comunicado por PM a las 23:11:43 Atlantic/Canary. PM confirmo develop y origin/develop sincronizados en ff2ea6be y limpio a las 23:14:04/23:14:32; el Validador habia cedido la plaza a las 23:13:52, con retorno propio PASS y luego retorno independiente PM PASS a las 22:14:32 UTC contra el mismo original `52fc2ff1f07cb4a844087ce0e21ad685f0cd876e3439e60a5f22c2ba40d256be`. Se conserva ese original; no se reemplaza ni declara coincidente con la base nueva.

Desarrollador entrego INTEGRATION_GREEN a las 23:29:50. Operacion real: stash-u de respaldo `b5564201db31c5fbecaab5a42cb6e4fce51b75ba` retenido; merge --ff-only del SHA autorizado y stash apply --index, ambos exit0, cero conflictos y sin commit de entrega/merge adicional. Respaldo externo integro de 908 fuentes. Incoming37 rutas, unico solapamiento README combinado automaticamente; 14 rutas locales JUP-108 restantes byte-exact y 36 incoming no solapadas cotejadas con el checkout filtrado. Indice staged vacio como antes. El primer comparador detecto normalizacion CRLF→LF por stash en evidencia/tareas untracked: igualdad textual probada y reaplicacion byte-exact desde respaldo, conservando fallo/after-apply/hashes. No reset, rebase, cherry-pick, descarte, drop/pop, push o publicacion.

| Control nuevo tras reconciliar | Resultado propio Desarrollador |
| --- | --- |
| Compose/gateway, tres suites estaticas | 42 PASS/3 SKIP, 0 FAIL; los tres Docker optativos no se ejecutaron aqui. |
| Contratos focales de salud backend | 26 PASS, sin FAIL/ERROR/SKIP. |
| Salud/API/pill frontend | 99 PASS, sin FAIL/ERROR/SKIP. |
| OpenSpec/trazabilidad/higiene/diff | 54/54 estricto, traza108, higiene932 y diff-check correctos. |
| Build backend/frontend afectados | 2/2 correctos, build habitual con capas de dependencias existentes en cache; Vite construyo dist nuevo, aviso existente de chunk grande. |

No se suman campañas ni se atribuyen checks del autor a TL/Revisor/Validador. No bateria global/Turbo/frozen-install o CI remota nueva. Las 34 omisiones backend historicas y 57 processor siguen no validadas en esas campañas.

### Revision independiente previa y MUT-01 resuelto

Revisor examino las 15 rutas originales y obtuvo 44 Node PASS/1 SKIP(mock) y Python Docker optativo 1 PASS/26 comprobaciones: se resolvio la omision Python previa sin sustituirlo por Node. OpenSpec53/53/config9/11/traza/higiene fueron correctos en la base anterior. Su REVIEW_FAIL inicial solo identifico MUT-01/P2: faltaba evidencia localizada de tres mutaciones previstas, no defecto funcional. Informe original SHA256 `62a3fc73f4dd904700cbc4ba3c0efdbdcb9007014b2c5ac902b1b5cda7b26916` preservado.

Desarrollador completo exclusivamente esos operadores en copias externas con tests fijos: retirar profiles[ai], sustituir clave backend por processor y retirar montaje gateway-data. Original dos PASS; cada mutante individual un PASS/un FAIL significativo ERR_ASSERTION en lineas225/244/229, exit1; restaurado dos PASS. Tres detectados, cero supervivientes/invalidos. Revisor verifico 47 artefactos/fuentes/test/restauracion sin nuevas ejecuciones y emitio REVIEW_PASS actualizado a las 23:06:23. Adenda SHA256 `393a6f6570d1d78ed229d079139938b772338963c3243df5243f16daab4a2396`. PM retorno independiente contra original de revision `7a0a7860293360d5d719015b08c770718d1efc3333f83a6b18106e73a4f2ddbf` PASS a las 23:07:04, antes de crear el original Validador conservado.

La reconciliacion conserva byte a byte fuentes de operadores, test fijo, Node24.19 y dependencia YAML del ensayo MUT-01; `mutation-reuse-proof.json` prueba vigencia, sin repetir operadores. Config/aliases/pins/gateway/processor propios de108 intactos, por lo que sus recibos anteriores mantienen autor/base/fecha/entorno y limites. README combinado, aplicaciones nuevas de salud y arranque integrado necesitan contraste afectado; no se convierte la review previa en relectura de la nueva base.

### Checkpoint y runtime listos para revalidar

El Validador ejecutó en base antigua: mock config/nueve servicios sanos sin secretos IA, health200 de backend/processor/Azure; bootstrap IA de gateway+DB+upstream sintetico sanos. No genero claves virtuales ni peticiones de modelo. Retiro sus contenedores/redes sin borrar seis volumenes propios sinteticos. Checkpoint externo `jup108-validation-20261008/checkpoint-20261008.md`: no dictamen final, pendientes IA completa/claves/persistencia/error/mapa de criterios. Sus imagenes antiguas no acreditan codigo047; no se presenta el checkpoint como reproduccion --build de la base nueva.

Desarrollador midio procedencia: backend/frontend antiguos carecen del codigo047; processor57fuentes/requirements y Azure11fuentes/requirements coinciden (no se afirma cotejo de assets Azure). Construyo tags propios nuevos sin sobrescribir anteriores, auditados contra 48 fuentes backend y 84 src frontend, labels revisionff2ea6be y manifiesto932:

| Servicio | Imagen para recorrido reconciliado |
| --- | --- |
| Backend | `jup108-reconciled-backend:ff2ea6b-20261008`, ID `sha256:467382172a7c311bf83bd1281f854b4986102ec29c0c7e1f07f28fc153159cfd` |
| Frontend | `jup108-reconciled-frontend:ff2ea6b-20261008`, ID `sha256:0fbdfd34b3b21f028d932bcfd5d692959622c917490722dcaf2f32584b76a69c` |

Las auditorias efimeras se retiraron; solo imagenes/cache propios retenidos, sin tocar stacks047 ni volumenes del Validador. No LLM pagado ni secreto real nuevo. La siguiente validacion usara copia actual, original PM nuevo, guia/mock9 e IA completa con ambos consumidores reales, upstream sintetico interno, claves/scopes/rechazo, salud negativa y claves persistentes; aplicara imagenes/puertos mediante override operativo externo documentado. No repetir llamadas reales historicas ni DockerServer. El impacto047 incluye salud configurada finita2..8/default8, agregado18/GET20, POST30/35 y polling30, saneamiento de metadata y panel autenticado; diagnostico LLM sigue deshabilitado en estos ensayos.

Paquete de integracion externo `jup108-integration-20261008/DELIVERY.md` SHA256 `a865440bdd6acb1f3f5640aa64a360590ed6aa1a8be2e17d47bb1fb0afed4882`; artifact-index.json `4b5ccae421c42f92d2b988c53939bf31a190940425f98c58447412c14f0e51aa`, 129 artefactos comprobados por TL. La comparacion de integracion verifica el delta Git expresamente autorizado; no es un falso PASS de perfil Green generico que excluye tests/specs entrantes, ni guard de lector contra original antiguo. TL solo consolida documentacion/evidencia. PM conserva originales independientes y autorizaciones; no hay aprobacion final humana ni permisos de publicacion por esta nota.


## Resultado local independiente sobre la combinación reconciliada — 08/10/2026

Este apartado actualiza el estado operativo de los anteriores; conserva sus dictámenes, recibos, fechas y límites. HEAD/base `ff2ea6be12abf1bea4789791c34efb46c3b55aa8`, rama `feat/JUP-108-litellm-compose`, delta local sin commit. **REVIEW_PASS focal y validación funcional local favorable para criterios 1–6. Criterio 7 parcial por hitos posteriores.** No son reviews humanas ni aceptación global.

Revisor focal, 23:35:56 Atlantic/Canary: README conserva íntegra la guía108 y añade seis líneas047 compatibles; once rutas críticas de Compose/gateway/tests conservan identidad; 129 recibos del paquete de integración cotejados. No repitió suites, Docker ni mutantes. Adenda externa `jup108-postmerge-review-20261008/addendum.md`, SHA256 `d10605bacdf1b925aa300142deed6beacdd9e02e27efc594ece3ff7fc5bdeb8e`. Original PM nuevo SHA256 `d84f960e69da7dbff62d2115d8b49b9a4f5ecb5c76df8abc7dd6935187adbdfa`, guard propio entrada/retorno PASS y retorno independiente PM PASS a las 22:38:28 UTC. REVIEW_FAIL inicial y resolución MUT-01 permanecen históricos.

Validador independiente, entrega 23:52:39 Atlantic/Canary: copia exacta933, original PM nuevo SHA256 `4f8d3fcce42d0b61939e18fcb8f46dcd630dbed3ad57a6346f9cc6f3dddbd266`. Guards propios entrada22:39:37UTC/retorno22:51:14UTC PASS, sin escrituras repo/Git incluidas transitorias. PM conserva y comprueba independientemente el mismo original. Son controles conductuales, no sandbox.

| Criterio oficial | Dictamen y evidencia propia del Validador |
| --- | --- |
| 1. IA integrada desde Compose principal | Favorable local: bootstrap y arranque completo de once servicios de producto sanos, ambos consumidores reales actuales, sin conexiones manuales entre proyectos. |
| 2. Mock sin gateway/OpenRouter | Favorable local: nueve servicios sanos, sin gateway ni clave upstream; login/salud/ingesta, job202→completed, vector persistido `8|mock|1`. |
| 3. Claves independientes, autorizado e inválido | Favorable local: dos claves distintas. Backend embedding200/1536, ambos chats403, inválida401; processor ambos chats y embedding200/1536, inválida401. Peticiones desde los contenedores reales. |
| 4. PostgreSQL y claves persistentes | Favorable local: gateway y PostgreSQL recreados manteniendo volumen, mismas claves y alcances después; proyecto IA nuevo persistió `1536|litellm|1`, mock8 intacto. |
| 5. Aliases, pins y seguridad | Favorable local: tres aliases y flags de privacidad/ruta observados con proveedor sintético, digests fijados, redes internas, PostgreSQL sin puerto y administración configurada loopback; sin dotenv entre933fuentes. No certifica enforcement externo. |
| 6. Instrucciones, tests y evidencia | Favorable local con vínculo permanente pendiente: secuencia documentada reproducida con adaptaciones abajo; local:test74/74PASS,0FAIL/SKIP, sin sumar campañas. Evidencia real histórica atribuida al autor; no nuevos pagos. |
| 7. OpenSpec/documentación, archivo, PR y reviews | Parcial: especificación/documentación y revisión/validación locales disponibles. Aprobación final, archivo autorizado, PR/CI y reviews humanas de Alejandro/Lucía pendientes del flujo posterior. |

Casos negativos: diagnóstico anónimo401; gateway parado produce failed/connection con API autenticada disponible200, y vuelve a ok al recrear. OpenRouter permanece unknown/not_verified, sin diagnóstico generativo. Claves inválidas401 y chat con clave de backend403 se conservaron tras recrear gateway/DB.

Entorno: Windows/Docker28.0.4/Compose2.34.0/Node24.17; proyectos propios `jup108-val-post-mock-20261008` y `jup108-val-post-ai-20261008`. Backend/frontend nuevos auditados (IDs completos en sección anterior), processor/Azure auditados reutilizados. Overrides externos de imágenes, upstream falso y salud no generativa; `--no-build --pull never`. No se afirma build literal del README: los builds habituales actuales son evidencia separada del Desarrollador. Docker Desktop no publicó al host los puertos IA con redes internas; bootstrap/peticiones mediante exec dentro de contenedores, conservando aislamiento y sin egress. Estas adaptaciones no acreditan un despliegue externo.

Recibos externos del Validador en `jup108-postmerge-validation-20261008/`: informe `validation-report.md` SHA256 `7a7081474b0fb73310b18067f3222c6c43153ca9d365b570253ce9f77b4343ec`; índice `artifact-index.json` SHA256 `3d303e7c2508ef9ff5735821e003263d0047e9ed1195dec6a44de373c192715f`, catorce recibos seguros cotejados por TL. Borrador de validación en plantilla, sin publicación, SHA256 `4f91aed68c3a09bd2a42b2c93229348fc3095ffa6a84821233dbf1078211a513`. El informe conserva comandos, imágenes, entorno, criterios y limitaciones; no se atribuye a Lucía ni sustituye su review humana.

Recursos propios cerrados con down sin -v: cero contenedores/redes activos; once volúmenes sintéticos nuevos y seis del checkpoint anterior retenidos. No se borraron datos ni tocaron stacks ajenos. Sin inferencias pagadas, claves privadas, instalaciones nuevas, Git o publicación.

### Controles de cierre y vigencia

TL contrastó62logs históricos conservados y las entradas actuales, no sólo los nombres de checks. Azure59PASS conserva identidad de app/tests/dependencias/datos; processor448PASS/57SKIP conserva producto/dependencias y su Docker opt-in modificado fue ejecutado independientemente por Revisor (1PASS/26comprobaciones). Backend reutiliza Green896PASS/34SKIP y las dos suites posteriores91PASS con fixtures finales; producto ejecutable idéntico salvo finales de línea. Frontend reutiliza suite completa629PASS y tres suites actuales99PASS: únicas diferencias funcionales respecto a aquella copia son hook/test de salud; las restantes son finales de línea. No se suman campañas ni se convierten omisiones en PASS. Tipos/lint/compilación conservan recibos propios y contexto original; los builds Docker actuales están separados.

El diagnóstico local sí consume Compose/.env modificados: Validador lo repitió74/74PASS. La matriz final debe incluir los controles documentales actuales y las equivalencias por componente, con revisiones/fechas originales. No hay nueva batería global/Turbo/frozen-install ni CI remota/Node22 comprobados. La referencia de aplicabilidad/matriz se conserva fuera del producto junto al expedienteTL.

Los guards históricos iniciales de diseño/Red/Green del autor no se han localizado. Existen aprobación pre-code comprobada, resultados históricos Red/Green y controles independientes actuales, pero no se reconstruyen snapshots ni se declara DoD PASS por esos datos. Su ausencia no es un defecto del producto ni justifica repetir pruebas ya acreditadas. PM debe canalizar una disposición humana explícita si no aparece la referencia original. La aprobación final humana, el DoD/disposición aplicable, el archivo específicamente autorizado y los controles previos a publicación siguen pendientes; no se archiva ni publica por esta consolidación.


### Instrucciones completas mock/IA y retorno — petición expresa de Paris

PM transmitió la petición a las23:55:02Atlantic/Canary del08/10: comprobar ambos recorridos completos y retorno IA→mock. TL completó README raíz «Modo mock: stack completo sin OpenRouter» con variables explícitas development/mock/mock/8, credenciales normales, selección de proyecto y prioridad del shell; hizo explícitos --env-file .env/-f docker-compose.yml y añadió «Volver de IA al proyecto mock original» con parada IA sin-v, doctor, arranque mock y smoke, preservando nombre/archivos/volúmenes originales. El apartado IA conserva bootstrap, dos claves, ambos archivos-f/profileai y arranque completo. infra/litellm/README enlaza los tres recorridos canónicos y distingue gateway aislado del stack completo.

Cambio exclusivamente editorial: comandos/topología y resultados ya comprobados por Validador, sin nuevas implementaciones o pruebas de aceptación; no se afirma haber ejecutado de nuevo el recorrido literal con --build ni haber probado una nueva transición IA→mock. La prueba independiente conserva mock8/IA1536 separados y persistencia de ambos, con sus adaptaciones de runtime declaradas. Los controles documentales posteriores incluyen diff-check y vigencia de especificaciones/trazabilidad/higiene; no se reconstruyen guards iniciales ni se amplían permisos Git/publicación.


## Excepción histórica aprobada exclusivamente para JUP-108 — 09/10/2026

Paris respondió «la apruebo» a la propuesta concreta de aceptar la ausencia de los tres registros históricos `guard-desarrollador-design`, `guard-desarrollador-red` y `guard-desarrollador-green`. PM confirmó y registró la decisión el09/10/2026 a las00:07:28Atlantic/Canary; es hora de registro, no segundo acreditado del mensaje humano. Fuente preservada: `jup108-historical-guards-exception-approved-20261009.md` en el expediente externo PM.

La excepción se limita a JUP-108 y se sustenta en aprobación pre-code comprobada, diseño/especificación y Red/Green históricos atribuidos, mutaciones sensibles, revisión/validación independientes actuales y originales/controles PM preservados. **Se resuelve por decisión humana la falta de esas referencias; no se afirma que los guards históricos pasaron.** No se fabrican snapshots, sustituyen originales, modifica el helper ni extiende la excepción a otras tareas/directrices.

El resultado original del helper sigue FAIL por esos tres registros ausentes, con matriz aceptada y sin errores de artefactos; se conserva sin alteraciones. La disposición humana se registra separadamente: no es un DoD nativo PASS. Los controles de repositorio aplicables y la revisión/validación local están acreditados con sus límites, por lo que3.2 queda completada bajo esta excepción expresa. El criterio7 global y3.3 siguen pendientes de sus etapas posteriores.

PM verificó independientemente el estado anterior a este registro a las23:06:58UTC del08/10 contra el mismo original SHA256 `4f8d3fcce42d0b61939e18fcb8f46dcd630dbed3ad57a6346f9cc6f3dddbd266`: exactamente seis documentos autorizados y ninguna otra diferencia/HEADchange. Este registro posterior sólo modifica evidencia/review/tasks, con control documental propio separado; PM conserva su referencia y control final pertinente.

Esta aprobación **no** es aprobación final de la entrega ni autoriza archivo OpenSpec, commit/push, PR, publicación o merge. No se repiten pruebas funcionales por el registro. Aprobación final humana, disposición final aplicable y archivo específicamente autorizado en la misma rama preceden las etapas de PR/CI/reviews humanas e integración.


## Post-validation approval — APPROVED, archivo autorizado y roles vigentes

Paris respondió «apruebo» al paso explícito de aprobación final de la entrega y autorización para archivar OpenSpec en esta misma rama, con la excepción histórica ya aprobada. PM registró la decisión el09/10/2026 a las00:08:45Atlantic/Canary; es hora de registro, no segundo exacto del mensaje humano. Fuente preservada: `jup108-final-approval-and-roles-20261009.md` del expediente PM.

Asignación vigente expresamente indicada por Paris, con fecha de asignación08/10/2026: **Paris Arcos liderazgo; Lucía Mateo pairing/coautoría; Víctor Méndez revisión de PR; Alejandro Aguado validación, pruebas y documentación**. La fuente de este cambio es la comunicación humana directa transmitida por PM, no una nueva lectura de Trello. No se presume participación realizada; se conservan atribuciones y asignaciones históricas con sus fuentes/fechas.

Revisión y validación locales favorables y controles aplicables acreditados; excepción exclusivamente JUP-108 para referencias históricas diseño/Red/Green no localizadas. Se conserva el FAIL original del helper y la aprobación de excepción separada, sin inventar PASS/guards/snapshots ni modificar el helper. El cierre final se registra bajo esa disposición humana expresa, no como DoD nativo PASS.

Se autoriza únicamente el archivo OpenSpec de JUP-108 en `feat/JUP-108-litellm-compose`, promoviendo su delta al canónico y conservando evidencia/resultado local. PR, CI y reviews humanas de Víctor/Alejandro permanecen hitos posteriores; commit/push, PR, comentarios/publicaciones y merge no están autorizados. La aprobación final/archivo no completan el criterio7 global ni atribuyen reviews humanas a los agentes.


## Archivo OpenSpec ejecutado y estado vigente — 09/10/2026

Tras aprobación final y autorización específica transmitidas por PM00:08:45Canary, OpenSpec archivó JUP-108 en la misma rama `feat/JUP-108-litellm-compose`, HEAD/baseff2ea6be, mediante archive con validación activada. Resultado exit0: tres requisitos añadidos y uno modificado promovidos a [containerized-runtime](../../openspec/specs/containerized-runtime/spec.md), sin implementación nueva. El cambio activo se movió a [2026-10-09-jup-108-litellm-compose](../../openspec/changes/archive/2026-10-09-jup-108-litellm-compose/proposal.md); [review](../../openspec/changes/archive/2026-10-09-jup-108-litellm-compose/review.md) y [DoD/disposición final](../../openspec/changes/archive/2026-10-09-jup-108-litellm-compose/local-dod-final.json) conservan resultados y decisiones. Referencias anteriores a la ruta activa describen su estado histórico.

Se conserva el DoD final nativo previo al archivo: FAIL exclusivamente por los tres guards históricos ausentes, sin eventos inválidos ni errores de artefactos; excepción expresa y aprobación final humanas separadas. No se genera un PASS artificial ni se vuelve a evaluar la ruta activa inexistente. Las verificaciones posteriores corresponden únicamente a especificaciones/trazabilidad/higiene/enlaces/diff afectados, no a repetir aceptación.

Roles vigentes indicados directamente por Paris, fecha de asignación08/10/2026: Paris Arcos liderazgo; Lucía Mateo pairing/coautoría; Víctor Méndez revisión PR; Alejandro Aguado validación/pruebas/documentación. No se afirma nueva lectura o actualización de Trello ni participación realizada. Criterio7 sigue parcial por PR/CI/reviews humanas e integración posteriores. Sin permisos de commit/push, PR, comentarios/publicaciones o merge; archivo no los concede.


### Comprobaciones posteriores al archivo

OpenSpec estricto:53/53PASS (el cambio108 ya no está activo); trazabilidadALL e higiene934 exit0. Se comprobaron41enlaces relativos de los documentos afectados, sin destinos ausentes, y los tres encabezados mock/IA/retorno de README. No se consultaron enlaces externos ni repitió aceptación.

El primer diff-check postarchivo detectó una línea vacía nueva al final de containerized-runtime generada por el propio archive (exit2). Se conserva ese resultado y la preimagen; se retiró exclusivamente el exceso de salto final, sin cambiar requisitos ni cuerpo. El control final de formato se conserva por separado en archive-diff-final.json del paquete de archivo, sin convertir el primer fallo en PASS.
