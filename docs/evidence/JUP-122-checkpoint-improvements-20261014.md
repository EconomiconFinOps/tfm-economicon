# JUP-122: tres mejoras de ingenieria del checkpoint

## Candidato y alcance

Destino propio: `codex/JUP-122-checkpoint-improvements`, HEAD sin cambiar
`318a56f31828be50f8960860f69172f51046734d`, base de PR130 comprobada antes de aplicar.
Referencia de lectura: checkpoint Paris
`98586e860d5c625441f9fd69ab3377a8638baf7e` y tokenizer
`a8f4dddc05d85b17ed2023388c8857d1ce538882`.
Paris aprueba ejecutar el alcance de tres puntos el 14/10/2026. Sustituye el
borrador de siete puntos: no se incorpora preparacion HMAC local, recuperacion
UI, rechazo de memoria vacia, reinicio/buffers ni semantica de JUP-123.

| Mejora | Archivos principales | Resultado local |
| --- | --- | --- |
| Tokenizer fuera de Git | apps/processor/build_tokenizer.py; tools/test_build_tokenizer.py; Dockerfiles backend/processor; .gitignore y ambos contextos .dockerignore; CI; package.json; README; test_compose_chat_jup035.py | Artefacto retirado del indice y cache local ignorada. Descarga fija validada en ambos builds; runtime offline carga el mismo recurso. |
| .secrets fuera de releases | tools/cd/deploy.py; tools/cd/test_deploy.py; exclusiones Git/Docker y tools/docker-topology.test.mjs | Filtro aplicado a cualquier nivel, HMAC y symlinks preservados. |
| Fixture SQL | apps/processor/tests/test_chat_summary_sql_deadline_jup035.py; .github/workflows/chat-engineering.yml y test de CI | Datos sinteticos propios, espera shield/wait_for y cierre real; 6 controles SQL y 2 controlados pasan, sin omisiones. |

El tokenizer conserva revision `a66456a59f21345d1e5e586345c448a9106d29d7`,
20217442 bytes y SHA256
`19e773648cb4e65de8660ea6365e10acca112d42a854923df93db4a6f333a82d`.
No se alteran manifiestos, prompts, schema, generacion, ventanas, deadlines o
activacion de A. `CHAT_ENABLED=false`, protocolo `required-documentation-v1`,
HMAC de CD y runtime permanecen intactos. Solo el copiado CD excluye un directorio
adicional. El tokenizer sale del indice sin borrar su cache ni reescribir historia.

## Pruebas y resultados

| Comprobacion | Resultado |
| --- | --- |
| Red tokenizer | Descargador ausente: importacion falla antes de implementar. |
| Red CD Linux | 1 fallo: .secrets se copiaba; los controles HMAC existentes pasan. |
| Red SQL | La base configurable falla contra el nombre historico requerido por la fixture. |
| Tokenizer | 4 pruebas: pins, descarga positiva, tamano/hash incorrectos sin reemplazo, cache offline. |
| CD Linux/Python3.12 | 57 pruebas sin fallos ni omisiones y 3 de workflow. Incluye enlaces simbolicos reales. |
| SQL processor | 8 passed, 0 skipped; base Cockroach24.1.11 propia. 6 controles nativos y 2 controlados. |
| Integridad de escenarios SQL | Las 29 aserciones de los 5 escenarios originales siguen identicas por AST. |
| Controles negativos | Omitir integridad o exclusion de .secrets en memoria provoca fallos; no modifica producto. |
| Topologia/workflows afectados | 52 pasan inicialmente; CI final ampliada, 14/14. |
| Imagenes | Backend/processor construidos con descarga verificada real y cargados sin red, root de solo lectura. |
| Frontend | 984/984 tests, tipos, lint y build pasan. Warning existente de hook y bundle >500 kB. |
| Azure Cost API | 81/81 tests. |
| Processor amplio | 1202 passed, 1 failed, 92 skipped; unica expectativa obsoleta de copiar el asset desde Git. Se adapta solo ese test y el modulo pasa 10/10. No se repite la suite completa. |
| Backend amplio | 1851 passed, 6 failed, 145 skipped. Los seis fallos se detallan debajo; 8 controles de autorizacion pasan al repetirlos aisladamente. |
| Proyecto | Build del workspace, OpenSpec estricto 71/71, trazabilidad, higiene y herramientas de gobernanza pasan. |

Las omisiones de las tandas amplias no se cuentan como comprobaciones superadas.
Las pruebas SQL afectadas se ejecutaron con URL propia y requisito
obligatorio, sin omisiones. No se presenta la suma de ejecuciones parciales como
una unica tanda completa verde ni se sustituye revision/validacion humana.

## Limitacion del control global backend

`test_system_health_jup047.py` genera JWT al construir su parametrizacion durante
collection. Su helper les da cinco minutos. En la tanda amplia, fueron emitidos
a las 13:16:13 de Canarias y caducaron a las 13:21:13; el primer caso fallido
se ejecuto a las 13:21:18.870. El producto devolvio 401 al token caducado, mientras
el caso esperaba 400/403 para examinar tenant. El contraste focal da 8 passed.
No se ha modificado autenticacion ni esta fixture de JUP-047. Su estabilizacion
requiere alcance separado; no se declara cierre verde del control global.

Tambien se conservan preparaciones fallidas: redes automaticas Docker agotadas,
puerto Windows reservado, imagen QA antigua sin email-validator y CD sobre Python
3.10 (extractall filter requiere el Python3.12 del proyecto). Se soluciono el
entorno con red propia sin puertos publicados e imagen QA con los locks vigentes.
No se debilitaron controles ni se ampliaron tiempos de produccion.

## Identidad, reproduccion y entrega

- Backend: `sha256:3f7a25adb4b5d9ae03fa0b8fb7b1acc9bd4a751bb615d704ad53293a08e7173f`.
- Processor: `sha256:d4c5c6e387386f962e53ad5ee468207d5d4ba9fa3bbdef53dd171de5bf0c563c`.
- QA desechable: `sha256:45b8056ac22f9035396dd3f4826d1ab9b533c948a50753ce515bb3e09eb65bfb`.
- Recursos en ambas imagenes: chat `jup-035.chat.v3:d9b6946f56baf5ed2172ab4f116e3c57f45f68b1db387d74c16ec48ff5a279bc`; summary `jup-035.summary.v3:b77cb54456152e08db25c57fef510b5864b0f2679db76e743cfe7a5b8a9c8634`.

Reproduccion: `corepack pnpm tokenizer:prepare`, `corepack pnpm tokenizer:test`,
`corepack pnpm cd:test`, `corepack pnpm ci:check:test`, builds de Dockerfiles y
pytest SQL segun el workflow, con Python3.12 y bases nuevas exclusivas.
Para SQL processor usar `JUP035_COCKROACH_TEST_URL` y
`JUP035_REQUIRE_NATIVE_SQL=true`; la fixture crea su tabla minima y solo su fila.
No acredita migraciones completas del producto. El workflow conserva los
controles backend y anade processor en otra base.

Recibos, logs Red/Green, hashes y guard se conservan fuera del repo en el paquete
`jup122-checkpoint-improvements-precode-20261014`; no contienen claves reales.
Los comandos obligatorios se ejecutaron a traves del workspace; Python se
ejecuto en Docker3.12 sobre el arbol montado en lectura y frontend en Windows.
Los scripts personales de ejecucion no se incluyen en Git.

Los recursos temporales se retiran al terminar; las imagenes quedan disponibles
para reproduccion. Sin llamadas pagadas, full28, commits, push ni publicaciones.
La rama del companero y el checkpoint fuente permanecen intactos. La CI remota y
las reviews oficiales siguen separadas de estos resultados locales.
