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
Implementacion de Alejandro en PR121 sobre la base de Paris. Revision de Victor
y validacion de Lucia siguen pendientes. No push a la rama original, merge ni
cambio del despliegue compartido.


## Seleccion de evidencia por intento (12/10/2026)
El esquema estatico del manifiesto es una plantilla. Antes de finalizar se
construye su variante efectiva con los registros autenticados iniciales y la
extension HMAC ya validada. Cada alternativa fija id, kind, title y source; una
lista vacia solo admite estados no accionables sin citas. Backend y processor
cuentan esa variante. El backend conserva un firewall independiente: no confia
en que el proveedor respete el esquema y nunca repara un candidato invalido.
El hash de ensamblador identifica effective-context-exact-records-v2.

Las llamadas multiples del endpoint actual se reproducen y permanecen
rechazadas; no se presentan como corregidas sin un control compatible probado.
El nuevo esquema tiene regresiones offline; su aceptacion real sigue pendiente.

La proyeccion v2 omite uniqueItems, rechazado con HTTP400 por el endpoint real.
Se conservan las alternativas exactas y el rechazo local de IDs duplicados en
FinOpsResponse del processor y en el firewall backend; no se normaliza salida.
