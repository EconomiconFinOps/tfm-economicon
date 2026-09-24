# Batería de preguntas FinOps — JUP-069

[Tarjeta](https://trello.com/c/Qi5uwxgW) · [Preguntas y respuestas esperadas](JUP-069-questions.json) · [Evidencia técnica](../evidence/JUP-069-validation.md)

La batería contiene **28 consultas representativas en español**, redactadas para
probar el MVP de forma repetible. No son conversaciones recogidas de clientes.
Los importes y suscripciones de cada contexto son ejemplos **sintéticos**,
autocontenidos e independientes; no proceden del dataset público Microsoft ni
demuestran resultados de un tenant real. Las reglas se apoyan en el corpus
versionado del repositorio. No se necesita Azure, red, credenciales ni un LLM
para validar o preparar la batería.

## Cobertura

Los sufijos corresponden a IDs estables `JUP-069-NNN` del JSON; identifican casos
de prueba de esta tarjeta, no tareas adicionales.

| Categoría | Casos | Qué se comprueba |
| --- | --- | --- |
| Costes | 001–004, 027 | Total y servicio principal, evolución, ambigüedad, actual/amortizado, coste unitario |
| Asignación | 005–009, 028 | Shared/excluded, límites 5 %/10 %, denominador cero, reparto sin regla, showback |
| Tagging | 010–012 | Tags mínimos, cumplimiento ponderado por coste, asignación por regla documentada |
| Presupuestos | 013–015 | Variación, forecast frente a gasto observado, ausencia de apagado automático |
| Anomalías | 016–019 | Doble condición, igualdad en ambos límites, baseline cero |
| Recomendaciones | 020–022 | Rightsizing con evidencia insuficiente, ahorro verificado, commitments |
| Alcance y datos | 023–026 | Tenant real no disponible, monedas distintas, orden de apagado, ingesta incompleta |

Cada caso conserva pregunta, contexto completo, categoría, comportamiento esperado
(`answer`, `clarify` o `abstain`), fuentes y rúbrica. `clarify` permite dar una
respuesta parcial fundada y pedir el dato que falta. `abstain` exige no afirmar
información o ejecución inaccesible, aunque puede ofrecer un siguiente paso.

## Validar y preparar

Desde la raíz del repositorio, con Node.js 22 o posterior:

```sh
node tools/validation-questions.mjs validate
node --test tools/validation-questions.test.mjs
node tools/validation-questions.mjs prepare > validation-inputs.json
```

También están disponibles `pnpm validation-questions:validate` y
`pnpm validation-questions:test`. Para redirigir el JSON se usa directamente Node
y así se evita que el encabezado de pnpm contamine el fichero. Guardar los inputs
generados fuera de Git o en una carpeta temporal de evidencias.

`validate` revisa estructura, IDs, cobertura, rúbricas, referencias y SHA-256 de
las fuentes (normalizando CRLF a LF). No evalúa la calidad de una respuesta.
`prepare` falla si la batería no es válida y emite solo ID y prompt por caso,
además de versión y hash de la batería. El prompt concatena contexto y pregunta;
no contiene rúbrica, comportamiento esperado ni clave de respuestas.

## Protocolo de ejecución para JUP-070 y JUP-071

1. Fijar el commit de aplicación y batería; ejecutar los dos checks anteriores.
   Guardar versión y `suite_sha256` del JSON preparado junto a los resultados.
2. Registrar fecha UTC, entorno, corpus/index utilizado, dataset disponible,
   proveedor/modelo (o mock), configuración de generación, prompt de sistema y
   modo de acceso (chat manual o adaptador de evaluación). No guardar secretos.
3. Cargar el corpus permitido mediante el flujo existente, cuando se pruebe RAG.
   La batería y sus respuestas esperadas **no se añaden al manifest ni al índice**.
   Los datos numéricos se suministran dentro del prompt, no se presupone que
   existan como recursos o registros de la aplicación.
4. Usar una conversación nueva para cada caso. Enviar exactamente el `prompt`
   preparado y guardar la respuesta original, citas y errores. No enviar el JSON
   de respuestas esperadas al modelo ni añadir pistas para conseguir un aprobado.
5. Evaluar todos los puntos de `required`, ninguna conducta de `forbidden` y
   todos los valores de `numbers`. Se aceptan paráfrasis: no comparar texto
   literalmente. La tolerancia es absoluta en la unidad indicada; en porcentajes
   son puntos porcentuales. Comprobar etiquetas/unidades, no solo que aparezca un
   número. Una explicación coherente con 10 % no permite clasificar 10,1 % como amarillo.
6. Comprobar fundamento en las fuentes indicadas. Si el sistema ofrece citas,
   verificar que respaldan las afirmaciones; no aceptar una cita inventada como
   evidencia. La evaluación específica de presentación de citas no se implementa aquí.
7. Registrar por caso `pass`, `fail`, `blocked` o `not_run`, explicación del
   revisor y referencias a la respuesta original. `pass` exige todos los criterios
   anteriores. Un error de infraestructura es `blocked`; una respuesta incorrecta
   del sistema funcionando es `fail`. No omitir silenciosamente ninguno.
8. Para comparar ejecuciones, mantener las mismas entradas/configuración y
   registrar las repeticiones; un LLM puede variar incluso con temperatura cero.
   JUP-070 decide la metodología y los umbrales de aceptación del sistema.

Plantilla de registro (una fila por ID en cada ejecución):

| Ejecución | Caso | Respuesta/evidencia | Criterios incumplidos | Resultado | Revisor |
| --- | --- | --- | --- | --- | --- |
| fecha UTC + commit + versión/hash | JUP-069-001 | referencia al texto original | pendiente | not_run | pendiente |

Registrar los totales de los cuatro estados con denominador **28** para esta
versión. No tratar `blocked`/`not_run` como aciertos ni llamar «calidad validada»
al check estructural. El proveedor mock actual puede no producir cálculos o
respuestas semánticas suficientes: conservar ese resultado sin alterar la clave.

## Mantenimiento y límites

El JSON es la fuente única de preguntas y rúbricas. Los hashes impiden que un
cambio del corpus modifique silenciosamente la referencia: revisar los casos
afectados, actualizar expectativas y hash, incrementar `suite_version` y repetir
las pruebas. Conservar los IDs; no reutilizar un ID para otra pregunta. Un cambio
incompatible del formato requiere nueva `schema_version` y adaptación del validador.

JUP-069 entrega el instrumento de prueba y su preparación determinista. La
evaluación de respuestas frente a referencia corresponde a JUP-070; la ejecución
de robustez, a JUP-071. No se implementan scoring con LLM, llamadas al chat,
benchmarks de latencia, nuevas reglas de negocio ni integración con Azure real.
