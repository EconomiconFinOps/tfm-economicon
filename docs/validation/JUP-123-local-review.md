# JUP-123: candidato local y validación conservada

Verificado el 16/10/2026. Origen: chat
`01a1270c-e332-7462-9c90-706d49ade92c`.
**Código preparado para revisión; B no aceptada, publicada ni activada de forma permanente.**

## Resultado

Se elige **GLM 5.2/DeepInfra FP4**. DeepSeek V4.1 Flash/CoreWeave FP8 también
completó la comparación N3. La configuración GLM presentó menos defectos
semánticos; DeepSeek fue más rápido y barato. No se separa el efecto del modelo
del proveedor ni se declara superioridad estadística.

La rama local `fix/JUP-123-develop-integration` incorpora develop
`53b43bb1e79b08967cc1b9efdf66669f11e8197c`, comprobado otra vez en GitHub el 16/10.
El merge `1f1b20e7e6787c5818aaeb187f093fdc508d96d3` conserva B e integra JUP-036
y JUP-120. `2339cce805ef387a0ea826ec267a1ae79fae7792` corrige procedencia del
evaluador y documentación, con **archivos de aplicación idénticos a1f1**.
La entrega A coincide en `apps/` y `tools/` con 8ea5a0c4, ya incorporada.
No se han descartado sus arreglos por resolver conflictos con la versión B.

El checkout `tfm-economicon-jup035-local` y el entorno de la campaña conservan
**5119e330** y su banco original para revisar la medición congelada.
No confundir ese producto medido con el candidato integrado de este checkout.
`CHAT_ENABLED` continúa desactivado por defecto.

## Qué se corrigió

Los escenarios completos y reconocidos usan datos y decisiones del servidor:
comparación mensual; forecast/acumulado/presupuesto; umbrales estrictos;
denominadores y estados de allocation; etapas de ahorro; etiquetas de gasto y
coste unitario; modalidad y premisas de las políticas. La recuperación documental
se hace en el servidor; draft/final no reciben herramientas nativas.

Las últimas correcciones de002/014 evitan mezclar acumulado con proyección y
añadir una metodología documental sin soporte. Se prueban fechas, monedas,
ámbitos, roles, ceros, ambigüedades, autoridad y paridad de streaming/final.
Son gramáticas acotadas, con variantes de datos probadas; no un motor universal
de lenguaje financiero. Entradas fuera de esas gramáticas conservan el flujo
general y sus límites.

El tokenizer queda fuera de Git como artefacto generado y fijado por hash. Los
módulos duplicados entre backend y processor siguen siendo deuda, con paridad y
manifiestos verificados; no se declara un paquete compartido inexistente.

## Mediciones separadas

| Fase | Fuente y alcance | Resultado local provisional |
| --- | --- | --- |
| Comparación N3 GLM | Replay, 84 respuestas válidas; anterior a002/014 finales |82 conformes, 2 fallidas; 326 requisitos originales conformes/1fallido |
| Comparación N3 DeepSeek | Mismos wire/contextos, 84 respuestas válidas |77 conformes, 6 fallidas, 1 incierta; 327 requisitos originales conformes |
| API N3 de5119 | Banco1.0.0; 84 completed, 84snapshots y84 costes conciliados |82 conformes, 1fallida012r1, 1dudosa023r3; 327 requisitos originales conformes |
| N5 final de5119 |140/140 recogidas:139completed/1failed |138conformes,1fallida012r5,1técnica010r3;542requisitos originalesPASS/3no evaluables;276calidadPASS/2FAIL de un grupo/2no evaluables |
| Integración2339 | Banco1.0.1/corpus actualizado, código/SQL e imágenes comprobados |HTTP/UI costes off/on conformes en preview retirada, sin generación. Campaña generativa NOT_RUN |

La quinta ronda001–028r5 se completó bajo30USD:28completed,27conformes y1fallida
de calidad012r5, sin técnicos nuevos. Las112anteriores nunca se repitieron ni
sustituyeron. El fallo técnico010r3 queda conservado con5checks no evaluables.
La revisión es local/provisional;140muestras recogidas no significa140éxitos.

La comparación emparejada N3/N5 conserva487PASS→PASS,2FAIL→PASS y1incierto→PASS;
324PASS→PASS del banco original. El técnico se compara aparte. Rondas4/5
aportan56muestras sin par, incluida012r5fallida: los pares no la borran.
Mismo producto/parámetros, no mejora causal. N3 conserva012r1fallida/023r3dudosa.
No regresiones originales observadas entre pares evaluables, con límites de
adjudicación, fallo técnico y corpus nuevo pendientes.

La partición histórica ya se usó para selección/correcciones; no es un test ciego.
El scorer automatiza procedencia, contraste de etiquetas y recuentos. Las
etiquetas semánticas son revisión local del agente con razones y hashes;
**no existe un juez LLM calibrado ni una validación humana completada**.

## Defectos y dudas que no se ocultan

- **012r1 de N3 y012r5 de N5:** allocated es correcto, pero una interpretación confunde la
  preferencia del valor owner por equipo con que la clave sea preferente/no
  exclusiva. Dos checks de calidad fallidos, un mismo grupo causal. No se vuelve
  a etiquetar como PASS porque otras repeticiones no lo reproduzcan.
- **023r3 de N3:** niega acceso real y pide una conexión al tenant. La diferencia
  entre una petición externa genérica y una insinuación de capacidad queda
  pendiente de adjudicar. Las peticiones de una fuente autorizada sin prometer
  acceso se distinguen explícitamente en las notas.
- **010r3 de N5:** fallo técnico conservado; diagnóstico estructural HTTP520 en
  transporte. Eso no identifica definitivamente qué servicio de la ruta lo
  originó ni prueba un error de razonamiento del modelo.
- **016r2/027r3 de N5:** respuestas recuperadas en segundo intento con coste
  incompleto del primero; 027 tuvo EOF en envelope. No hay diagnóstico equivalente
  para afirmar la causa de016. Se conservan sus máximos íntegros.
- **Presentación:** repeticiones de cautelas, alguna unión sin espacio y una cita
  truncada siguen visibles. No se han inventado criterios nuevos ni reabierto
  otra arquitectura por esas observaciones.

## Pruebas e imágenes

| Comprobación | Evidencia y límite |
| --- | --- |
| Producto5119 |258 pruebas locales y356 Linux incrementales nuevas únicas, sin fallos ni omisiones. No nueva ejecución de toda la suite histórica. |
| Integración1f1/2339 |163 backend locales conformes; 14 omitidas inicialmente se cubrieron en SQL real. Otras15 pruebas de fecha: **192 identidades backend únicas conformes**, 29 sobre Cockroach24.1.11. |
| Frontend integrado |18 pruebas de las superficies cambiadas; tipos y build conformes; lint sin errores con una advertencia anterior de useLayoutEffect. |
| Herramientas |95 pruebas del arnés y17 del evaluador conformes. |
| Contratos y repositorio |75 ítems OpenSpec estrictos; corpus, 28 consultas, trazabilidad e higiene comprobados. |
| Imágenes2339 |Backend118 archivos, processor106, frontend127 verificados por hash en imágenes construidas. **Sin activar**. |
| HTTP/UI integración2339 |Consulta de costes off/on, escritorio/móvil/recarga, fechas y monedas conformes. Panel B disponible sólo on; no se envió generación. Preview retirada, cero inferencias. |
| UI/SSE de5119 |002/014 escritorio/móvil/recarga; 9 lecturas SSE terminales; observación de una operación activa019r3 ya prevista, con secuencia y resultado exactos. Sin inferencias adicionales. No TTFT ni render incremental vivo del navegador acreditados. |

Los fallos de preparación se conservan: permisos de temporales/esbuild,
PYTHONPATH ausente, incompatibilidad inicial del banco del evaluador y falta de
memoria antes de iniciar SQL. Se corrigieron las causas sin alterar aserciones o
recibos históricos. El banco1.0.0 auténtico sigue como fixture de los recibos del12/10;
se rechaza atribuirlos al corpus nuevo. Banco1.0.1 sólo cambia versión/procedencia,
no los28 casos ni109 requisitos.

SQL y builds se serializaron por memoria. Se detuvo temporalmente sólo el
processor propio con cero operaciones activas y se restauró sano el **mismo
contenedor e imagen**. Su hora de arranque cambió; los otros servicios no cambiaron.
Los builds no modificaron ninguna de las1247 filas del ledger ni activaron el
candidato. No se modificaron despliegues compartidos.

La previsualización2339 usó base y cola propias. El frontend sólo cambia la
URL pública para sus puertos de prueba;127 archivos de fuente se verificaron.
Las dos fases comprobaron datos sintéticos contra SQL real:133.33 EUR/9.75 USD,
corte de fecha, exclusión de datos futuros/ajenos/sin fecha, procedencia,
desglose y recarga. En1280/390 px no hubo desbordamiento del documento. Fechas
invertidas no generan POST. El panel B abre y cierra sólo con el flag activo.

No se enviaron generaciones ni se configuraron claves o transporte del modelo;
esta prueba **no mide el nuevo corpus ni el streaming generativo**. Dos fallos
del arnés se conservaron y corrigieron sólo en esperas/selectores. La etiqueta
sintética HTTP del operador sufrió decodificación Windows; no acredita entrada
UTF-8. Base, cola y contenedores temporales retirados, túnel propio cerrado,
processor anterior restaurado sano, otros servicios y1247 entradas intactos.
No hubo activación permanente ni cambios de producto por este recorrido.

La comparación offline del corpus reproduce1018 fragmentos históricos de111
contextos:914 conservan texto/índice,100 cambian texto y4 cambian frontera.
Afecta a003/006/007/013/014/016/017/018/023/028. Los18casos restantes conservan
el texto observado, **no prueban una nueva búsqueda o generación**. El chunker
500/50 y las definiciones de los28casos/109requisitos son iguales; el banco no
incorpora casos de los nuevos estados/impacto acumulado/navegación de anomalías.
No se invalidan los resultados históricos ni se atribuyen al corpus nuevo.

## Contabilidad y continuación

Máximo autorizado vigente: **30USD acumulados**. Auditoría final N5:
**19.893051732USD de cota conservadora**, no factura ni atribución exacta.
Se conservan **12.69071250USD** de reservas desconocidas:11.73085650 anteriores
y0.959856 de016r2/010r3/027r3. No se tratan intentos desconocidos como gratis.

N5 tiene137costes observados:0.622073267USD. La continuación001r5 añadió28costes
observados por0.110671422USD (redondeados a9decimales; auditoría conserva valores
originales). Ledger final1275filas, SHA`0e861c496853a687f9053f2d0a212829cfd25a53752e4889cff0c6059f9751b9`;
1135previas y las1247al retomar siguen idénticas, igual que los112recibos y su
paquete parcial250archivos.

La política externa30USD, autorizada por «Ampliar a30», se aplicó a admisión y
ledger con seis guardas y comprobación fresca por operación. No cambió fuente,
prompt, modelo o plan de5119. Controlador803686 terminó con COLLECTED. Mismas
claves processor4.5/backend0.1 hasta16/10a18:00París, sin renovación ni nuevas.
No volver a lanzar140muestras. Paquete final310archivos conserva el histórico.
B no publicada; ningún despliegue compartido modificado.

## Para cerrar B

1. Resolver el defecto de calidad012 medido nuevamente, conservando las campañas.
2. Acordar criterios con los revisores y adjudicar012/023 sin simular consenso.
3. Determinar el alcance de validación de la integración con el corpus nuevo:
   la N3/N5 antigua no acredita esa combinación. Su plan N3 está NOT_RUN.
4. Revisar el candidato y sus límites antes de publicar/activar. El colector
   PR131 es independiente; sus reviews y CI no se trasladan a B. No CI verde
   ni aprobación nuevas afirmadas aquí. B permanece sin publicar.

## Evidencia reproducible

Directorio externo relativo a la raíz del proyecto:
`../materiales/07-evidencias/PR121-local-evaluation/`.

- `model-selection-final-v1.{json, md}` y `matched-model-comparison-final-v1.json`.
- `period-api-n3-final-audit-v2.json`, SHA
  `fe5db9bbb23b034044a8686726325d97ca0116ddf50ce9eb51c1220336f34541`.
- `period-api-n5-final-audit-v2.json`, SHA`6981d89bcdf3760cd3680d0a0517f65ce3c5b9760ed6c355119c8e28c0499406`.
- Paquete final310archivos: `period-n5-full140-frozen-v1/manifest.json`, SHA`db463ef190e19bc063784f0ef44ecaee329f9bb99b0b2a0f04ece9d4327f3bdd`.
- `period-api-n5-budget-stop-audit-v1.json`, SHA
  `30557789c152f64369446950e4376caf72780f965059e8d575c968235220d04f`.
- Paquete112 inmutable de250 archivos: `period-n5-budget112-frozen-v1/manifest.json`,
  SHA`a34817a826b8c41a1ebc4d518573d7faf002065c225299e616cc25c6cd903d88`.
- `period-integration-sql-final-audit-v2.json` y
  `period-integration-build-final-audit-v1.json`.
- `integration-ui-final-audit-v1.json` y `integration-ui-collected-v1/`: HTTP/UI de costes off/on sin modelo; auditoría SHA`6b6d98a50c49c5ecaf429f9222ec09891be5a2d1727d54d9e69cf09aa165042d`.
- `integration-corpus-impact-v1.{json,md}`: comparación offline y alcance pendiente; JSON SHA`43f60ff5b4905e39d30f730873e98bbb3de5bb08c946e428013b34ad9f7dd191`.
- `period-n5-cap21-continuation-proposal-v1.json`: simulación contable, no permiso.

Los contextos de RAG tardío se reconstruyen con suplementos SQL de hash exacto;
la entrada de fallos también usa SQL explícito. Los originales se preservan y no
se presenta la recogida como exclusivamente pública. El paquete congela las
vistas al momento de exportarlas: una nota temprana sobre reserva pendiente no
sustituye las disposiciones finales de la auditoría.

Estado y procedimientos en [continuidad](../continuidad/chat-evaluacion-local.md).
