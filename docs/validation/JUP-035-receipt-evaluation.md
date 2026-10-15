# Evaluación reproducible de recibos JUP-035

Estado: propuesta local del 13/10/2026; no sustituye JUP-070 ni una review humana.
Herramienta: `tools/chat-receipt-eval.py`, biblioteca estándar, sin acceso a red.

Actualización15/10: la comparación de modelos distingue errores del proveedor,
respuestas técnicamente válidas y requisitos semánticos adjudicados. Un replay de
generación con contexto congelado no acredita API, SQL, historial ni navegador.
No se convierte una respuesta recogida en PASS por coincidencias de números.

El adaptador `chat_generation_schema.py` conserva el esquema lógico completo:
expande constantes exactas y elimina sólo gramáticas inaccesibles. Los validadores
de respuesta y la unión de modos siguen aplicándose; no hay reparación de JSON,
reintentos ocultos ni generación de datos por defecto. Backend y processor cuentan
el esquema enviado al proveedor, y su manifiesto incorpora la versión y hash del
adaptador. Un descriptor de la versión anterior no sirve para admitir la nueva.
La copia de backend debe coincidir con la fuente de processor y con el hash del
manifiesto; esto no resuelve la deuda previa de módulos duplicados en el proyecto.

Las pruebas de equivalencia usan `jsonschema==4.25.1` sólo como dependencia de
desarrollo. El runtime no incorpora esa dependencia. Cambiar esta representación
del esquema no demuestra que un proveedor la acepte ni que el contenido cumpla:
ambas cosas requieren evidencia separada sobre el candidato correspondiente.

## Contrato

Se mantienen intactos los 28 casos y los 109 requisitos originales de
`JUP-069-questions.json`. Cada requisito conserva texto y hash. La rúbrica local
añade dos comprobaciones independientes por respuesta (56 en total): soporte de
afirmaciones/citas y consistencia de la respuesta completa. Su origen se indica
como `provisional-local-rubric-v1`; no se atribuyen al banco original.

Los recibos antiguos se normalizan conservando respuesta, campos auxiliares,
fragmentos citados y etiqueta histórica. `completed` sólo significa terminación
técnica. `NO_VIOLATION_OBSERVED` no es una etiqueta adjudicada por requisito.
Falta de respuesta, entrada no verificable y revisión incompleta tienen estados
separados. El veredicto de aceptación siempre queda NOT_ASSESSED en esta versión.

Se reutilizan las reglas numéricas y de prohibiciones de JUP-070 como diagnóstico.
Una coincidencia de número/unidad/alias no prueba una afirmación correcta: por
ejemplo, la regla reconoce «El total no es 1000 EUR». La ausencia de una expresión
prohibida tampoco demuestra que no haya una paráfrasis de ella. Ninguna heurística
convierte por sí sola un requisito semántico en PASS.

## Rúbrica para adjudicación

- `required`: todas las partes del requisito deben estar expresadas. Conclusión
  correcta pero incompleta falla; citar los datos de entrada no sustituye el contraste.
- `numbers`: valor, unidad, denominador, etiqueta y función en la conclusión
  deben ser correctos. Una cifra negada o atribuida a otra magnitud no cumple.
- `forbidden`: PASS significa que no se observa la conducta en la respuesta
  completa, incluidos assumptions/next_actions. Un ejemplo hipotético no excusa
  una prohibición explícita de inventar un tipo de cambio.
- `quality-grounding`: cada cita debe apoyar una afirmación presente. El título
  de la sección o el solapamiento de palabras no basta. No se sustituye un chunk
  truncado por contenido del documento completo que el modelo no recibió.
- `quality-consistency`: contrastar cálculos y conclusiones, incluidos campos
  auxiliares. Si el cálculo es correcto y el comparador incorrecto, el número
  puede pasar mientras la clasificación falla.

Cada juicio incluye revisor real (el agente local no se hace pasar por humano),
razón, hash de evidencia y hash del requisito. Para FAIL se exige un grupo causal
local a la respuesta. Los errores del mismo origen se cuentan como un grupo,
aunque afecten a varios requisitos. Etiquetas dudosas permanecen `uncertain`.
La discrepancia con el veredicto histórico debe explicarse, no borrarse.

## Calibración y reserva

`JUP-035-evaluation-partition.json` reserva familias completas: budgets (013–015)
y recommendations (020–022), en ambas campañas. Los otros 22 casos son calibración.
La primera prueba detectó un nombre de categoría incorrecto (`budget` frente a
`budgets`); se corrigió antes de adjudicar y ajustar reglas. No se seleccionan
repeticiones buenas ni se mezcla focal con full28.

Los recibos y sus conclusiones ya eran conocidos en la conversación: esta reserva
NO es un conjunto ciego nuevo. Sirve para evitar nuevo ajuste a esos casos. Para
afirmar generalización será necesario un conjunto independiente. No se ha entrenado
ni calibrado un juez LLM, ni se ha pagado por uno.

## Uso

Guardar salidas y juicios fuera del checkout, siguiendo JUP-070. Ejemplo desde
la raíz del proyecto (sustituir `../evaluacion` por la carpeta de evidencias):

```sh
python tools/chat-receipt-eval.py score --receipt docs/evidence/jup-035-pr121-full28-20261012.json --section results --partition docs/validation/JUP-035-evaluation-partition.json --judgments ../evaluacion/judgments-first.json --output ../evaluacion/first.json
python tools/chat-receipt-eval.py score --receipt docs/evidence/jup-035-pr121-review-fixes-20261012.json --section full28 --partition docs/validation/JUP-035-evaluation-partition.json --judgments ../evaluacion/judgments-second.json --output ../evaluacion/second.json
python tools/chat-receipt-eval.py compare ../evaluacion/first.json ../evaluacion/second.json --output ../evaluacion/comparison.json
python -m unittest discover -s tools -p test_chat_receipt_eval.py -v
```

Formato de juicios: objeto indexado por `sample_id` de la salida, con objeto por
identificador de requisito. Cada entrada lleva `status` (`pass`, `fail`, `uncertain`),
`reviewer`, `reason`, `evidence_sha256`, `criterion_sha256` y, para fallo,
`failure_cluster`. No hay conversión automática de etiquetas históricas.

La comparación exige banco, partición, scorer y reglas idénticos. Empareja por
caso y repetición y conserva fallos técnicos, ausentes, pendientes y transiciones
en ambos sentidos. Las campañas históricas son N=1: sus diferencias son descriptivas,
no atribución causal a un cambio. No hay intervalo de confianza fingido por contar
requisitos correlacionados como muestras independientes.

## Medición siguiente

Antes de N=3 congelar commit, prompt, esquema, corpus, fragmentos recuperados,
configuración/modelo, banco, scorer y estado inicial. Conservar todos los intentos
y costes. Ninguna media compensa una regresión obligatoria. Un juez futuro debe
medirse contra adjudicaciones revisadas y reserva, incluyendo falsos PASS y FAIL.
El runner histórico no se ejecuta contra el entorno compartido para simular una
base local. El 13/10 Docker Desktop local no tiene daemon accesible; el contexto
predeterminado apunta a DockerServer. No se ha desplegado ni cambiado ese entorno.

Desde un commit local limpio, `python tools/chat-eval-plan.py --repetitions 3
--output ../evaluacion/baseline-plan.json` congela84 entradas exactas y hashes
del código/prompt/corpus/scorer. `--repetitions 5` prepara140 entradas sin escoger
casos favorables. Este comando no ejecuta consultas: conserva NOT_RUN y exige
proveniencia del runtime, contexto recuperado, parámetros y contabilidad viva al
ejecutar. El balance histórico no basta para admitir gasto. Cada repetición debe
recogerse íntegra y evaluarse conservando su identidad; los adaptadores de recibos
actuales describen las campañas históricas N=1 y no son un colector del API nuevo.


## Adaptador repetido JUP-123 — 14/10/2026

El recibo puede declarar `repetitions: 3` o `5`; cada fila debe incluir
`repetition` entero entre 1 y N. El par caso/repetición es único. No se admiten
recibos repetidos vacíos ni sustitución de fallos por reintentos favorables.
Los intentos adicionales se preservan en sus propios recibos de ejecución.
`missing_samples` y `samples_expected` hacen visibles repeticiones omitidas aunque
aparezcan todos los casos. N1 mantiene los identificadores históricos. El colector
API sigue pendiente: las 15 pruebas unitarias no constituyen una campaña N3.


## Recogida pública del API — JUP-123

`tools/chat-eval-collect.py` recoge una operación existente y terminal mediante
GET: estado antes/después, contexto, evidencia, historial y resultado. No inicia
ni reanuda inferencias. Los identificadores se validan; los redirects se rechazan;
el token y tenant se leen de CHAT_EVAL_TOKEN y CHAT_EVAL_TENANT y no se guardan.

Ejemplo (variables de autenticación ya configuradas, sin ponerlas en comandos):

```sh
python tools/chat-eval-collect.py --plan ../evaluacion/plan.json --sample JUP-069-001:r1 --conversation ID --operation ID --base-url http://127.0.0.1:28657 --output ../evaluacion/001-r1.json
```

Ese puerto es sólo un ejemplo, no identifica el runtime B. Es obligatorio verificar
procedencia antes de generar una campaña. La herramienta exige salida nueva fuera
del checkout. Conserva fallos HTTP por clase/código sin texto de error sensible;
rechaza estados no terminales y deja el handle disponible para observación posterior.
No reemplaza un intento fallido por otro. Cada recibo parcial se puede inspeccionar
con el scorer: las otras muestras constarán ausentes hasta agregarlas.

VERIFIED_PUBLIC_SNAPSHOT significa igualdad de resultado/historial, entrada única
correcta, snapshot estable y citas con identificadores conocidos. No prueba soporte
semántico, commit, proveedor, payload completo ni contabilidad. El evaluador bloquea
PASS si la recogida es incompleta, incluso con juicios manuales positivos.
Pendiente agregar recibos, verificar entorno/coste y ejecutar N3: este componente
no es todavía el ejecutor de campañas.


Agregación: `python tools/chat-eval-aggregate.py --plan PLAN --output NUEVO_JSON
RECIBO1 RECIBO2 ...`. El agregador mantiene el hash canónico del plan y de cada
recibo; no acepta conversaciones reutilizadas ni duplicados caso/repetición.
La salida COLLECTED puede contener fallos técnicos y no implica PASS.

Admisión de coste: `tools/chat-eval-budget.py` calcula el máximo de4intentos por
operación, con3200tokens de salida por intento y entrada total de ambas fases.
Las tarifas y cota de entrada deben verificarse, no estimarse a partir de medias.
Costes auxiliares incluyen embeddings u otros servicios facturables. El runner
pendiente debe guardar la reserva antes de POST y conservarla ante timeout o
caída; sólo reconciliación contable prueba el coste final. El módulo no consulta
proveedores y no convierte una afirmación de snapshot en evidencia autenticada.


Registro duradero: `tools/chat-eval-ledger.py` serializa reservas en SQLite con
BEGIN IMMEDIATE; todas las campañas del límite acumulado usan el mismo fichero.
Antes del callback de envío confirma DISPATCHING. Tras timeout se recupera la
operación por lectura usando request_id; nunca se vuelve a enviar automáticamente.
La reserva permanece mientras el coste sea desconocido. La conciliación de coste
observado exige informes completos de todos los intentos y fases; una respuesta
final correcta no acredita la facturación del intento anterior. No eliminar
filas ni abrir otro ledger para eludir reservas pendientes. El adaptador debe
demostrar esa cobertura antes de sustituir el máximo por un coste observado.


Transporte de ejecución: `chat-eval-api.py` crea una conversación y recoge el
handle inicial SSE o JSON. El ejecutor debe pasar generate como callback de
Ledger.dispatch después de comprobar procedencia y contabilidad. Si falla el
envío, recover_handle usa exclusivamente GET /assistant/requests; devolver None
no autoriza repetir POST. Se conserva la reserva hasta reconciliar el resultado.
No usar este módulo de forma aislada para una campaña de pago.


Orquestación: `chat-eval-runner.py` ofrece Runner.step(), una transición por llamada.
Se inyecta un adaptador que consulta procedencia y contabilidad real; aún no se
expone CLI de pago. Retorna OBSERVING para operaciones vivas, UNKNOWN_DISPATCH
si no se recupera el handle y NEEDS_RESERVATION_RECONCILIATION para una reserva
interrumpida antes de envío. Ninguno de esos estados autoriza reintentar POST.
Una campaña COLLECTED aún necesita agregación, adjudicación y aceptación.


## Forecast completo aportado — corrección local del 16/10/2026

La comparación mensual completa usa `monthly_comparison`: dos meses explícitos,
mismo año/ámbito, meses completos, moneda y base de coste comparables. El mes de
referencia pedido es el denominador aunque se invierta el orden de las cantidades
en la declaración; baseline cero conserva diferencia y porcentaje indefinido.
La salida sólo explica esos datos y cálculos, sin poder añadir el método documental
de investigación que falló en GLM002r3. Cantidades, meses, ámbito y base de coste
son variables. Declaraciones parciales, monedas mezcladas o autoridad financiera
distinta conservan la ruta general. No es un extractor universal.

La ruta `forecast_budget` acepta únicamente una petición completa de comparación
al cierre y una declaración hipotética fechada con acumulado, forecast suministrado,
presupuesto, moneda y ámbito inequívocos. Conserva el acumulado como dato de la
fecha de corte, el forecast como predicción no garantizada y el presupuesto como
base de la desviación. El servidor calcula diferencia y porcentaje; un presupuesto
cero deja el porcentaje indefinido. No genera un forecast ni añade políticas de
alerta o apagado sin evidencia. La salida mantiene `insufficient_data` y métricas
y evidencias vacías: no convierte datos del usuario en facturación verificada.

No es un extractor universal de lenguaje natural. El módulo consume la declaración
completa y rechaza esa ruta ante fechas/monedas incompatibles, partes ausentes,
roles duplicados, instrucciones añadidas o evidencia financiera de otra autoridad.
Esos casos siguen el contrato general, sin corregir sus datos silenciosamente.
Las 28 pruebas de forecast y las 29 de comparación mensual cubren datos variables,
límites y rechazo de ID o auxiliares forjados; 258 pruebas locales de los contratos
afectados conformes, incluidas las 57 nuevas. El primer intento conjunto no llegó
a ejecutar pruebas por un parámetro reservado de pytest; se corrigió sólo su nombre
y se conserva ese recibo de error junto con la pasada posterior completa.
La medición y la regresión nativa del candidato nuevo siguen pendientes. Se
conserva el fallo medido de GLM014r2 y no se reetiqueta con el resultado del código.

## Evidencia RAG posterior al contexto inicial — 14/10/2026

Verificado en B: el endpoint de evidencia conserva el contexto inicial; los
fragmentos recuperados durante la operación no aparecen allí. El manifest del
resultado conserva sus IDs ordenados y el hash exacto del payload de recuperación.
`chat-eval-retrieval.py` admite un snapshot suplementario sólo cuando coincide
con ese hash (incluido escape de ángulos, orden de fragmentos y omisiones), la
identidad de operación y la lista de evidencias del manifest. Recalcula las
comprobaciones de pregunta/historial/estado desde los recursos originales.
Una cita desconocida o un historial diferente siguen dejando INCOMPLETE.

El recibo derivado conserva íntegros `resources` y su hash; incorpora snapshot,
hash suplementario y derivación que apunta al hash de la fila original. El
operador guarda primero la copia original separada antes de instalar la vista
derivada. La recuperación SQL del corpus de B verifica además el hash de cada
documento contra el banco original y reconstruye título/spans con el mismo
código versionado; no vuelve a ejecutar embeddings ni el modelo. Una discrepancia
no se corrige buscando otro fragmento parecido: detiene la recogida.

Seis pruebas cubren recuperación exacta/escape UTF8, fragmentos u omisiones
alterados, operación ajena, citas desconocidas, pregunta/historial distintos y
recursos modificados. Conjunto herramientas49PASS. Esta verificación demuestra
identidad de los fragmentos, no pertinencia semántica de las citas. La aceptación
continúa pendiente de adjudicación y de los criterios de revisores.

## Tokenizer generado y procedencia — 14/10/2026

Tras reconciliar A/28ee5b1c, el tokenizer ya no pertenece al archivo Git. El plan
congela también helper, Dockerfiles y locks, y declara `generated_artifacts` con
revisión, bytes y SHA256 comunes de los manifests de chat y summary. El verificador
comprueba el hash del archivo instalado en backend y processor, en sus rutas
propias. Un archive fuente no tiene que contener el artefacto generado.

Los planes nuevos que incluyen el helper no pueden omitir el pin generado;
tampoco se admiten rutas arbitrarias, identidades duplicadas o metadatos inválidos.
El preflight del adaptador debe devolver esos pins después de verificar ambos
contenedores. Runner rechaza su ausencia antes de reservar o enviar una petición.
Los planes históricos permanecen intactos y conservan su contrato anterior con
el tokenizer versionado. Esta compatibilidad no permite omitir el artefacto en
planes nuevos. Las pruebas son offline; no acreditan un runtime nuevo ni gasto.

## Respuesta completada con coste desconocido — 15/10/2026

Un intento puede perder su registro de consumo y una repetición automática
posterior completar la respuesta. El contenido sigue siendo completed, pero
su coste no está conciliado. Ledger.retain_completed_cost permite registrar
ese hecho sin convertirlo en un fallo de contenido y sin reducir un céntimo
de la reserva original. Es una operación explícita, no una decisión basada
en spend0, ausencia de ID o silencio del proveedor.

Exige estado completed, pregunta/estado/citas verificados, paridad con historial,
respuesta pública no vacía, recursos con hash exacto y coincidencia entre esos
recursos, el resultado y las dos lecturas de la operación. La transacción sólo
admite una reserva completa aún intacta para la misma conversación/operación.
Guarda terminal_completed y el hash del recibo; no crea terminal_failure.

retained_cost conserva la compatibilidad con los comprobantes terminal_failure
anteriores. El auditor de prefijos y Runner aceptan ambas procedencias sólo
con identidad y máximo completo. La admisión sigue sumando el importe íntegro:
un estado terminal registrado no autoriza la siguiente llamada si rebasa el
límite. No se sobreescriben comprobantes de coste ya observados.

109 pruebas offline cubren las herramientas completas. Un ensayo separado con
la proyección de las303 filas reales conserva302 filas históricas y todos los
importes, registra completed para008 y rechaza la novena reserva con el máximo
de5USD. No es una modificación del ledger real ni una conciliación del proveedor.
Esta corrección local posterior no cambia el plan, candidato o recibos de la
campaña7be57c05 congelada. Antes de usarla en una continuación hay que registrar
su versión de herramientas y verificar de nuevo procedencia y admisión; no
sustituir a escondidas los ficheros que el plan anterior mantiene fijados por hash.
