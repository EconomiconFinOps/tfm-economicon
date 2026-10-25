# JUP-035: correcciones focales semantic3200j-all3

## Alcance y autorizacion

Paris autoriza corregir las tres reglas generales y probar solo los tres casos
afectados. La bateria real full28i permanece 25 PASS/3 FAIL (019,022,024);
la aceptacion anterior de dos limitaciones queda sustituida, no se reescribe
el resultado historico. No se exige full28 nueva para esta entrega si el
ensayo focal es aceptado; no equivale a 28 PASS actuales ni a JUP-070 formal.

Cambios exclusivos del productor:
- Conservar unidad completa y denominador temporal del input junto al resultado
  en answer, sin convertir tasa en total ni dejar la unidad solo en otros campos.
- No completar duraciones, precios o condiciones contractuales con conocimiento
  general sin respaldo del input o corpus; explicar concepto y pedir condiciones.
- No citar instrucciones internas o aritmetica del usuario ni agregar afirmaciones
  irrelevantes para justificar fuentes.

Solo prompt v3, su hash de manifiesto, prueba existente de instrucciones,
escenario OpenSpec y continuidad. Sin cambios de esquema, validadores, corpus,
retrieval, modelo, routing, reintentos, plazos, salida3200 o politica financiera.
No borrado de citas ni reparaciones posteriores a la respuesta.

## Evidencia local

Worktree: C:/Users/Trabajo/.codex/visualizations/2026/09/07/01a07c55-c454-7bb3-8053-cbf2ad70d2ec/e5-battery-corrections-worktree

Expediente externo:
C:/Users/Trabajo/.codex/visualizations/2026/09/07/01a07c55-c454-7bb3-8053-cbf2ad70d2ec/e5-context-compression-evidence/restart-20261011/jup069-real-battery/corrections/

HEAD preservado: 954b44298ccd94994f3ac420a3aec55c32eeb521.
Referencia estable: semantic3200j-all3-product-stable.json.
Fingerprint producto: bd20e30410d640a4f4bac288dcb6f4bdc5cc2e66e4a1efc800001f76ec6e59b9.

Fases distintas, referencias nuevas y guards sin rutas inesperadas:
- design: OpenSpec estricto validado antes de escribir tests/producto.
- red: un test existente falla por ausencia de la nueva instruccion, exit1,
  AssertionError (no fallo de importacion ni infraestructura).
- green: tests/test_chat_battery_corrections_jup035.py y
  tests/test_chat_resources_jup035.py: 22 passed.
- mutation: tres copias desechables retiran unidad, respaldo contractual y
  exclusion de citas internas/aritmetica; hashes recalculados en las copias.
  Los tres fallan por AssertionError, exit1, sin cambios al original.

Los logs llevan prefijo semantic3200j-all3 y no sustituyen ensayos anteriores.
Incidente menor conservado: los primeros conteos offline se invocaron sin el
argumento de servicio y fallaron IndexError; checkpoint inicial no generado.
Los registros count-*-retry conservan la ejecucion corregida sin reemplazarlos.
Conteos backend/processor identicos: esquema1633, variable26,
total sintetico9092 incluidos margen1024 y salida3200, contexto1048576.

Bundle: jup-035.chat.v3:2fc2813791dba7d139cb033181966533f9219aaace6dc8528f25a66b691a805a.
Schema publico y variantes privadas sin cambios; manifiesto verificado por las
pruebas de recursos. El historial v2 y los artefactos archivados no se modifican.

## Limites y siguiente gate

Las pruebas de texto e integridad detectan perdida de instrucciones, no garantizan
obediencia o sustento semantico del modelo. No hubo inferencia ni administracion.
Revision independiente y aceptacion real focal019/022/024 pendientes del parent.
La revision actual no tiene full28 ni cierre global; conservamos FAIL originales.
Presupuesto autorizado TOTAL0.25USD, baseline0.338851568, gasto comunicado
0.212688338, restante0.037311662. No incrementar topes ni reiniciar referencia.
Sin commits, push, publicaciones o cambios de trackers por esta entrega.
