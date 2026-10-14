JUP: JUP-123

## Context

B preserva el flujo que ya recupera documentación en servidor y genera draft/final
sin herramientas nativas. Retirar tools no es una nueva solución pendiente.
El scorer previo conserva 253 juicios históricos y nueve incertidumbres.

## Decisions

1. Reconciliar A por bloques usando la base Paris f63c150 para adiciones paralelas;
   mantener semántica B y controles de activación, cancelación y fecha de A.
2. N=3 inicial, N=5 de confirmación según criterios obligatorios y presupuesto.
   Sin selección del mejor intento ni omisión silenciosa de fallos técnicos.
3. Identidad por campaña, caso y repetición; banco y corpus inmutables. Conservar
   commit, hashes, entradas, fragmentos realmente usados, parámetros y costes.
4. Contabilidad viva y reserva conservadora antes de inferencias. Tope acumulado
   de 2 USD, incluyendo intentos fallidos y servicios auxiliares facturables.
5. Las coincidencias de palabras/números son diagnósticos, no veredictos semánticos.
   Citas requieren soporte de la afirmación, no sólo solapamiento léxico.
6. Las correcciones se evalúan contra la misma rúbrica congelada. Ninguna media
   compensa una regresión obligatoria; umbrales aún pendientes de revisores.

## Risks and open questions

El entorno compartido anterior no demuestra procedencia del candidato nuevo.
Colector y baseline real N3 completados el 2026-10-14: 84 recibos, 77 operaciones
completadas y 7 fallidas preservadas. Pendientes adjudicación independiente,
acuerdo de criterios y comparación del candidato corregido. El candidato e94 completó regresión Linux y43pruebas SQL reales; el historial017
se verificó en navegador, sin nueva generación. El candidato posterior requiere
su propia validación. La campaña comparativa quedó parcial41/84 por presupuesto.
No afirmar cierre por superar pruebas unitarias ni por reunir 84 recibos.

## Premisas y conclusiones — integración en curso, 2026-10-14

Los fallos026/028 no se resuelven comprobando sólo que una cita sea literal.
Se introduce un evaluador trivalente acotado (`chat_premises.py`), integrado primero en la combinación de comparaciones numéricas
verificadas; la ruta de premisas textuales continúa pendiente. Una premisa conocida tiene procedencia; una premisa
no evaluada conserva valor desconocido, sin evidencia negativa inventada.
AND/OR/NOT usan lógica de Kleene. Se validan todas las ramas y se conservan
las premisas desconocidas aunque otra condición determine el resultado.

La frontera de confianza es explícita: el evaluador NO interpreta lenguaje
natural ni demuestra implicación documental. Sólo admite objetos construidos
por código de servidor; no diccionarios de verdad/procedencia del proveedor.
El enlazador deberá contrastar identidad, ámbito, instante y soporte semántico
con la entrada capturada o la fuente autorizada. Citar una frase literal no
basta para establecer su valor. Una regla ambigua no produce una premisa falsa.

Integración pendiente, por orden:
1. Enlazar hechos tipados con observaciones/fragmentos originales. Registrar
   lo que no se ha medido como desconocido. No deducir gasto cero de cero filas.
2. Aplicar reglas explícitas con sus propias fuentes, separando evidencia de
   la regla de evidencia de los hechos; la regla general no verifica al cliente.
3. Una misma decisión alimenta respuesta, limitaciones y recomendaciones.
   La redacción de esos terminales no puede sustituir desconocido por falso.
   Conservar el resto de la síntesis útil y el alcance original del chat.
4. Derivar citas de reglas y premisas utilizadas; nunca añadir fuentes sólo
   por aparecer en el retrieval. No declarar resuelta la pertinencia general.
5. Verificar por replay de026/028, contraejemplos, streaming/final y backend;
   actualizar el contrato de recursos sólo cuando la ruta esté integrada.

Treinta pruebas del núcleo cubren las tablas de verdad y límites, pero no
acreditan el enlazador, extracción, redacción ni la corrección del producto.
No se cambia el candidato desplegado ni la campaña congelada para este trabajo.

### Fuente disponible para el enlazador de cobertura

Inspección de `apps/backend/app/services/chat_context.py::ChatContext.billing`
(14/10/2026): la consulta se ejecuta por tenant y periodo; `BillingSummary`
valida resultados, y la comparación con pantalla incluye importes, grupos,
conteos y estado. La evidencia cost_query expone métricas, periodo, agrupación
y data_status. Ese contrato no aporta una certificación de cobertura de ingesta
para el periodo completo. `available` y `matched_at_verification` no autorizan
inferirla. Tampoco los fragmentos FinOps generales acreditan cobertura financiera.

El enlazador debe separar como mínimo:
- `query_has_rows`: observación de la consulta contrastada, con su scope.
- `queried_total_is_zero`: sólo un total explícito contrastado para una moneda;
  no se construye a partir de una lista vacía ni mezcla monedas.
- `period_coverage_complete`: desconocido mientras no exista evidencia específica.
- `period_spend_is_zero`: no se deriva de query_has_rows=false; requiere total y
  cobertura completos en el mismo scope/periodo/moneda.

Los escenarios textuales del usuario, incluido026, mantienen procedencia
hipotética y no pasan a este canal de autoridad financiera. La integración
requiere además una ruta de escenario explícita y sus contraejemplos; no usar
una mera coincidencia de palabras para simular observaciones autenticadas.

### Integración numérica verificada

render_boolean construye premisas a partir de resultados de _numeric y del
comparador de la regla ya ligada al catálogo. evaluate combina esos resultados;
no recibe la verdad escrita por el modelo. Conserva la semántica anterior y
no cambia las fuentes documentales. Las pruebas de streaming/final incluyen
falso AND desconocido=falso y falso OR desconocido=desconocido, sin convertir
el operando desconocido en falso. Queda pendiente el enlace textual descrito
arriba; esta integración no cierra026/028 ni suple la campaña real incompleta.

### Terminal documental de reporting (implementado localmente)

Para clasificación showback/chargeback, una gramática cerrada enlaza el escenario
completo con la presencia/ausencia explícita de repercusión contable. No extrae
ese hecho de una frase aislada ni acepta instrucciones o condiciones adicionales.
Un bloque completo de definiciones y sección documental autentificada proporciona
la regla; un hash de entrada+fuente liga el terminal privado. La respuesta usa
la decisión del servidor, explicita que la calidad no se evaluó y conserva citas
literales. Se rechazan auxiliares libres en ese terminal, incluido el rationale
que causó028. El resto de rutas conserva su capacidad narrativa/recomendaciones.

La política admitida está codificada como una gramática documental, con términos
explícitos del corpus. Una política modificada o un escenario fuera de gramática
no se consideran equivalentes automáticamente. Su soporte requiere ampliación
justificada con pruebas; la ruta general no hereda garantías de este terminal.
El replay028 prueba selección y renderizado con entradas originales, no una
nueva respuesta del proveedor ni todo el espacio de preguntas conceptuales.

### Terminal de gasto desconocido en escenario incompleto

Implementado para una declaración completa de consulta vacía e ingesta incompleta
con pregunta de gasto cero y periodo coincidente. No acredita cobertura real ni
incorpora documentos generales como evidencia financiera. La premisa de gasto
cero es desconocida; el resultado explica qué falta sin afirmar un gasto positivo.
El terminal rechaza auxiliares del modelo y queda ligado al hash de la pregunta.
No toma prioridad sobre evidencia financiera del servidor. Otras formulaciones,
periodos contradictorios o datos añadidos retienen la ruta narrativa; esta ruta
cerrada no constituye una solución general de comprensión semántica. Replay026
y verificación de selección sobre calibración preservados fuera del repositorio.

## Auditoría de preparación para revisión — candidatofa5e9527, 2026-10-14

Esta tabla describe evidencias y pendientes; no modifica los criterios ni
convierte pruebas sintéticas en validación del modelo.

| Requisito | Evidencia comprobada | Estado / paso pendiente |
| --- | --- | --- |
| Reconciliar A/develop | merge-base confirma318a56f y c30a7d0 ancestros del candidato | Base actual incorporada; A/PR130 sigue abierta con tokenizer/reviews pendientes; revalidar si cambia |
| Identidades caso/repetición y ausencias | Baseline84/84 y candidato41/84 con hashes y agregados;43ausencias explícitas | Implementado; no declarar completa la campaña candidata |
| Contabilidad y procedencia | Ledger común, controles de hash/runtime y reserva que detuvo nuevas llamadas | Preservados; contador histórico conservador1.683584087 no es lectura viva actual |
| Línea base repetida |84recibos baseline,77completed/7failed conservados | Recogida completa; adjudicación independiente pendiente |
| Comparación emparejada |41muestras de e94:29fail→pass y regresión026r1 | Descriptiva/parcial; no acredita al candidato posterior |
| Correcciones semánticas |005determinista,026/028replay local,110/134pruebas focales y108gateway | Gramáticas cerradas; variantes no reconocidas conservan ruta general; aceptación no demostrada |
| Gateway y contrato público |12pruebas nuevas en108PASS; esquemas, streaming/final y rechazo de contradicciones | Probado con proveedor simulado, no ejecución final pagada |
| Linux | fa5e9527:244processor/64backendPASS,exit0; archivo e imágenes registrados | Superficies modificadas verificadas; no equivale a suite completa ni calidad real |
| SQL | fa5e9527:43PASS58.30s en instancia exclusiva limitada | Contratos SQL verificados; no prueba pérdida de red después deCOMMIT |
| Navegador | e94:historial017; frontend sin cambios; replays026/028 en1280/390px con texto íntegro normalizando espacios | Presentación simulada verificada; falta integración con backend/citas y proveedor actual; runtimeB SQL detenido porOOM |
| Especificación e higiene | OpenSpec estricto JUP123 válido; higiene1609archivosOK | Comprobado en9f52; CLI instalada en checkoutauto, sin instalar red |
| Criterios y N5 | Tareas1.4/2.4/3.3 abiertas; pregunta al usuario sobre acuerdo existente | No inventar acuerdo, porcentaje ni dispensa de revisores |
| Revisión externa/publicación | B no publicada; borrador técnico y evidencia local disponibles | No integrar ni afirmar listo para aprobación mientras faltan los puntos anteriores |

Comandos de comprobación local:
- `git merge-base --is-ancestor 318a56f31828be50f8960860f69172f51046734d HEAD`
- `git merge-base --is-ancestor c30a7d0f28c04cae757b424222b34b232814303e HEAD`
- `../tfm-economicon-jup035-auto/node_modules/.bin/openspec.cmd validate jup-123-chat-semantic --strict --no-interactive`
- `node tools/jup-cleanup-check.mjs`

La comprobación de higiene necesitó ejecución fuera del sandbox para invocar
`git` (EPERM inicial); no hubo una modificación del control ni descarga de paquetes.
El ejecutable openspec no está instalado en este checkout: se usó el ya instalado
en el workspace. Los fallos iniciales de herramientas no cuentan como aprobados.
