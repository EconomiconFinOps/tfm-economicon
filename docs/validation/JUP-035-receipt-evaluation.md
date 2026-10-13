# Evaluación reproducible de recibos JUP-035

Estado: propuesta local del 13/10/2026; no sustituye JUP-070 ni una review humana.
Herramienta: `tools/chat-receipt-eval.py`, biblioteca estándar, sin acceso a red.

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
