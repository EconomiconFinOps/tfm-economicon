# Evidencia de extracción del colector — 15/10/2026

JUP: JUP-123 · https://trello.com/c/TqtcumIN

Base: `develop/53b43bb1e79b08967cc1b9efdf66669f11e8197c`.
Rama: `feat/JUP-123-response-collector`. Extracción autorizada por el usuario;
no representa aceptación de B ni validación humana independiente.

## Contrato solicitado por Lucía — 16/10/2026

Origen: «Implementa los cambios que nos piden en PR131».
Leídos todos los comentarios de conversación, reviews e inline (ninguno) antes
de editar `af8388d0`. La [validación de Lucía](https://github.com/EconomiconFinOps/tfm-economicon/pull/131#pullrequestreview-5543997424)
es favorable en su alcance probado; su [propuesta de contrato](https://github.com/EconomiconFinOps/tfm-economicon/pull/131#issuecomment-6209801137)
se implementa en esta entrega. No se atribuyen sus pruebas al autor ni se levanta
la solicitud de cambios de Víctor.

- Capacidad `ACCEPTS_UNMEASURED_DISTANCE = True` consultada en la herramienta
  importada: conserva corpus con `distance: null`, respuesta y citas. Sin ese
  booleano exacto se mantiene el bloqueo legado; valores mal formados o no finitos
  bloquean en ambos modos. No se modifica la rama de JUP-071.
- `structured` conserva `status` y `has_next_actions` sin texto de acciones;
  los datos ausentes o no verificados siguen como `null`.
- `execution.collection.server_reported` conserva procedencia por muestra,
  `attested: false`, desde recursos públicos revalidados. No inventa hashes ni
  uso ausentes y distingue el hash del bundle incluido en `prompt_version`
  del hash del texto del prompt. Contrato completo en la [guía](../validation/chat-collector.md#contrato-con-jup-071-y-el-dashboard-de-jup-121).
- Opcionales solicitados implementados: `--all-repetitions`, resúmenes de estados,
  `--strict` con código 3 después de guardar evidencia parcial y diagnósticos
  propios con motivo seguro. Los planes nuevos v2 fijan contenidos relevantes,
  incluidas métricas y calibrador; commits ajenos no invalidan ni cambian la
  identidad de comparación. Los planes v1 siguen con su contrato anterior.

Verificación propia de esta entrega: pruebas locales de biblioteca estándar,
**48/48 conformes**, sin inferencias ni servicios externos de pago. El primer intento en sandbox
Windows encontró ACL en los temporales; la ejecución con acceso normal pasa.
La integración con JUP-071 original `81ceafc6` usa 87 fixtures/521 GET locales,
cero POST y tres raw aceptados por review-sheet/score/compare; se conserva un fallo
técnico y reexportar produce bytes idénticos. No acredita calidad de un modelo.
La exportación conjunta coincide byte a byte con las individuales y el modo
estricto devuelve 3 por el fallo preservado. Plan y recibos v1 históricos se
revalidan y exportan correctamente. Recibo externo:
`JUP-123-collector/integration-10dd5cef/summary.json`; guion reproducible en
`materiales/07-evidencias/JUP-123-collector/integration-contract-20261016.py`
del espacio de trabajo padre. Higiene conforme (1597 archivos), trazabilidad
conforme y OpenSpec estricto 74/74. Estos controles no sustituyen CI remota.

La rama remota de JUP-071 consultada el 16/10 sigue en `81ceafc6`, sin anunciar
la capacidad. Su adaptación corresponde a esa entrega; las pruebas del camino
con capacidad son fixtures explícitas, sin fingir una integración ya publicada.
El fallo previo de seis pruebas de salud backend en `af8388d0` es ajeno a este
delta y conserva su diagnóstico histórico en continuidad. CI del nuevo commit,
revisión de Víctor y actualización de validación siguen pendientes al preparar
esta evidencia. No se integra, despliega ni ejecuta una campaña real.

## Corrección tras revisión — 16/10/2026, corte anterior

Leídos la [revisión de Víctor](https://github.com/EconomiconFinOps/tfm-economicon/pull/131#pullrequestreview-5540209141)
y el [contraste real de Paris](https://github.com/EconomiconFinOps/tfm-economicon/pull/131#issuecomment-6203151803)
contra la cabeza `5cae4942`; no había comentarios inline. Ambos corroboran que
A no entrega distancia y que el formato anterior perdía la trazabilidad de esas
filas ante el scorer. El ensayo real es evidencia de Paris, no una ejecución
real de este corrector ni una aceptación de B.

Se bloquea la exportación si algún fragmento de corpus no trae distancia
numérica: `invalid_response`, respuesta y citas vacías, originales y evidencia
completa conservados. Esto no invalida la recogida verificada ni modifica el
evaluador de JUP-071. Con A real todas las filas con corpus quedan bloqueadas
hasta que JUP-071 admita esa evidencia sin distancia.

Pruebas posteriores: **33/33 conformes**, sin errores ni omisiones. La prueba
nueva reproduce un fallo de aserción en la cabeza anterior y pasa con el arreglo;
dos intentos previos en sandbox no llegaron a esa aserción por ACL de temporales.
Se mantienen los controles con distancia real y sin corpus, los suplementos y
los originales. Contraste con el scorer original de JUP-071/`81ceafc6`:

| Fixture sintética | Antes | Después |
| --- | --- | --- |
| Corpus sin distancia, cita auténtica y cifra 4321 sólo en el fragmento | `fail`, una cita colgante y cifra no trazable | `blocked`, sin puntuar contenido |
| Mismo fragmento con distancia medida 0.2 | `pass` | `pass` |

Los juicios de ese control son fixtures sintéticas expresamente identificadas,
no revisiones humanas. No se ha llamado al proveedor. Evidencia local externa:
`PR121-local-evaluation/collector-pr131-scorer-fixtures-v1/proof.json` y logs
`collector-pr131-{red,green}-v2-native.txt`. También se corrige la separación de
palabras y números en los documentos y OpenSpec añadidos. La solicitud de
cambios sigue pendiente de la aprobación del revisor; no se declara CI del
candidato corregido antes de publicarlo y comprobarla.

La integración completa se repitió después del arreglo: 87 fixtures, 521 GET
locales y tres exportaciones de 29 casos aceptadas por el evaluador original;
fallo técnico conservado y reexportación idéntica, sin juicios de calidad.
Resumen externo: `JUP-123-collector/integration-4533cf28/summary.json`.

## Comprobaciones iniciales del 15/10 — históricas


- 31 pruebas de biblioteca estándar pasan, sin omisiones: 9 del colector,
  6 de reconciliación RAG y 16 del adaptador 071. Incluyen servidor HTTP local,
  fallos/redacción, archivo alterado, identidad cruzada, citas ajenas,
  recuperación incompleta, salidas exclusivas y exportación estable.
- Integración con el evaluador 071 real, commit
  `81ceafc67ba400414040b1468d795a41d9d5468d`: plan de 87 muestras,
  521 GET contra servidor simulado,0 POST/0 llamadas al proveedor. Tres raw
  de 29 casos aceptados por review-sheet, score y compare; fallo técnico introducido
  conservado, reexportación de r1 idéntica byte a byte. Son fixtures de transporte,
  no respuestas de un modelo ni una tasa de robustez. No se crearon juicios.
- Regresión del evaluador existente: 110 pruebas PASS. Gobernanza: 97 pruebas
  Node PASS; trazabilidad e higiene conformes; OpenSpec estricto: 74 elementos PASS.
  Las ejecuciones de Python/Node en sandbox encontraron restricciones de ACL o
  procesos; estos resultados son de las pasadas completas con acceso normal.
- El contrato inspeccionado de develop ofrece estado, contexto, evidencia,
  resultado e historial requeridos. No se ha validado un despliegue de A.
  A ya pertenece a esa base por `cf821570` (#130); no es necesario copiar su rama.

Reproducir el conjunto portable:

```sh
python -m unittest discover -s tools -p 'test_chat_eval_collect*.py' -v
```

La primera ejecución en el sandbox Windows falló por ACL de directorios
temporales. La ejecución con acceso normal encontró una aserción del diagnóstico
de timeout: el colector interno conservaba el error pero el adaptador perdía la
clase al fallar la comprobación de identidad. Se corrigió preservando la clase
de la lectura original, sin texto sensible. La pasada final 31/31 es posterior
a esa corrección. No se han borrado ni reconciliado recibos de campañas reales.

## Límites y revisión pendiente

El contrato público puede omitir RAG posterior al contexto inicial; se necesita
el payload real exacto para suplementarlo. Sin él se conserva el bloqueo. La
distancia no disponible no se reemplaza por 0. La copia de JUP-071 es código local de
confianza y debe permanecer congelada durante la campaña; sus comprobaciones
de fuentes se ejecutan otra vez al exportar. Metadatos locales no atestiguan el
despliegue. La [guía](../validation/chat-collector.md) detalla comandos y salidas.

La entrega no toca apps, prompts, corpus, bancos, ledger, contadores, reservas,
claves ni límites. Gasto incremental de esta extracción: 0 USD. Reviews,
comprobación del despliegue de A, campaña real de JUP-071 y aceptación semántica de B
siguen fuera de esta validación.
