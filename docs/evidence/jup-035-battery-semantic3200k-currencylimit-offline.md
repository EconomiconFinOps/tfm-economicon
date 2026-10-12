# JUP-035: conversion monetaria semantic3200k-currencylimit

Nota del 12/10/2026: esta evidencia conserva un ensayo historico y sus rutas
locales; esos recibos no son accesibles desde otro checkout. La
[guia reproducible](../validation/JUP-035-chat-reproduction.md) usa entradas
versionadas y el chat vigente. No sustituye ni revalida este resultado.

Paris acepta focal019/022 y autoriza corregir/repetir SOLO024. Parent comunica
019PASS022PASS024FAIL en j: formula monetaria con destino/direccion ambiguos,
no las citas irrelevantes anteriores. Historico full28i25PASS/3FAIL preservado;
no full28 nueva exigida ni declarada, no evaluacion formal JUP-070.

## Cambio y limites

Solo prompt general v3 y hash del manifiesto: sin destino, fecha y direccion del
cambio autorizados se conservan importes separados y se piden esos datos.
No formula que presuponga un importe en destino desconocido. Un ejemplo
hipotetico declara origen/destino y unidades de cambio, convierte cada importe
necesario al mismo destino sin inventar cotizacion ni inferir moneda de tenant
o configuracion regional. Instrucciones de unidades y condiciones contractuales
aceptadas permanecen intactas. No schema/validadores/retrieval/modelo/routing/
plazos/reintentos/salida3200 ni reparacion posterior de respuestas.

## Fases y resultados

- OpenSpec63/63 antes de tests/producto, escenario monetario explicito.
- Red: test existente falla AssertionError por instruccion ausente, exit1.
- Green: suites existentes de instrucciones y recursos,22passed (6.33s).
- Mutacion: retirada de la prohibicion de formula con destino desconocido en
  copia desechable; hash recalculado, AssertionError exit1 detectada.
- Guards design/red/green/mutation/docs sin cambios fuera del alcance.
- Backend/processor mismo bundle y conteo sintetico9205 con salida3200/margen1024;
  variantes schema1633, variable26, contexto1048576.

Worktree:
C:/Users/Trabajo/.codex/visualizations/2026/09/07/01a07c55-c454-7bb3-8053-cbf2ad70d2ec/e5-battery-corrections-worktree

Expediente:
C:/Users/Trabajo/.codex/visualizations/2026/09/07/01a07c55-c454-7bb3-8053-cbf2ad70d2ec/e5-context-compression-evidence/restart-20261011/jup069-real-battery/corrections/

Logs nuevos prefijo semantic3200k-currencylimit; referencias separadas por fase.
Referencia estable semantic3200k-currencylimit-product-stable.json.
Fingerprint producto612d6d66c6cafbf3b1095e27872842724d234e776d3a95e1ca57d8fa23496f34.
Bundle jup-035.chat.v3:1354e009842406653db08fbda974baf71ef3a993d2a516e312d6d67bf3f537de.
HEAD954b44298ccd94994f3ac420a3aec55c32eeb521 sin escrituras Git.

Pruebas offline de instrucciones e integridad, no garantia de obediencia real.
Revision independiente y ensayo real SOLO024 pendientes del parent.
Sin inferencia/administracion/publicacion. TOTAL.25USD, gasto comunicado
.220203420, restante.029796580, baseline.338851568 preservado.
