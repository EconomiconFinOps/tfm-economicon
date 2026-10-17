# JUP-063: análisis de modelos para la memoria

Verificado 16/10/2026. Encargo: analizar los modelos, justificar el elegido y
preparar material para la memoria. Origen: chat
`01a1270c-e332-7462-9c90-706d49ade92c`. Preparación asistida por Codex;
sin adjudicación independiente, aceptación del equipo o incorporación al Google Doc.

## Alcance y seguimiento

No se abre una tarea duplicada: [JUP-063](https://trello.com/c/sRKGpYEy) ya cubre
los apartados e/g y [JUP-109](https://trello.com/c/orFyeUW2) cubre h.
[JUP-123](https://trello.com/c/TqtcumIN) aporta las mediciones del producto.
Roles, fechas y estado de esas tarjetas se conservan. La memoria canónica vive
fuera de Git conforme a [sus normas](../memoria/README.md).

## Conclusión contrastada

Se justifica DeepSeek V4.1 Flash/CoreWeave FP8 para el candidato LOCAL B corregido:
84/84 completed y 84 conformes provisionalmente, 495 comprobaciones. La comparación
histórica común favoreció GLM en calidad local(82 conformes frente a 77); DeepSeek
costó 49,3 % menos y tuvo menores percentiles de generación. Los 429observados en
la validación GLM posterior motivaron la elección operativa de DeepSeek.

No es una comparación causal del candidato actual ni superioridad universal.
Sonnet/Sol se mantienen como parciales técnicas, no como modelos semánticamente
peores. El banco solo no detectaba todos los defectos: la rúbrica adicional y la
revisión del contexto son necesarias, aunque aún provisionales. N5 actual no
ejecutada; N5 histórica no se hereda. No hay nuevo gasto para este análisis.

El [ADR-0023](../adr/ADR-0023-chat-model-selection.md) está Proposed. El ADR-0002
aceptado y el modelo del gateway compartido no cambian. V4 Pro no es V4.1 Flash.

## Entregables preparados fuera de Git

- [Informe completo](../../../materiales/07-evidencias/PR121-local-evaluation/tfm-model-analysis-20261016-v1.md):
  inventario, experimentos separados, tablas, decisión, limitaciones y fuentes.
- [Cifras y hashes recompuestos](../../../materiales/07-evidencias/PR121-local-evaluation/tfm-model-analysis-20261016-v1.json):
 14 fuentes primarias verificadas offline; SHA
 `0a1743eee14cdd6b3a4d4dc07050365756646968dcce43407dfccc0ce321b54d`.
- [Propuesta para e/g/h](../../../materiales/06-entregables/JUP-063-modelos/propuesta-modelos-2026-10-16.md):
  P1–P7, T1, referencias y tabla de cobertura del guion. Texto nuevo para revisar,
  no exportación o copia del documento compartido.
- `materiales/06-entregables/JUP-063-modelos/manifiesto-2026-10-16.json`:
  hashes de los tres entregables y del operador de recomposición.

La auditoría API final tiene SHA
`07d33e8b61affeb07b62ede7a7010920a1b96f08b30eddf72f4b15a9bc4cc06f`;
paquete 203 archivos con manifest SHA
`996304903e99d2a7449e8378dc605ae80a041f090b0e78f475866e1d79f43c3c`.
Las fuentes y campañas antiguas siguen intactas. La cota21,448811463/30 USD
incluye 13,99052050 USD de reservas históricas; no es factura o coste de este texto.

## Comprobaciones y pendientes

Se verifican hashes de snapshots/revisiones, recuentos de la comparación,
84 recibos de la campaña actual y manifiestos completos 203+185 archivos. Las cifras
de coste se calculan con Decimal; no se ejecutan inferencias o suites de producto
para redactar. El guion oficial Guion_PJ.md se leyó por su nombre, sin leer la
memoria compartida; se contrastaron requisitos de entregables, técnicos/funcionales
y evaluación. La propuesta marca lo que aporta y lo pendiente de otros apartados.

Pendientes: revisión humana de los textos, criterios/adjudicación del producto,
decisión de alcance N5 actual e incorporación/exportación por los responsables de
memoria. No se atribuyen a París/Lucía revisiones no realizadas. Ninguna tarjeta
se marca Done, ninguna PR se publica y no se envían mensajes a Discord.

## Registro final del entregable

- Propuesta SHA-256: `12c0f587256c9d344abd377a0f7a7b655cbfb4dbd6af0ff4fbab99fe0231e2ff`.
- Informe SHA-256: `aac40bd3b906c70f9f8758d93457c4a34b0d1bf415bfbc8f236b7b7b9bbe6a29`.
- Manifiesto SHA-256: `a3ada6275f39c07bef9dd47f14f1568f67a63dae58ef71f4bc7e3e8d8c23d7b4`.
- Verificación local: 14 fuentes, 23 enlaces, párrafos P1–P7 y cifras coherentes;
  OpenSpec estricto: 75 PASS, 0 FAIL. Sin cambios en apps/tools/packages.
- Trello actualizado por el puente DockerServer y contrastado por lectura:
  JUP-063 descripción SHA `3eb10a144cb76915c630949f809964e120e575220b367251419937405fe972b8`;
  JUP-109 descripción SHA `0458e24f828391a892820001064c690e13a86be4d0c40a0060af7a87d604f143`.
  Historial, lista, miembros, fechas y nombre conservados. Registro externo:
  `tfm-model-analysis-trello-update-v1.json`.
