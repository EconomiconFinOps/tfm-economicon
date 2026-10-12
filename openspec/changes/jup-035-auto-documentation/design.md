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
Paris autoriza el 12/10/2026 incorporar esta rama en la entrega local de JUP-035
y conservar el RAG automatico. Un ensayo real documental recupera fuentes,
cita los fragmentos que sustentan owner/equipo/PII y persiste el par completo.
Un saludo inicial falla por evidence_membership: sin fuentes disponibles, el
esquema aun permitia inventar referencias. Paris autoriza restringir el esquema
de finalizacion a evidence vacia y estados no accionables en esa situacion.

La disponibilidad se deriva solo de authorized_evidence y del resultado de la
herramienta ya validado. No es un flag publico ni una decision del modelo.
Con fuentes financieras o corpus se conservan ambas ramas del esquema anterior.
El esquema base se sigue contabilizando como cota conservadora: la variante
sin fuentes elimina la rama accionable, sin ampliar ventana ni cambiar hashes
de los recursos, protocolo automatico o validadores finales.

El saludo corregido pasa con OpenRouter y no usa retrieval ni citas. Esta
aceptacion focal no equivale a otra bateria completa ni a validacion humana.

Parche para Paris en rama propia. Revision Alejandro y validacion Lucia
independientes siguen pendientes. No push a la rama original, merge o despliegue.

## Convivencia con consulta de propiedad

Paris aprueba el 12/10/2026 conservar JUP-037 en `/ownership`, reutilizando su
formulario, aislamiento y endpoint `messages` con `ownership_query` obligatorio.
No se restituye la generacion ficticia ni la pestaña `/assistant`: esa ruta abre
el panel nuevo. El evaluador sigue usando generaciones. La captura de la nueva
vista es `no-adapter`, sin promover el historial o formulario a evidencia financiera.
