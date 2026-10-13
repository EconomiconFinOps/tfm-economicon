# Tareas técnicas JUP-055

Estado reconciliado por el Coordinador el 06/10/2026 con los handoffs de refinamiento, comparación, datos v2, documentación y revisión interna. Solo se marcan tareas con evidencia de ejecución; la ejecución independiente y matriz general se han realizado; la disposición del límite móvil, la aprobación postvalidación y las puertas de integración permanecen abiertas.
No comenzar tests/producto sin aprobación humana y encargo del Coordinador.

## 1. Puerta pre-código

- [x] 1.1 Validar OpenSpec estricto, trazabilidad JUP-055, enlaces locales y límites de rutas; entregar resultados al Coordinador.
- [x] 1.2 Obtener aprobación explícita de Paris del diseño completo, incluyendo retirada de demo/exportación del panel, límites de representación y consultas sin snapshot común.
- [x] 1.3 Confirmar edición README mínima ante JUP-104/JUP-105 y rutas exactas por fase; conservar approvals en artefactos del Coordinador.
- [x] 1.4 Confirmar herramienta de mutación existente y matriz de checks; pedir decisión si exige excepción, sin instalar herramientas unilateralmente.

## 2. Red: comportamiento observable antes de implementación

- [x] 2.1 Tests de meses UTC: seis completos por defecto, febrero–agosto siete, marzo–junio cuatro, único mes, cruce de año, límites exclusivos, años 0001–0099, vacío/formato/inversión rechazados sin red.
- [x] 2.2 Tests de consultas: total más N meses (único mes sin duplicación), misma agrupación/tag/tenant, clave canónica coherente, fechas devueltas erróneas rechazadas, máximo tres simultáneas y cancelación de pendientes.
- [x] 2.3 Tests de dinero: varias monedas sin suma/conversión, importes >MAX_SAFE_INTEGER exactos, crédito/cero, diferencia último–primero elegibles no cero, negativos, mensajes uno/ninguno y errores que impiden extremos; conservar cero/ausencia en serie.
- [x] 2.4 Tests de presentación: meses ausentes/fallidos en posición, línea con huecos, tabla exacta y límite de representación, errores total/mensual/409, partial/null e indatados sin doble conteo, sin datos distinto de cero.
- [x] 2.5 Tests de aislamiento: cambiar tenant/periodo/agrupación/tag/sesión durante carga/refetch, respuesta tardía ignorada, sin token/tenant sin consultas ni importes cacheados visibles.
- [x] 2.6 Retener regresiones JUP-026 y legacy; ajustar únicamente expectativas sustituidas por alcance aprobado. Demostrar fallo por comportamiento requerido, no por entorno/imports, y entregar VALID_RED antes de Green.

## 3. Green: implementación bajo tests fijos

- [x] 3.1 Añadir utilidades puras de límites/meses, importes exactos y comparación firmada.
- [x] 3.2 Implementar hook ejecutivo con identidad de conjunto, cola de tres, abort, validación de metadatos, error por consulta y reintento completo sin mezclar ejecuciones.
- [x] 3.3 Sustituir demo del panel por selección mensual, totales por moneda, comparación de extremos, tendencia y desglose del intervalo; conservar cinco agrupaciones/tag, origen almacenado y ahorro no disponible.
- [x] 3.4 Reutilizar tarjetas/controles/tokens/tooltip, estados anunciados, tabla accesible y layout adaptable; quitar export/inventario ficticios solo de este panel.
- [x] 3.5 Pasar tests afectados, typecheck, lint y build; ejecutar matriz de regresiones acordada. Entregar GREEN con límites y sin alterar tests ni especificaciones.

## 4. Documentación de producto

- [x] 4.1 Actualizar mínimo README: ruta ejecutiva real, meses inclusivos/seis iniciales, primer/último mes con coste no cero y meses efectivos, moneda/precisión, consultas almacenadas y límites, demo restante en otras pantallas.
- [x] 4.2 Incluir instrucciones reproducibles para cargar datos de referencia y recorrer cero, huecos, créditos, multimoneda, partial, errores y cambio de ámbito.
- [x] 4.3 Verificar enlaces ADR existentes y docs; no duplicar backlog ni introducir una decisión arquitectónica nueva.

## 5. Sensibilidad, revisión y evidencia

- [x] 5.1 Mutación en copia desechable de lógica cambiada, con tool existente; clasificar cada superviviente y demostrar producto final sin cambios. Solicitar excepción material si procede.
- [x] 5.2 Revisor independiente: código, tests, docs y concordancia con alcance; devolver hallazgos sin commits.
- [x] 5.3 Validador independiente: demostrar todos los escenarios funcionales y criterio oficial aplicable, un caso límite/error, y capturas escritorio 1440×900/móvil 390×844 en carga/error/vacío/partial/foco/selección.
- [x] 5.4 Coordinador registra comandos, resultados y limitaciones, ejecuta guards y checks finales; repetir afectados tras correcciones/cambios de base. Obtener aprobación humana postvalidación.

## 6. Puertas de integración posteriores

- [x] 6.1 Con autorización expresa, archivar el cambio en esta misma rama después de revisión/validación local, evidencia y aprobación postvalidación.
- [ ] 6.2 Crear/publicar PR a develop, enlazar tarjeta/evidencia y solicitar las dos reviews solo con permisos expresos y previa comprobación de pendientes.
- [ ] 6.3 Acreditar participación real de pairing y reviews humanas de Alejandro/Lucia con formato y orden de CONTRIBUTING; no declarar cumplimiento mediante agentes internos.
- [ ] 6.4 Antes de integrar, leer todo feedback, comprobar CI/ausencia de pendientes y revalidar afectados por base; merge y cambios Trello con sus autorizaciones propias.


## 7. Refinamiento solicitado el 06/10/2026: desglose y datos diversos

Las tareas de este apartado necesitan aprobación específica del diseño validado.
No reutilizar la aprobación inicial como aprobación de estos cambios ni
los resultados anteriores como evidencia vigente después de cambiarlos.

- [x] 7.1 Validar este refinamiento y su plan v2 (OpenSpec, trazabilidad, enlaces, guard); el Coordinador obtiene aprobación explícita de Paris y asigna rutas/fases.
- [x] 7.2 Red: demostrar en el producto actual que el desglose no precede a totales/comparación/tendencia; cubrir cambio servicio→proyecto con grupos distintos y finanzas invariantes usando pruebas observables proporcionadas, sin duplicar tests monetarios.
- [x] 7.3 Green: mover una sola instancia del desglose debajo de controles/avisos; conservar gating, tabla y semántica; ejecutar tests afectados y suite frontend/tipos/lint/build. Sensibilidad del caso de orden mediante mutación manual solo bajo excepción confirmada para esta fase.
- [x] 7.4 Con despacho de datos separado, preparar externamente referencia/SQL v2 con 16 filas EUR core, 3 USD y 2 EUR growth; preservar artefactos v1/hash/estado previo, comprobar precondiciones y mantener un único run completado por suscripción.
- [x] 7.5 Aplicar transacción únicamente en la DB desechable asignada; verificar 21 registros/3 runs, totales mensuales y grupos independientes del diseño, cero/créditos, precisión USD, no solapamiento y tenants separados; guardar instrucciones/cambios exactos externos, sin datos o secretos en repo.
- [x] 7.6 Revisor y Validador independientes repiten lo afectado: orden/estados, cinco agrupaciones con importes EUR distintos, finanzas invariantes, USD y growth; capturas escritorio/móvil con versión de dataset/revisión. Coordinar instrucciones de producto mínimas si cambia el recorrido documentado, sin modificar README en este despacho.
- [x] 7.7 Coordinador reconcilia evidencia histórica y actual, conserva pendientes de Layout/latencia/sesión y los gates humanos; no marcar validación completa ni archivar/publicar por este refinamiento.



## 8. Comparación con primer/último coste no cero — 06/10/2026

El criterio humano sustituye el anterior, conservado en aprobaciones/evidencia
históricas. Las tareas de comparación de apartados previos se interpretan bajo
esta regla y el mapa de sustitución de design.md. Solo aprobación y encargo del
Coordinador permiten modificar tests/producto/docs/datos en fases respectivas.

- [x] 8.1 Validar diseño/escenarios/trace/higiene/guard; presentar selección lineal y política de errores/partial, conservar approvals históricos y obtener gate pre-código del diseño validado.
- [x] 8.2 Red: preservar revisión/hash/logs previos fuera del repo y registrar sustitución de casos de base cero/extremo ausente/mensaje de mes único por cambio de requisito. Probar nuevos extremos efectivos por moneda, doce posiciones intactas, cero/ausencia/negativos, uno/ninguno, grande exacto, errores interiores/exteriores y metadata inválida/partial; demostrar fallos reales antes de tocar producto.
- [x] 8.3 Green bajo tests fijos: seleccionar en O(N) costes exactos no cero, devolver meses efectivos/estado/límites a la página, etiquetarlos sin confundir rango elegido; conservar toda serie, total/desglose, cohortes y tabla. Ejecutar tests afectados y suite frontend/tipos/lint/build según matriz.
- [x] 8.4 Mutación manual autorizada en copia: cero incluido, negativo excluido, selección por valor gráfico, extremo equivocado, etiqueta de rango, uno/ninguno y errores saltados/silenciados. Clasificar sin cobertura exhaustiva inventada ni instalación.
- [x] 8.5 Despacho documental/datos separado: actualizar mínimo README/instrucciones y solo esperados comparativos del plan EURv2 en nueva referencia, sin cambiar sus filas/totales/monedas/tenants ni sobrescribir originales; preparar DB únicamente bajo despacho autorizado.
- [x] 8.6 Tras integrar disposición/comparación/docs/dataset, Revisor y Validador independientes comprueban entrega consolidada con referencia/revisión identificadas; evidencia de meses efectivos/rango completo, un caso error/límite, monedas/aislamiento y doce puntos. Conservar pendientes de Layout/proxy/casos no validados y gates humanos posteriores.


## Consolidación de cierre local — 06/10/2026

[Revisión](review.md) y [evidencia actual](../../../../docs/evidence/JUP-055-validation.md).
Tareas 3.4/5.3/7.6/8.6 mantienen un límite de responsive global: RF-026-002,
overflow compartido reproducido a 390×844. Revisión integrada PASS y ejecución
funcional independiente completadas; no se declara PASS visual ni aceptación
humana del límite. 5.4 conserva pendiente la aprobación postvalidación.
Matriz general: 1601 superadas, 85 skips nativos explícitos; test/lint/typecheck globales
ejecutados realmente mediante Turbo sin caché, todos con exit 0. El proxy aprobado
y la fila temporal sin fecha ya se probaron; la fila se retiró con snapshots
antes/después idénticos. Las tareas 6 siguen pendientes sin autorización de
archive/PR/reviews/merge otorgada en esta fase.

## Decisión humana postvalidación — 06/10/2026

Paris aprobó el cierre local con el límite RF-026-002 y autorizó el archivado.
Las tareas locales se cierran con esa disposición expresa y las limitaciones
registradas, sin afirmar PASS visual global ni ejecución de 85 skips. Se
conservan pendientes las tareas de PR, participación humana e integración.

Archivado realizado el 06/10/2026 mediante el comando nativo; 6.2–6.4 siguen pendientes. No se solicita ninguna review humana ni se publica una PR en esta acción.
