# Composición narrativa de evaluación — JUP-129

Actualización documental: 21/10/2026. [Tarjeta](https://trello.com/c/07J4M5ZN). [Diseño y tareas](../../openspec/changes/jup-129-grafana-evaluation-composition/design.md). Implementación local en `feat/JUP-129-grafana-evaluation-composition`, base `bc94a4daea98e97b574d00f019d347fc61c2f915`; sin commit ni publicación.

## Estado vigente: integración de ee84 — 21/10/2026 (R4)

PM cierra el candidato R3 evaluado en `bd134a31`, padres a542/b7c8 y árbol c10f273a,2271blobs cotejados. Revisor R3 favorable con53 pruebas focales; Validador R3 favorable con carga9/444,28consultas y tres vistas, conservando la lectura humana NOT_VALIDATED. Sus originales y controles quedan custodiados.

Tras integrarse el modelo único en develop `ee84f791`, Paris autoriza reconciliar esta base. Se integra sin commit: un único conflicto de índice de continuidad, resuelto conservando las entradas de ambas historias. No cambia la composición, loader, manifiesto, métricas o provisioning. Los objetos completos Compose Grafana/Prometheus/PostgreSQL y sus recursos compartidos son idénticos. Su clausura de arranque incluye backend/processor, cuyas rutas de recursos v4 sí cambian; la evaluación R4 cubre ese impacto sin repetir campañas o baterías intactas. No se incorporan las PR147/149 todavía abiertas.

El default sigue9/444; el suplemento histórico de modelos18filas permanece opcional. A petición de Paris se cargó fuera del producto con el loader existente (10/462), se cotejaron18filas/metadatos exactos y se capturaron todas las secciones con modelos poblados. Las14capturas/11vistas, procedencia y retirada se conservaron fuera de Git y entregaron a PM; no se añadieron al manifiesto de producto. Cohorte16/10,84respuestas/modelo, valoración provisional; separada de robustez y comparativa posterior. No nuevas llamadas o juicios.

Al fijar esta documentación, revisión/validación afectadas R4 requieren sus nuevas referencias PM. Se conserva la evidencia técnica previa por identidad y límites, sin extender dictámenes unilateralmente. Lectura humana, aprobación final, archivo y publicación conservan sus etapas. No hay commit/push/PR del nuevo merge por el implementador.

## Reconciliación previa R3 con develop — 21/10/2026


El candidato remoto comunicado por PM es `a542e8cb`, sobre `bc94a4da`. Paris autoriza incorporar exclusivamente `develop` `b7c8b708`; el merge local sin commit termina sin conflictos. No se incorpora la rama independiente de cambio de modelo. Los apartados siguientes conservan los cortes históricos anteriores.

El manifiesto integrado incorpora robustez: **9 ejecuciones/444 filas**. La nueva composición y el provisioning no requieren cambios de producto: la portada elige la campaña experimental más reciente y conserva 7/29 favorables, 17/29 fallidos, 5/29 sin medir y 24/29 puntuables, con modelo sin verificar. El suplemento de modelos sigue fuera del default; sin él el XY indica «Sin datos».

Pruebas propias del delta: **266 PASS** de composición, manifiesto, carga, conciliación e indicadores; no suite completa. Grafana 11.3.0 real del Compose general aprovisiona los tres UID y **28 consultas** de la composición/selectores devuelven 200 con la carga 9/444. Capturas nuevas en la matriz de evidencia. Las correcciones anteriores 110/322/903/114 se conservan; no cambian dependencias, servicios ni modelos.

R2 original terminó con revisión técnica (10 PASS) y validación focal (9 PASS y 15 consultas) favorables, custodiadas por PM. No se extienden automáticamente al nuevo candidato: revisión y validación afectadas de la reconciliación pendientes al fijar esta documentación. Lectura humana NOT_VALIDATED; omisiones e históricos conservados. PM conserva aprobación final, archivo, commit, push, PR y publicación.

## Cortes históricos conservados

Paris aprobó composición y lenguaje funcional y autorizó implementar con evaluación independiente antes de subir. La entrada nueva `economicon-assistant-evidence` selecciona señales de los dos dashboards previos; sus UID y archivos se conservan para no romper consumidores, auditoría o contratos. [Guía](../validation/evaluation-dashboard.md) y [matriz de evidencia](../evidence/JUP-129-validation.md).

No se cambia loader, datos, permisos, provisioning, backend, frontend o dependencias de producción. La base tiene 8 ejecuciones/308 filas y no incluye la campaña experimental ni el suplemento de modelos. Se prueba además una proyección experimental separada de 10/462, sin introducir esos datos en el manifiesto versionado ni incorporar producto de PR144. Cero llamadas a modelos o campañas nuevas.

El selector describe lo cargado; cifras dinámicas, ausencias nulas y cero sólo cuando se midió. Cada agregado histórico se fija a una identidad. Las cuatro familias se explican con sus límites; conversación es un proxy, no usuarios reales. La comparación exige referencia distinta y anterior, misma fuente y clave de comparabilidad; sin pareja compatible no se declara mejora. El detalle sólo describe cambios de medidas existentes, sin score compuesto o causalidad.

La matriz registra nueve capturas iniciales y dos del Compose general, 14 pruebas focales PostgreSQL PASS y 25 consultas por proyección conciliadas. Build, políticas, OpenSpec e higiene pasan; la regresión Linux conserva los fallos originales; una corrección focal posterior acredita cuatro tests promtool PASS y 54 casos backend PASS con registro individual. Processor tiene cuatro fallos originales de extracción y una reevaluación focal posterior con cuatro PASS; no se declara el workspace íntegramente verde. Recursos temporales se inventarían fuera del producto, con bases aisladas, y se retiran o dejan en custodia para revisión. Las referencias originales y controles independientes corresponden al PM. Revisor y Validador distintos no sustituyen Alejandro y Víctor ni acreditan pairing de Lucía.

Próximo paso actual: fijar el candidato corregido para reevaluar únicamente los hallazgos de la primera revisión y validación, conservando sus informes originales. Prueba de lectura externa pendiente de respuestas reales, sin atribuirla a agentes. Archivado, Git, publicación y merge conservan permisos específicos; no se ejecutan por esta entrega local.

## Resultado de Linux y Compose general — 21/10/2026

Paris autorizó usar Ubuntu WSL2 e integración Docker existentes, con dependencias privadas, sin instalaciones globales ni cambios de host. Evaluación completa: 1.890 casos, cuatro FAIL promtool por acceso al temporal, cero SKIP. El discriminante UID/permisos se conserva sin sustituir los fallos originales ni modificar helpers.

Frontend: 1.380 PASS. Azure: 81 PASS. Processor: 2.599 PASS, cuatro FAIL y 144 SKIP; los mismos cuatro casos pasan después en la imagen Linux aislada que dispone de las herramientas en el PATH fijo del worker. Backend se retoma sólo en 51 casos no completados (10 PASS, 41 SKIP); total acreditado 2.576 PASS, 368 SKIP y un resultado anterior desconocido. No se repiten suites completas ni se atribuye PASS a ese resultado.

El Grafana del Compose general aprovisiona los tres UID originales/nuevo con las dos datasources existentes; sus JSON coinciden y 25 consultas SQL del nuevo funcionan mediante el lector configurado. La carga existente mantiene ocho ejecuciones/308 filas. No se añade importación manual, despliegue separado o carga automática de campañas. Capturas en la matriz de evidencia; recursos Compose y contenedor focal retirados con comprobación de ausencias.

Siguiente paso: fijar referencias originales del candidato corregido antes de evaluación independiente y realizar la lectura externa humana pendiente. Base estable bc94, sin integrar el avance posterior de develop durante estas pruebas. No hay archivo, commit o publicación.

## Corrección focal posterior — 21/10/2026

Con autorización expresa de Paris, se corrige únicamente la legibilidad del temporal sintético del test promtool y su montaje de sólo lectura. Los cuatro tests originales pasan con umask077, sin alterar sus expresiones o aserciones. No se repite la batería de evaluación completa.

El marcador histórico backend no se recupera; se acredita el estado actual mediante el archivo afectado de 54 casos, todos PASS con JUnit y cotejo individual. La reconciliación por nodeid con las ejecuciones preservadas acredita 2.577 PASS y 368 SKIP de 2.945, sin casos actuales desconocidos. No se modifica backend ni se repite su suite completa. Registros y manifiestos anteriores se conservan; las evaluaciones independientes y humanas siguen pendientes.

## Correcciones tras revisión y validación — 21/10/2026

La primera evaluación independiente detectó mezcla de ejecuciones en calibración y facturación, pérdida del cero medido en las dos tasas HTTP nuevas y «Err» en el XY sin suplemento. Los informes originales se conservan. Tras el control de retorno se corrigen los cuatro comportamientos sin cambiar base, datos, dashboards anteriores, Compose o provisioning.

Los agregados completos de los paneles 110/322 quedan acotados a sus informes. El panel 903 convierte en cero sólo el numerador ausente con tráfico, conservando ausencia sin tráfico. El XY mantiene columnas nulas tipadas, filtra coordenadas ausentes y rotula la disponibilidad del mismo informe. No añade métricas ni puntos artificiales.

Ocho regresiones focales pasan; contra el dashboard original detectan los defectos. Dos comprobaciones adicionales pasan para la etiqueta de disponibilidad y los selectores. Grafana 11.3.0 del Compose general muestra «Sin datos» con 8/308, dos puntos intactos con 10/462 y vuelve a «Sin datos» al recargar 8/308. Se retiraron tres contenedores, seis volúmenes, dos redes y credenciales propias. Capturas y detalle en la matriz.

Pendiente: nueva revisión y validación de lo afectado sobre candidato fijo; lectura externa humana; pasos finales del proceso. Se conservan 368 SKIP backend y 144 SKIP processor, los fallos históricos y su evidencia focal posterior. Sin nueva batería completa, aceptación humana ni publicación.
