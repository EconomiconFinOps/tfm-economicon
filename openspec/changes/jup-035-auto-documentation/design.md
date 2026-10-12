JUP: JUP-035

## Decision
Usar dos fases incluso sin herramienta. Una respuesta de la primera fase no
cumple un esquema final impuesto y no puede ser aceptada como respuesta publica.
Su texto tampoco se añade como mensaje assistant a la segunda fase. Con una
herramienta se conserva solo el envelope validado, su ID y resultado autorizado.

El contrato mantiene bundle v3 pero cambia su hash y protocolo; los descriptores
que no coinciden fallan cerrados. Se conservan max_searches=1, max_generations=2,
HMAC, intento vigente, plazo absoluto, cancelacion, limites y suma de uso.

## Policy
Auto puede no buscar. Si falta sustento documental, el prompt exige abstencion
no accionable/aclaracion. No hay forced retrieval ni tercera llamada. Los
validadores siguen rechazando evidencia ajena/inventada, provenance alterada y
metricas no contrastadas por billing. El control semantico de afirmaciones en
texto requiere evaluacion real; una prueba con proveedor simulado no lo acredita.

## Diagnosis
Cuatro regresiones nuevas fallan funcionalmente sobre f63c150: parser rechaza
native_seen fuera de required y trata el texto de decision como JSON final;
el coordinador no inicia dos fases en auto. Esto demuestra el bloqueo propio,
no una incapacidad de GLM, DeepInfra, OpenRouter o LiteLLM. La coexistencia del
schema estricto es una hipotesis de proveedor que no se prueba sin presupuesto.

## Rollout
Parche para Paris en rama propia. Revision Alejandro y validacion Lucia
independientes siguen pendientes. No push a la rama original, merge o despliegue.
