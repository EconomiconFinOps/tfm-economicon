# JUP-139 · evolución a cinco secciones —23/10/2026

## Cierre local aprobado y archivo — 24/10/2026

Rama `feat/JUP-139-grafana-five-sections`; base y develop oficial
`93624f77b2481d64ba40e95f211a9e53451f9e0e`. Coordinación confirmó el
24/10/2026 la identidad exacta: no se ejecutó fetch, merge ni escritura Git.
El cierre sólo afecta al archivo y su documentación; dashboard, pruebas, datos,
loader, Compose, dependencias y los tres UID conservan los bytes aprobados R8.

Revisión técnica independiente R8 favorable: 23 comprobaciones propias PASS, sin
omisiones; validación funcional independiente R8 favorable: 21 PASS, sin
omisiones, recorrido de 12 conjuntos y 15 capturas propias. No se suman como
casos distintos con los 41 del autor. Los originales completos se conservan
externamente: técnico SHA256 `3ca38970c290c17f9039878bffeccb19c52d0183087a3c4a9a3d8a7175e8d610`
y funcional SHA256 `0de33be5280a4154c86b7b6d3831e1498a40dc15449e6996820f03756c4148b4`.
La coordinación cotejó 2547 fuentes y 240 evidencias, mismas referencias
originales, sin discrepancias ni violaciones; inspeccionó 32 capturas y Grafana.

Se conservan 99 identificadores anteriores y 38 incorporados, 1688 observaciones
de 19 ejecuciones, señales y alertas. Esta cobertura no replica toda la auditoría
del dashboard anterior: versión de batería, commit, proveedor/cuantización,
indicador de hito y calibración elegida siguen en la base y vista original.
Ningún dashboard se retira. No nuevas campañas, modelos, recargas o gasto.

### Aprobación humana posterior a revisión y validación

- Decisión: Paris Arcos aprueba expresamente la entrega local R8 y autoriza
  reconciliación, archivo nativo en la misma rama y evaluación independiente del
  delta de archivo/base/documentación.
- Registro confirmado: 24/10/2026 a las 00:52:00 Atlantic/Canary
  (23/10/2026 23:52:00 UTC), conservado por coordinación.
- Candidato aprobado: manifiesto R8
  `c45cd8b95cce7f0fd7b1f40a7845ff04bfcbb8814af1cdd6e68bfef16d8ffd96`;
  entrega `19d3f7747a4dbdffb68cd2b207d8546e6e511fb4fde61f889880dd0e862b8c09`.
- Límites: mostrar cierre y título/descripción completos de PR antes de publicar.
  No commit, push, PR, merge, despliegue o retirada autorizados en este paso.

Archivo nativo ejecutado el 24/10/2026 en esta misma rama, con validación
activada y promoción de cinco requisitos añadidos y uno modificado. Se conserva
el DoD del change activo anterior al archivo y se comprueban promoción y enlaces. El
candidato final de archivo requiere nuevas referencias originales y evaluación
independiente del delta, con ratificación de lo no afectado R8. Esto no atribuye
anticipadamente sus dictámenes ni una nueva ejecución de suites de aplicaciones.

Roles humanos: Paris liderazgo, Alejandro pairing, Lucía revisión y Víctor
validación; asignación no acredita participación. Proceso CONTRIBUTING
18/10/2026, sin excepción PR135. Pairing previo acreditado, commit/push, CI,
publicación de PR y reviews humanas siguen pendientes de sus etapas. Las reviews
`Revision JUP-139` y `Validacion JUP-139` no se sustituyen por comprobaciones locales.

## Historial R1–R8 conservado; los pendientes anteriores corresponden a su corte

[Cambio archivado](../../openspec/changes/archive/2026-10-24-jup-139-grafana-five-sections/proposal.md) · [Matriz](../evidence/JUP-139-validation.md).


## Implementación del diseño visual v6 aprobado — 24/10/2026

Paris aprueba v6/versión temporal 12 el 23/10/2026 y autoriza implementarla sobre
la base estable `93624f77b2481d64ba40e95f211a9e53451f9e0e`. El dashboard de producto
conserva su UID y ambos dashboards anteriores. El prototipo aprobado y los
originales R1–R7 permanecen aparte, sin sustitución. No hay nueva campaña, carga
de GENERAL, modelo, gasto ni Git de escritura por esta implementación.

Cinco secciones desplegadas, tarjetas compactas, matrices de repeticiones, hitos
humanos y comparación Antes/Ahora/Diferencia. Las barras muestran mediana/p95 en
segundos por cohorte y población; p95 explica definición y base. Los 310 registros
automáticos, 28 humanos y 24 de latencia pasan a sus tablas completas, con sus
identidades y originales de tiempo/valor conservados ocultos. Las cinco
configuraciones conservan cada tipo y fecha originales. Diagnóstico mantiene las
1688 observaciones de 19 ejecuciones; no se convierte ausencia en cero o juicio IA
en participación humana. Las señales temporales permanecen accesibles en Salud.

Las opciones de detalle mantienen columnas, unidades, estados, bases e intervalos;
Indicador/Valor/Base quedan próximos con anchos fijos y un inspector nativo para
el texto extenso. Campaña y Lectura no quedan fijadas a las selecciones de la
demostración; Referencia empieza sin pareja. La nota de Salud explica el contrato
en vivo, sin congelar como hecho global el diagnóstico temporal de la propuesta.

Comprobación propia afectada: 41 casos distintos favorables (estructura 9, de
ellos ocho en el primer intento y uno tras aclarar la ayuda; SQL 17; integración
de datos 10; estados de recuperación con promtool 5). Se conservan el primer fallo
de la ayuda y su reensayo. Dos regresiones negativas rechazan el JSON R7 inmutable
con 2 FAIL/0 ERROR; el candidato nunca se restaura. El primer intento del runner
negativo no pudo cambiar de directorio por permisos y se conserva como entorno,
no defecto del producto. PostgreSQL de pruebas propio se retira; GENERAL conserva
sus datos. No se declara una suite workspace completa nueva ni se convierten las
omisiones históricas en PASS.

Este delta requiere revisión técnica y validación funcional independientes sobre
su manifiesto fijo y nuevas referencias originales PM. Los informes completos,
cobertura reutilizada/focal, límites y capturas se acompañan en la entrega; los
dictámenes R7 no se extienden automáticamente. La aprobación visual v6 no es
aprobación final de producto. Paris recibe resultados y capturas antes de subir
nada; archivo, commit/push/PR/CI y reviews humanas conservan sus etapas. Ninguna
retirada de dashboards está autorizada.

## Historial R1–R7 conservado; no dictamen del delta v6

## Cierre local: corrección y evaluación afectada — 23/10/2026

Revisión técnica y validación funcional independientes R6 favorables. R5-01/F1 queda resuelto: las cinco anotaciones conservan fecha, tipos originales de cambio y tags, origen público y advertencia de no causalidad; se observaron los tooltips reales en las tres evoluciones. Cada evaluador ejecutó únicamente la nueva regresión afectada (1PASS/0SKIP cada uno) y ratificó expresamente la evidencia R5 no modificada. El principal conserva su positivo y el control negativo sensible contra R5, ambos con recursos retirados; no se recargaron datos ni se repitieron suites generales. Los informes desfavorables R5 y todos los intentos originales permanecen intactos.

PM verificó el retorno contra las mismas referencias originales R6 antes de este cierre documental. Los bytes evaluados R6 y sus huellas se conservan aparte. El cierre sólo actualiza documentación y tareas; la aplicabilidad al manifiesto final requiere confirmación independiente, registrada en las adendas externas de cada rol. La evidencia de aplicaciones se reutiliza por identidad y ratificación, incluidos backend2732PASS/369SKIP y sus límites; no se declara una suite workspace completa nueva.

La entrega local queda preparada para mostrar resultados y capturas a Paris. Aprobación final humana, archivo autorizado, commit/push/PR/CI y revisiones humanas mantienen sus etapas. Los tres dashboards permanecen disponibles; ninguna retirada o publicación está autorizada por este cierre.

## Corte de preparación de la corrección local R6 — 23/10/2026

Los originales R5 técnicos y funcionales son desfavorables por el mismo hallazgo: se mantuvo la fecha de configuración pero se suprimieron los tipos de cambio. Se conservan íntegros con sus huellas; PM verificó el retorno contra las mismas dos guardas, sin discrepancias. La corrección R6 recupera annotation y changes existentes en texto/tags, con origen público y advertencia de no causalidad, sin modificar vista, loader o datos. Una regresión PostgreSQL comprueba las cinco fechas, cada lista de cambios distinta y ausencia sin anotaciones inventadas:1PASS/0SKIP. Contra el JSON R5 inmutable falla el mismo caso en sus cinco subcasos, sin errores; no se restaura el candidato. Ambos recursos temporales se retiraron. Se solicita evaluación independiente exclusivamente afectada y ratificación expresa de lo no modificado; este apartado no anticipa su dictamen ni una aprobación humana.

## Estado vigente: adaptación PR156 y reconciliación PR158 — 23/10/2026

Base de trabajo 93624f77b2481d64ba40e95f211a9e53451f9e0e, incorporada por PM con autorización humana expresa; rama feat/JUP-139-grafana-five-sections y cambios locales sin commit. Este apartado sustituye para el corte actual las cifras y pendientes de adaptación de los cortes R1–R4 conservados debajo. Sus dictámenes favorables no se trasladan automáticamente a esta base.

La carga nativa propia pasa de13/665 a19ejecuciones/1688resultados: manifiesto actual18/1670 más suplemento histórico1/18. Instantánea JSON y volcado SQL recuperable anteriores conservados; prueba de transacción abortada sin cambio de contenido;13ejecuciones/665filas históricas idénticas y todos los campos de19/1688 conciliados sin discrepancias. PR158 no cambia manifiesto, seis rows ni loader: no se repite la carga. Ninguna llamada nueva a modelos, campaña, importación financiera o gasto.

La composición conserva los tres UID y cinco secciones. Lectura de casos distingue instrumento original y juez IA provisional; la selección más reciente de robustez muestra7favorables/21fallidos/1sin evaluar de29, frente a0/8/21 del instrumento, y28/29operaciones completadas. No son medidas intercambiables. Cobertura separa28/29previstas,28/28disponibles y144/144criterios; humano permanece No medido. La metadata identifica repetición1/2/3de3 y conserva que el modelo no está atestiguado.

Las tablas incorporan coste/operaciones del gateway y latencias sin cambiar la factura histórica75consultas, modelos84/modelo o negocio sintético. Tiempos separados por todas las operaciones terminales, sólo completadas y etapa total histórica; sin inferir tiempos de generación o HTTP ausentes. Los originales internos se conservan ocultos en Diagnóstico/comparación, con etiquetas públicas traducidas.196puntos automáticos históricos se conservan: ahora310automáticos,28humanos registrados sólo hitos y24latencia. Las repeticiones nuevas forman dos cohortes de tres; no unen ensayos históricos por declarar el mismo modelo.

Pruebas propias: primera familia1995ejecutadas con69entradas de fallo y29de error, incluyendo subtests y preparaciones, conservada íntegra. Los fallos de expectativas/fixtures se resuelven incorporando PR158: histórico explícito12informes y cobertura separada del manifiesto completo. La preparación de permisos fallaba por recuentos16/14obsoletos frente22/20, no demuestra un defecto ACL. Reintento exclusivamente afectado:136PASS/0FAIL/0ERROR/0SKIP, incluidos8tests nuevos158,12regresiones139 y clases bloqueadas;1contrato adicional de metadata PASS.25tests offline de controlador/readinessPASS. Todos los PostgreSQL temporales propios y sus volúmenes retirados.

Control negativo: se conserva el primer intento contra R4 con subtests fallidos y un acceso a una columna antigua ausente. Un segundo control acotado de dos contratos rechaza R4 con2FAIL/0ERROR; referencia R4 inmutable y candidato nunca restaurado. No es un resultado desfavorable del candidato actual.

46consultas SQL iniciales correctas y sin identificadores internos visibles; se reutilizan por identidad de consulta salvo la metadata301, verificada de nuevo. Integración nativa Grafana posterior:12consultas focales correctas (8paneles/4variables), tres UID y JSON iguales por campo a sus fuentes. Interacción real comprueba IA/instrumento, cobertura, humano ausente y poblaciones de latencia. Las capturas y registros originales se custodian fuera del producto en adaptacion-PR156-20261023/entrega-t800.

Obligaciones locales jup:check:all, pr:check:test, ci:check:test, repository:governance:test, OpenSpec estricto, higiene y build:exit0. Build5/5,4tareas de caché y1ejecutada; no se declara compilación limpia de todo. Las suites de aplicaciones del corte anterior se reutilizan sólo mediante contraste de identidad de fuentes/configuración/locks; backend2732PASS/369SKIP,frontend1427PASS,processor2674PASS/150SKIP,Azure81PASS ylandingexit0. Se preservan los intentos y omisiones originales; no hay nuevo pnpm test completo verde ni se atribuye al candidato el1998PASS ajeno de PR158.

Pendiente de este corte R6: nuevas referencias originales PM, reevaluación técnica/funcional del contenido de anotaciones y ratificación de lo no afectado. Los originales R5 desfavorables quedan conservados. Después, mostrar resultados/capturas a Paris y obtener aprobación final. Archivo autorizado, commit/push/PR/CI y reviews humanas conservan sus etapas. No se retiran dashboards ni se publica por esta autorización.

## Historial anterior preservado


Paris aprueba la propuesta v4 y autoriza implementación local, dos evaluaciones independientes y tres evoluciones adicionales (automáticas/juicio registrado sólo hitos en Calidad; latencia de campaña en Coste). Base84b53b74. Dashboard/tests/guía/OpenSpec afectados; fuentes y manifiestos intactos. Se conservan los tres UID y los originales v4. Compose general propio construido y servicios sanos tras ajustes del runtime aislado;13/665 cargados con el loader actual. [Guía](../validation/grafana-five-sections.md) y [matriz](../evidence/JUP-139-validation.md).

Implementación y ampliación de puntos terminadas: familia1998PASS,30casos de composición cubiertos mediante originales y reensayos afectados;Compose general/tresUID conformes,datos13/665 conciliados sin discrepancias. Backend2732PASS/369SKIP compuesto,frontend1427PASS y processor2674PASS/150SKIP,sin repetir suites completas ni convertir omisiones enPASS. Capturas reales:196/28/6puntos,sin unir cohortes. Originales R1/R2 desfavorables conservados y defectos corregidos. Revisión técnica y validación funcional locales R3 favorables; cierre documental posterior sujeto a adendas de aplicabilidad. Mostrar resultados a Paris antes de subir nada. Sin archivo,Git de escritura,publicación o eliminación de dashboards. Actualización de originales de robustez del 22 oct y campañas nuevas diferida; JUP136 y vídeo siguen detenidos. Los cortes siguientes son históricos.

## Estado local tras la reevaluación R3 — 23/10/2026

Revisor independiente: **REVIEW_PASS R3**; Validador independiente: **VALIDATION_PASS funcional local R3**. Ambos informes originales se leyeron completos. R1 y R2 fueron desfavorables y se conservan íntegros: no se sustituyen ni se convierten sus fallos en PASS. Las correcciones R2 resolvieron ayudas, referencia pública y origen del juicio; R3 resuelve las dos definiciones restantes. Recuperación sin uso se calcula sobre muestras con recuperación no vacía, excluyendo recuperaciones vacías; permite citas ajenas al contexto sin uso válido de sus fragmentos. El volumen de ingestas cuenta trabajos creados/encolados por backend tras publicación confirmada, no consumo ni finalización por processor.

R3 cambia sólo esas dos ayudas y su contrato de prueba. El principal, Revisor y Validador ejecutaron cada uno dos contratos focales PASS. El control negativo del principal rechaza exactamente los dos casos sobre el JSON R2 conservado, sin restaurar el candidato; los evaluadores distinguen esa evidencia reutilizada de sus ejecuciones propias. Validador comprobó ambas ayudas en Grafana real y tres UID exactos, con cero consultas de paneles nuevas. Revisor ratifica 82 casos únicos R1 y siete R2 no afectados; Validador ratifica sus 30 casos R1, cuatro R2 y un borde del instrumento, junto con consultas/fixtures previos por identidad. No se repitieron suites completas, campañas, fixtures o SQL intactos.

El manifiesto R3 identifica 2.496 fuentes, SHA256 68b97736650a77c51267ac368fc396ed41844a603e54cc8d86234af0ecd48101; dashboard SHA256 18bdfd93b5ed8708e5d53c0b80523bace9be6ea712a7d994d0d383d73f938cf7. Original técnico SHA256 11ee4e98579830e4a0839a02ec877803fc40fdcf190b07c1a915d26ac02768a4; funcional SHA256 6b27fca2a7470e7a802402b139c528b35263c78271537cbfb4ccbf5e84c12c30. Los bytes modificados son de trabajo sin commit, no del SHA base. Informes, capturas y referencias de integridad se custodian fuera del producto. Este cierre posterior modifica sólo documentación y requiere su propio manifiesto, referencias PM y adendas de aplicabilidad de los mismos evaluadores; no se anticipan aquí esos dictámenes.

PM verificó al retorno las mismas dos referencias ORIGINALES R3 a17:21:43UTC: ambas ok:true y cero violaciones; cotejó las 2.496 fuentes sin discrepancias. Las referencias no se sustituyeron ni se restauraron para PASS.

La carga sigue siendo 13 ejecuciones/665 resultados y las observaciones reales 196/28/6; los datos/SQL/series y los tres UID siguen intactos. Validador retiró sus 12 contenedores, seis volúmenes y dos redes, con ausencia verificada. El Compose general del principal se conserva para mostrar resultados a Paris. Aprobación final, archivo autorizado, commit/push/PR/CI y reviews humanas separadas mantienen sus etapas posteriores. Los dictámenes locales no acreditan esas acciones ni autorizan retirar dashboards o hacer merge.

## Corte histórico de preparación R2 tras los originales R1 — 23/10/2026

Los dos informes originales se conservan: revisión técnica REVIEW_FAIL por dos grupos de ayudas incorrectas (22 paneles), y validación VALIDATION_FAIL por ayudas ajenas e identificador de caso visible en Diagnóstico. PM comprobó al retorno las mismas dos referencias originales, sin violaciones ni sustitución; también cotejó los 43 payloads de evaluación. Esto acredita integridad, no aceptación de los defectos.

El principal revisó las ayudas de los 50 paneles y las ajustó a medida, fuente, población y límites. La factura corresponde a 75 consultas del 21–22 oct; cobertura 75/75 y tasas de errores sobre 124 llamadas o intentos, 0/124. Diagnóstico conserva la variante original en un campo interno excluido; la referencia se presenta como «Referencia interna del informe». El origen del juicio diferencia humano registrado, automático registrado y no registrado, sin acreditar participación adicional. Sólo cambian dos consultas de presentación, ayudas, anchos de columnas y las pruebas/documentación afectadas. Datos, cálculo, series, tres UID y base permanecen intactos.

Seis comprobaciones focales propias PASS, incluidas tres regresiones nuevas; las tres rechazan el JSON original R1 exacto, conservado por SHA256, sin modificar el candidato para ese contraste. Grafana real confirma las dos consultas afectadas sin error; las otras consultas conservan su evidencia por identidad. No se repiten suites completas. Nuevas capturas nativas comprueban ayudas, factura, juicios y diagnóstico. Al fijar este corte R2, su revisión y validación afectadas requieren las nuevas referencias originales PM; no se extiende un dictamen anterior.

La actualización diferida es la de los originales de robustez del 22 oct y campañas posteriores, no la eliminación de las ejecuciones ya incluidas: el Banco del 22 oct y la factura del 21–22 oct ya forman parte de los 13/665 conservados. Sin nuevas campañas, llamadas, gasto o actualización de datos.

# Composición narrativa de evaluación — JUP-129

Actualización documental: 22/10/2026. [Tarjeta](https://trello.com/c/07J4M5ZN). [Diseño y tareas](../../openspec/changes/archive/2026-10-22-jup-129-grafana-evaluation-composition/design.md). Rama `feat/JUP-129-grafana-evaluation-composition`. Los apartados históricos conservan sus candidatos y resultados.

## Estado vigente: cierre y archivo autorizado — 22/10/2026

PM confirmó íntegros los originales R4 y cerró su merge en `07ef55580c100885ffc8075e82fb7b2eb0011ce3`, con 2.290 fuentes cotejadas y sólo 14 normalizaciones LF autorizadas. Revisor R4 **REVIEW_PASS** (tres pruebas focales propias PASS); Validador R4 **VALIDATION_PASS técnico focal**, por contraste propio de Compose y entradas. Ratifican R3/R2 con sus límites. Sus informes originales no equivalen a reviews humanas ni se extienden automáticamente al siguiente candidato.

Paris autoriza completar la integración y archivar el cambio. PM incorpora `develop` `c00063dbaa83a1237431edef9de6d71d1bfd1ffd` sin commit y sin conflictos: siete rutas, seis documentales y un archivo con cinco pruebas nuevas de indicadores. Se conservan las aclaraciones de rúbrica mixta/normalización de citas y la vigencia histórica de los ADR; no cambian dashboards, loader, datasets, métricas, Compose o provisioning. Las cinco pruebas nuevas pasan en 0,77 s; no se repiten suites completas, consultas o campañas.

El manifiesto normal sigue **9/444**; modelos es suplemento histórico opcional **18 filas → 10/462**. Las 14 capturas/11 vistas entregadas a PM conservan su fecha y procedencia. Ninguna medida histórica se atribuye al modelo nuevo. El arranque completo backend/processor v4 queda fuera de lo demostrado por la ratificación de composición.

La lectura externa humana sigue **NOT_VALIDATED**. La especificación permite declararla pendiente; la tarea de registrar esa declaración se completa, sin afirmar que se hizo la lectura. Se conserva el guion en la matriz. Omisiones reales: 368 backend y 144 processor; marcador histórico backend ausente no recuperado, cobertura actual compuesta 2.577 PASS/368 SKIP. No se declara todo el workspace verde.

El CLI existente archivó el cambio el 22/10/2026 y promovió sus cuatro requisitos a `openspec/specs/assistant-evaluation-composition/spec.md`, sin saltarse validación o promoción. Se fija el candidato tras comprobaciones documentales para nuevas referencias PM. Revisor/Validador ratificarán sólo delta y archivo. Commit/push, CI y texto PR previo a abrirla corresponden a PM; el archivo no acredita aceptación humana ni autoriza merge. Los cortes siguientes son históricos y no sustituyen este estado.

## Integración anterior de ee84 — 21/10/2026 (R4)

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
