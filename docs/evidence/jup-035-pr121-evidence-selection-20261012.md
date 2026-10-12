# PR121: selección de evidencia y diagnóstico de llamadas múltiples

Verificado el12/10/2026. Encargo: corregir ambas causas mediante un subagente de
implementación de Alejandro; no constituye review independiente. Base9c37a15,
código0d91d337aa944404a76afa03ffbbc3e2c5501e7f, en la rama propia
fix/JUP-035-auto-documentation. [PR121](https://github.com/EconomiconFinOps/tfm-economicon/pull/121).

## Estado posterior

Compatibilidad corregida en e56562f; validación parcial y pendientes en el
[informe vigente](jup-035-pr121-schema-compatibility-20261012.md). Los cortes
siguientes conservan sus resultados históricos.

## Actualización: validación real autorizada

El usuario autorizó explícitamente la campaña posterior. 018 y saludo fallan
con HTTP400 antes de emitir texto. Probes aislados: decisión sin esquema200,
esquema nuevo vacío400, esquema estático anterior200 y esquema nuevo retirando
únicamente uniqueItems200. Incompatibilidad localizada; no corrección publicada.
Full28/navegador finales sin ejecutar por fallo focal; multiplicidad pendiente.
Incremento conjunto observado en claves0.004454135USD; runtime detenido y límites
intactos. [Recibos de la campaña](../../../materiales/07-evidencias/PR121-herramientas-evidencia-20261012/authorized-validation.md).
La sección siguiente conserva el corte previo a esta autorización.

## Resultado y límites (corte anterior)

Entrega parcial: el esquema final queda limitado a la evidencia efectiva del
intento y sus regresiones pasan offline. No se acredita todavía la corrección
real de018/saludo ni la compatibilidad del nuevo esquema con el endpoint real.
Las llamadas múltiples siguen sin solución compatible demostrada con todos los
invariantes; se rechazan antes de ejecutar una búsqueda. No integrar todavía.

El envío de018 y el saludo fue rechazado por la revisión automática de aprobación.
Tras comprobar que sólo eran escenarios sintéticos y aportar la autorización
previa, una segunda evaluación volvió a exigir autorización humana específica
para el destino/envío y gasto. No se ejecutaron esas peticiones ni se intentó
una vía alternativa. Focal final, full28 y navegador con envío quedan NOT_RUN.

## Causas comprobadas

La reproducción directa con el system/herramientas del producto, preguntas y
contexto sintéticos del banco, mismo alias y routing, produjo dos IDs nativos
con índices0 y1 en005 y012.019/020/022 produjeron una llamada en esta muestra.
No son ensayos completos por /generations ni pruebas de fiabilidad. Demuestran
que en los dos primeros el rechazo no era confundir fragmentos de una única
llamada. En la full28 histórica habían fallado los cinco.

El catálogo del endpoint DeepInfra/fp4 paraGLM5.2 anuncia tools, tool_choice,
response_format y structured_outputs; no parallel_tool_calls ni max_tool_calls.
Esto concuerda con el404 previo al solicitar parallel_tool_calls=false, sin
probar por sí solo la causa interna del404. No se vuelve a introducir ese
parámetro ni se desactiva require_parameters, se cambia proveedor, se truncan
llamadas o se promete fiabilidad mediante una frase del prompt.
Fuentes: [catálogo del endpoint](https://openrouter.ai/api/v1/models/z-ai/glm-5.2/endpoints)
y [semántica del control paralelo](https://openrouter.ai/docs/guides/features/tool-calling).

El esquema final anterior permitía cualquier ID y metadatos de evidencia que
cumplieran forma/tamaño, dejando la membresía sólo al firewall backend. El
candidato histórico rechazado de018/saludo no se conservó. Su clasificación
exacta no se ha reproducido aquí; en el camino normal, processor ya rechaza IDs
duplicados antes del backend, lo que apunta a referencias desconocidas, pero
no sustituye capturar la causa estructural del candidato concreto.

## Cambio implementado

- Esquema privado derivado de los registros autorizados del intento: alternativas
  de objetos con id/kind/title/source exactos, sin registros duplicados. La lista
  vacía obliga a evidence[] y estados no accionables, conservando una respuesta
  útil sin fabricar una cita para alcanzar ok.
- Tras el resultado HMAC, la continuación conserva sus mensajes/correlación y
  añade sus fuentes a la selección del esquema final. No se modifica el input
  congelado ni se extrae autoridad de recuerdos, pantalla o texto de decisión.
- Backend y processor cuentan el esquema efectivo, incluyendo la extensión, y
  comparten la política effective-context-exact-records-v1 en el ensamblador.
  Manifiesto/hash/descriptor y OpenSpec actualizados; FinOpsResponse público1.0
  y autoridad financiera intactos.
- Firewall final independiente conservado. Diagnósticos cerrados distinguen
  evidence_unknown_id, evidence_duplicate_id, evidence_provenance y
  native_multiple_calls, sin candidatos, argumentos, prompts o secretos.
- No hay normalización de candidatos inválidos, retries ocultos, búsquedas
  adicionales ni tercera generación. Se mantiene la corrección del scheduler.

## Verificaciones

- Regresiones nuevas sobre la base:11FAIL/1PASS, por ausencia del esquema acotado
  y del diagnóstico diferenciado; el firewall de procedencia ya rechazaba.
- Processor134PASS: auto, gateway, private/HMAC, recursos y context budget.
- Backend83PASS iniciales en evidencia/contexto/auto/metadata/batería; después
 61PASS en evidencia/metadata/operaciones (solapan, no sumarlos).
- La unión posterior dio106PASS/2FAIL por dos fixtures que esperaban30/40ms antes
  de comprobar una reserva que tardó40–87ms. La repetición focal conserva2FAIL
  (409 o SSE donde el helper esperaba JSON). Los fallos se conservan. Se corrige
  únicamente la espera de esas pruebas mediante reserva SQL observable; no se
  relajan aserciones ni se cambia la implementación de operaciones.
  Repetición de la unión con esperas sincronizadas:108PASS,35.99s.
- Build backend/processor PASS.75 y69 archivos Python del interior de las
  imágenes coinciden porSHA256 con0d91d33; comprobación en contenedores sin red.
- OpenSpec67/67; trazabilidad de los siete cambios activos, políticas de PR,
  workflow CI y gobernanza pasan.
- CI38285627173 sobre6d5b399: processor1006PASS/71SKIP; frontend build/typecheck,
  API y OpenSpecPASS. Backend1652PASS/82SKIP/1FAIL: el test de tamaño de resumen
  calculaba el techo con el esquema público estático. La variante privada sin
  fuentes ocupa menos. Se ajusta el test al esquema efectivo más herramientas,
  conservando rechazo con un token menos y aceptación del contexto sin prefijo.
  Focal de tamaños/resumen/evidencia:31PASS. No cambia código del producto.
  Fallo y corrección quedan conservados; consultar los checks de PR121 para la
  ejecución posterior. La CI push omite JUP policy y no sustituye las reviews.

Los comandos pytest usan CPython3.12.13 real, PYTHONPATH del servicio y
.venv/Lib/site-packages, -B -m pytest -q -p no:cacheprovider y temporales propios.
Expediente externo del workspace: materiales/07-evidencias/PR121-herramientas-evidencia-20261012/
(native-reproduce.log, endpoints.log, budget-final.log, build.log y recibos
backend-final/backend-recheck/backend-synchronized). No hay credenciales.

## Gasto observado y operación

Baseline processor0.082811665USD; lectura posterior0.0856426375USD: delta
0.0028309725USD, igual a las cinco respuestas de decisión. Contador OpenRouter
compartido:0.122310483→0.134890510USD; delta0.012580027USD, no atribuible como
factura exclusiva a este ensayo. Límites y caducidad intactos; no renovaciones.
Estas lecturas no autorizan una nueva campaña después de caducar las claves.

Las imágenes nuevas están construidas pero no activadas. La instrumentación
intentó primero escribir en el rootfs y fue rechazada por sólo lectura; después
se montó un archivo de diagnóstico sólo lectura en el runtime sintético antiguo.
No cambió la validación ni llegó a enviar las preguntas bloqueadas. No se toca
el despliegue compartido. El expediente conserva también ese intento fallido.
Runtime temporal detenido; imágenes, volúmenes sintéticos y recibos preservados.

## Próximos pasos

1. Resolver la autorización específica del ensayo real, manteniendo0.50USD y
   saldo vigente. No renovar claves ni subir presupuesto de forma implícita.
2. Activar exclusivamente las imágenes verificadas en el runtime sintético,
   comprobar aceptación del esquema y018/saludo, después full28 en una revisión
   congelada y streaming/reapertura desde localhost/TLS.
3. Para llamadas múltiples, acordar un mecanismo con soporte demostrado del
   endpoint o un cambio explícito de contrato/configuración. La combinación
   actual de auto nativo, proveedor fijo y máximo una llamada sigue bloqueada.
4. Mantener001 como defecto semántico conocido fuera de este parche y completar
   las reviews oficiales; no convertir completed en aprobación semántica.
