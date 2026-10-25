# JUP-139 · evidencia de implementación local

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

## Criterios vigentes tras aprobación local R8

La evidencia de comportamiento se reutiliza por identidad; no son nuevas
ejecuciones sobre el archivo. El delta documental requiere evaluación separada.

| Criterio | Evidencia aplicable | Estado |
| --- | --- | --- |
| AC1 · inventario y medidas | 99 identificadores anteriores y 38 incorporados, 1688 observaciones/19 ejecuciones; mapa y diagnóstico conciliados en R8. | Favorable local R8; datos intactos. |
| AC2 · propuesta aprobada | Diseño v6/version12 aprobado antes de implementar el 23/10. | Hecho humano confirmado. |
| AC3 · cinco secciones y lenguaje | Recorrido nativo R8, 16 capturas normales y 16 amplias; estructura y detalle legibles. | Favorable local R8; JSON intacto. |
| AC4 · robustez y límites | Matrices IA/reglas separadas, hitos provisionales; citas estructurales no equivalen a calidad semántica. | Favorable local R8. |
| AC5 · datos existentes | Loader/manifiestos/datos sin cambios, GENERAL19/1688 sin recarga; ninguna nueva campaña. | Favorable local R8. |
| AC6 · origen, filtros y poblaciones | Compatibilidad/ausencia de pareja, referencias fijas, poblaciones terminal/completadas/histórica separadas. | Favorable local R8. |
| AC7 · ausencia, cero y trazabilidad | Cinco estados promtool, 12 conjuntos, fechas/tipos/base/unidad/intervalo y originales conservados. No equivalencia de toda la auditoría anterior. | Favorable local R8. |
| AC8 · provisioning y tres dashboards | Arranque GENERAL anterior ratificado, exportaciones de tres UID exactas; Compose y dependencias intactos. | Favorable local R8 con reutilización explícita. |
| AC9 · comprobaciones y documentos | 41 casos distintos del autor, 23 técnicos y 21 funcionales propios solapados; originales/fallos/omisiones conservados. | R8 favorable; evaluación documental posterior separada. |
| AC10 · proceso | Aprobación local final y archivo nativo autorizados y realizados el 24/10; no commit/push/CI/PR/reviews humanas/merge. | Cumplimiento parcial por etapa, publicación no validada. |

## Historial R1–R8 conservado; los pendientes anteriores corresponden a su corte

[Cambio archivado](../../openspec/changes/archive/2026-10-24-jup-139-grafana-five-sections/proposal.md) · [Guía](../validation/grafana-five-sections.md).


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


Cierre documental local del23/10/2026 tras los originales independientes R3 favorables. Candidato de trabajo feat/JUP-139-grafana-five-sections sobre84b53b74d02ff5831ef9dbdd4f9c7d8c40cd4d24. Ejecución automatizada documentada. Roles oficiales comunicados por PM:Paris liderazgo,Alejandro pairing,Lucía revisión,Víctor validación; asignación no acredita participación. Proceso18/10/2026; excepción PR135 no aplicable.

Paris aprobó la propuesta visual v4 antes de modificar el JSON versionado,autorizó implementar/evaluar y amplió el alcance a tres evoluciones y a puntos aislados con líneas sólo comparables. Original v4 conservado:128 payloads,manifiesto SHA25675005182425a3201206fcbcb415643a7c04c292e702ebf0739b8294f79ffdc80. Nuevos originales,fuentes,manifiestos,capturas e informes se custodian fuera del producto en entrega-implementacion-t800 del encargo PM.

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

## Criterios y evidencia propia

| Criterio | Resultado observado y límite |
| --- | --- |
| AC1 | Inventario de665 filas:fuente,informe/huella,ejecución,fecha,modelo declarado,definición,valor,unidad,estado,base,intervalo,juicio y panel.50 paneles de contenido en cinco secciones;sin nuevas métricas,puntuaciones ni umbrales. |
| AC2 |20 capturas v4 mostradas y aprobadas antes de implementación. Se conservan sin sustitución;capturas nuevas del Compose general y de las tres evoluciones. |
| AC3 |Cinco secciones,máximo cuatro tarjetas por bloque,anillo,barras,matriz,puntos,tablas y series. Textos completos comprobados en navegador1280;diagnóstico/operación plegados. |
| AC4 |18 indicadores/19 filas de robustez disponibles;estados,bases y límites separados. Citas válidas/literales no se presentan como calidad semántica. Regresión que permite citas4/4 con casos0/4 favorable. |
| AC5 |Cargador actual con12/647versionados y suplemento histórico opcional1/18:13 ejecuciones/665 filas. Cotejo campo a campo usando mapas del loader:0 discrepancias. Sin cambios de manifiestos,informes,loader o evaluación;actualización de originales de robustez del 22 oct diferida; el Banco del 22 oct ya está cargado. |
| AC6 |Campaña/referencia sólo gobiernan consultas declaradas;referencias fijas,cohortes de modelos16Oct,factura21–22Oct e histórico/operación separados. Selector dinámico,incluye campañas sin medidas. Modelos declarados y juicio registrado no acreditan verificación/participación adicional. |
| AC7 y ampliaciones |Fecha UTC completa,ejecución inequívoca con ID oculto,unidad,estado,base,intervalo y juicio en detalle desplazable. Punto único visible;dos compatibles misma serie;dos incompatibles series separadas;fecha/valor ausentes sin posición inventada. Unidades,hitos y tipos de juicio comprobados. Catálogo de cohortes común a las tres gráficas. |
| AC8 |Compose GENERAL propio:backend,processor,frontend y dependencias sanos,migrador0. TresUID originales/nuevo aprovisionados e iguales por campo a los JSON.51consultas reales sin error;tras el ajuste se repiten sólo tres consultas cambiadas y la anotación(4),sin error. Sin dependencias de producción nuevas. |
| AC9 |Familia de evaluación1998 PASS antes del ajuste de puntos;delta cubierto por composición29 casos con26 PASS/3 FAIL originales y reevaluación de5 casos PASS. Catálogo común añade un caso y cuatro regresiones PASS. Estructura7 PASS. Políticas,OpenSpec,higiene,trazabilidad y build conformes. Los originales R3 posteriores son favorables en el ámbito técnico/funcional local; véase el estado vigente anterior. |
| AC10 |Sin archivo,commit,push,PR,publicación ni merge. Aprobación final y participación/reviews humanas pendientes;las comprobaciones locales no las sustituyen. |

## Tres evoluciones y datos realmente visibles
Se reutilizan definiciones/filtros/anotaciones de los paneles7/8/24 del dashboard anterior,que permanece intacto. Las nuevas consultas2101/2102/4101 leen evaluation.runs:la vista comparable_runs también eliminaba las observaciones aisladas y no se cambia. Identidad de serie:clave de comparabilidad,métrica,grupo,variante,unidad y tipo de juicio. Claves vacías/nulas aisladas por ejecución. Grafana muestra siempre puntos;particiona por identidad y sólo conecta dentro de cada serie,sin puentear nulos. Sin fecha o valor:detalle,sin punto ficticio.

La carga actual aporta196 observaciones automáticas,28 de juicio registrado sólo hitos y6 de latencia;cada serie tiene una observación,no hay líneas entre cohortes. Son los datos existentes,sin fixtures en las capturas de resultados. Los pares compatibles y los casos ausentes/incompatibles se verifican con fixtures SQL separados y ROLLBACK. Las anotaciones naranjas de configuración no se presentan como cambios causales. Ventana relativa propia30 d;Campaña/Referencia no filtran estas tres gráficas. Latencia de campaña en ms(se autoformatea en ms/s),separada de HTTP.

## Comprobaciones obligatorias y recuperación acotada

Políticas locales jup:check:all,pr:check:test,ci:check:test,repository:governance:test,openspec:validate y jup:cleanup:check:exit0. Tras el delta de especificación,se repiten sólo OpenSpec/trazabilidad:93 items válidos y exit0. Build workspace:5/5 tareas correctas,con avisos existentes de tamaño del bundle/salidas decompileall.

La única ejecución amplia efectiva de pnpm run test conserva su salida no favorable de entorno:backend2569 PASS/366 SKIP/64 FAIL/102 ERROR;frontend96 ficheros/1427 casos,25 fallidos;processor aborta colección por recurso generado ausente,ningún caso ejecutado;Azure81 PASS y tarea landingexit0. El runner privado no incluía tokenizadores generados/ignorados en el archivo de fuentes;se copiaron los artefactos ya verificados de las imágenes propias,sin cambiar fuentes,locks o tests.

Recuperación sin repetir suites completas:backend sólo166 nodeids fallidos/erróneos(--lf):163 PASS/3 SKIP;total compuesto2732 PASS/369 SKIP de3101,sin resultado desconocido. Frontend sólo los14 ficheros afectados con un worker y timeout original:148 PASS;los96 ficheros originales se concilian con el inventario,resultado actual1427 PASS. Processor primera ejecución efectiva tras resolver colección:2674 PASS/150 SKIP de2824,conJUnit. Los369/150 SKIP se conservan como omitidos,no superados. No se declara un nuevo pnpm test completo verde ni aceptación humana.

## Incidencias y originales
Se conservan:preparación de runner antes de arrancar pruebas(directorio,despacho pnpm y shim privado),primer error de generación de un test,expectativa de unidad corregida a usd y comprobación especial del listado nativo de alertas. Dos series de volumen necesitaban datasource y refId explícitos:corregidos y comprobados. Codificación implícita de un comparador y nombres commit/count frente a commit_sha/case_count produjeron discrepancias instrumentales;corregidos usando UTF-8 y mapas oficiales del loader;originales y cotejo0conservados.

Runtime general:base propia creada y dialecto corregido a cockroachdb+psycopg;sólo en configuración privada externa. Processor necesitó tmpfs propio /tmp:mode=1777 porque el montaje presentaba0700 al usuario10001. Primera carga psql sin usuario falló;argumentos del contrato -U postgres -d embeddings permiten13/665. Sin cambios de Compose del producto.

Se conserva la captura inicial aún cargando y las de textos cortados;las capturas finales corrigen legibilidad sin sustituir originales. Se mantienen las primeras consultas/capturas sin parejas y la reevaluación posterior de puntos aprobada por Paris. Se mantiene estable la base84b53b74;PM conserva los controles independientes originales y los verifica al retorno/prepublicación. Los recursos propios se inventarían con custodia/retirada fuera del producto;sin alterar 3000,AWS,recursos ajenos,vídeo o JUP136.
