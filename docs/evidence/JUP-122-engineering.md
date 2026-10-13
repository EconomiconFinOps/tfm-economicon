# JUP-122: extracción de la entrega A

14/10/2026. Evidencia asistida; no sustituye Revision JUP-122 ni Validacion JUP-122.

## Procedencia y límites

Base develop `c30a7d0f28c04cae757b424222b34b232814303e` y base del chat de Paris
`f63c15031b65c99f1da149e867675ff771d3c1dd`. La infraestructura del chat no existía
en develop: la entrega incluye esa base, no sólo los cinco arreglos de Víctor.
Las ramas originales y el candidato local B `50e169fa` se conservan.

| Punto | Extracción y prueba |
| --- | --- |
| Stream SQL/RAM | Bloque events() de fc0f469; matriz initial/observer, 4 estados y 3 órdenes. |
| Planificador | Bloque _schedule() con recuperación tras OperationalError en operaciones y resúmenes. |
| Truncación | Adaptación del guard finish=length a required-documentation-v1. No incorpora decisión auto ni draft/final. Test exacto 502/incomplete y reintento backend sin historial parcial. |
| UTF-8 | El fixture de Paris ya tiene el emoji correcto. Se añade transporte de un byte con secuencia f09f9880 real y paridad stream/final. |
| Continuidad | Se conserva el índice vigente de develop, incluida JUP-113; se añade sólo el enlace A/B. |
| CD/HMAC | Provisión idempotente de 551fb81/85e1dc9; 16 pruebas mock. Actualización del agente CD instalado pendiente de integración aprobada, no ejecutada. |
| Migraciones | Reconciliación 002/005 de 731b5ea; conserva ledger, chat y anomalías. |
| Cancelación summary | Transporte de 97e8e043, sin importar el rediseño semántico. |
| JUP-119 | Mantiene servicios demo opt-in, fecha de referencia, API y navegación de develop. Fixtures chat declaran su fecha sintética. |

Fuera de A: rediseño de expresiones, segmentos, clasificación, citas y draft/final
de #121; campañas y scorer de B. Se mantienen los guardrails de la base de Paris.
CHAT_ENABLED=false por defecto; generate/resume/summary-retry devuelven 503 en
runtime desactivado. No se realiza ninguna inferencia real.

## Verificación local

- Backend ingeniería/migración/fecha: **103 passed, 16 skipped**; los omitidos
  necesitan base SQL nativa, no se cuentan como pasados.
- Runtime apagado e historial/migración: **56 passed**.
- Frontend: primer conjunto completo **925 passed / 59 failed**; los siete
  módulos afectados por la dependencia nueva useReferenceDate se corrigieron
  con fecha sintética explícita y pasan **76/76**. No se suman ejecuciones.
- Typecheck y build frontend correctos; aviso existente de chunk >500 kB.
- Topología **36 passed** y CD **16 passed**. Primer intento restringido falló
  por spawn/chmod del sandbox; repetición fuera del sandbox indicada arriba.
- OpenSpec **71 passed**, trazabilidad e higiene correctas.
- Processor: primera extracción **156 passed / 58 failed**; fixtures Windows
  escribían CRLF mientras los hashes esperaban LF. Escritura explícita corregida;
  repetición del grupo summary **94 passed** en 187,21 s. El resto de las
  156 pruebas favorables iniciales incluye gateway/UTF-8 y propiedad del esquema;
  no se presenta una suma como nueva suite completa.

Comandos: pytest sobre test_chat_operations_jup035.py, test_chat_metadata_jup035.py,
test_migration_reconciliation_jup035.py y test_reference_date*.py; segundo grupo
test_chat_disabled_jup122.py, test_chat_runtime_jup035.py,
test_chat_history_document_jup035.py y test_chat_history_migration_jup035.py.
Processor: test_chat_gateway_jup035.py, test_chat_summary_capacity_jup035.py,
test_chat_summary_private_jup035.py, test_chat_summary_gateway_jup035.py,
test_summary_cancel_reader_jup035.py y test_schema_ownership_static.py.
Frontend: pnpm --filter frontend test, typecheck y build; topología pnpm docker:validate;
CD python -m unittest discover -s tools/cd -p test_deploy.py.

Logs locales conservados en `materiales/07-evidencias/JUP-035-split` del workspace
padre. No se usan esos paths como evidencia accesible al revisor: las ejecuciones
de CI publicadas serán la evidencia reproducible de esta PR.

## Revisión de extracción

**Verdict: NEEDS DISCUSSION. Confidence: MEDIUM.** Revisión propia de la extracción,
no aprobación independiente. Se verificó que el delta processor respecto de
Paris contiene sólo truncación, cancelación y cambios ya integrados en develop;
no se importaron las reglas ni prompts de B. Se revisaron consumidores, migrador,
flag, HMAC y reconciliación de frontend. Los fallos concretos de fixtures se
conservan arriba. Falta la ejecución CI del candidato, SQL nativo y UI en navegador.

El workflow Chat engineering SQL crea una Cockroach24.1.11 desechable únicamente
en el runner y comprueba migraciones, carreras y plazos sin credenciales externas
ni proveedor. No usa DockerServer. Primer candidato `2b55e1e2`: [54 pruebas
favorables, sin omisiones](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38475631994).
El frontend también completa su job. El candidato siguiente sólo aísla el flag
de arranque en la fixture api: una secuencia disabled→operaciones reproducía 503
indebido por estado global entre tests; corregida, **27 passed**. No altera producto.
La CI vuelve a ejecutarse sobre ese commit; consultar siempre el head de la PR.

CI `3cdd0f64` ([run38475972374](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38475972374)):
backend **1811 passed/191 skipped**, Azure **81 passed**, frontend favorable.
Processor **1195 passed/98 skipped/1 failed**: la extracción había trasladado
la parametrización stall_body pero no la pausa posterior a las cabeceras de su
servidor simulado. El test completaba antes de cancelar en Linux. Se traslada
la pausa de 97e8e043 y se añade un Event explícito que verifica haber alcanzado
esa fase antes de cancelar. Focales de cancelación/lector: **6 passed**.
Es una corrección de fixture, sin modificar el transporte ni ampliar tiempos.
El verde local94 anterior no demostraba por sí solo la variante posterior a
cabeceras; este límite queda registrado. Se ejecuta nuevamente CI completa.
Ninguna evidencia histórica implica aceptación de respuestas ni levanta las
requests changes de #120/#121. La decisión de integración corresponde al equipo.
