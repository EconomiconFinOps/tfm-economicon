# Memoria: análisis y elección de modelos

Verificado: 2026-10-16. Origen: chat `01a1270c-e332-7462-9c90-706d49ade92c`.
Encargo humano: analizar modelos, justificar el elegido, preparar material para
la memoria y abrir una JUP sólo si resulta necesaria.

## Resultado y razón

DeepSeek V4.1 Flash/CoreWeave FP8 elegido para el candidato LOCAL B a7f9502d.
La comparación común antigua favorecía GLM (82 conformes frente a 77), aunque
GLM tenía un fallo obligatorio. DeepSeek costó 49,3 % menos y tuvo menor latencia
de generación. Después, la API GLM del candidato corregido quedó en parcial4
por 429; DeepSeek completó 84/84 conformes localmente y 495 comprobaciones.
No se atribuye el salto al modelo: cambian código/corpus/recorrido. Sonnet/Sol
son parciales técnicas; tres respuestas Sol no adjudicadas no son tres aciertos.

No JUP nueva: JUP-063 ya cubre e/g y JUP-109 cubre h. Se mantienen responsables,
lista, fechas y estado. JUP-123 conserva evidencias del producto. No Done.

## Entregables y comprobación

- [Registro técnico](../evidence/JUP-063-model-selection.md) con fuentes y límites.
- [ADR-0022](../adr/ADR-0022-chat-model-selection.md), Proposed: no cambia el
  gateway compartido ni sustituye ADR-0002 aceptado; V4 Pro no es V4.1 Flash.
- Fuera de Git: `../materiales/07-evidencias/PR121-local-evaluation/tfm-model-analysis-20261016-v1.{md,json}`.
- Propuesta nueva e/g/h: `../materiales/06-entregables/JUP-063-modelos/propuesta-modelos-2026-10-16.md`.
  P1–P7/T1, fuentes y cobertura del guion oficial leído por nombre en Drive.
- Manifiesto: misma carpeta de entregables, `manifiesto-2026-10-16.json`.
- Operador offline: `build-tfm-model-analysis-v1.py`; 14 fuentes por hash,
  snapshots/revisiones y paquetes 203+185 verificados. Costes con Decimal.

No se leyó o modificó la memoria compartida ni se copiaron exportaciones a Git.
El texto es propuesta para revisar e incorporar, no una segunda fuente canónica.
No inferencias, claves, reservas o despliegues nuevos. Cota histórica al cierre
21,448811463/30 USD con 13,99052050 USD de reservas íntegras; no factura.

## Pendientes

Revisión e incorporación por liderazgo de JUP-063 (París) y JUP-109 (Lucía),
sin atribuir reviews realizadas; ajuste al máximo global de 20 páginas y nueva
exportación con hashes. Criterios/adjudicación independiente y alcance N5 del
candidato actual pendientes; no juez calibrado o conjunto ciego. B sigue local.
Para cifras de campañas, ver [evaluación local](chat-evaluacion-local.md).

## Cierre de preparación — 16/10/2026

Manifiesto SHA `a3ada6275f39c07bef9dd47f14f1568f67a63dae58ef71f4bc7e3e8d8c23d7b4`;
propuesta SHA `12c0f587256c9d344abd377a0f7a7b655cbfb4dbd6af0ff4fbab99fe0231e2ff`.
OpenSpec 75 PASS, 23 enlaces y 14 fuentes verificadas. JUP-063/JUP-109 actualizadas
por el puente autorizado, con lectura exacta y metadatos preservados; registro
`tfm-model-analysis-trello-update-v1.json` en la evidencia externa. No JUP nueva.
El registro técnico enlazado conserva los hashes de ambas descripciones y del
informe. Preparación completada; incorporación y aceptación siguen pendientes.
