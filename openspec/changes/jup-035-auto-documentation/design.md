JUP: JUP-035

## Compatibilidad de la union final — 13/10/2026

Una reproduccion sintetica autorizada confirma HTTP400 de DeepInfra al compilar
la interseccion repetida del mismo literal de support_quote. El esquema final
conserva las dos ramas completas anyOf y los $defs compartidos, pero elimina
las restricciones duplicadas en la raiz. Cada rama implica el antiguo objeto
base: la equivalencia se comprueba estructuralmente y con candidatos validos e
invalidos, incluyendo autoridad financiera y campos obligatorios. No se cambian
validadores locales, citas autorizadas, limites ni contrato publico. La
compatibilidad real del esquema corregido requiere validacion posterior.

## Decision vigente — 12/10/2026
El usuario autoriza sustituir auto-documentation-v2 por structured-documentation-v3.
La primera generacion devuelve exclusivamente {action:none,query:null} o
{action:search,query:string}, mas calculations. El esquema raiz simple acota
campos y tipos; la relacion action/query se valida localmente. Se rechazan campos extra, claves duplicadas, texto libre,
llamadas nativas y truncacion. El proveedor fijo no necesita soporte de
parallel_tool_calls. El servidor despacha como maximo una busqueda existente.

La extension conserva el transporte HMAC vinculado al claim/tenant/intento.
tool_call_id es ahora el SHA256 de la decision canonica, no un ID fabricado
del proveedor. Su resultado se añade como dato user UNTRUSTED_RETRIEVAL_CONTEXT;
no se incorporan la decision ni mensajes assistant/tool. La segunda generacion
usa exclusivamente FinOpsResponse estricto con evidencia autorizada efectiva.
Se conservan dos generaciones, plazo absoluto, cancelacion, billing, cuotas,
3200 tokens de salida y contabilidad de ambas fases. Ambos servicios cuentan
el mismo esquema de decision y esquema final efectivo junto al contexto.

Cada alternativa documental exige support_quote privado del fragmento citado.
El esquema enumera ventanas literales no vacias de hasta2048 caracteres, y el
processor comprueba la seleccion exacta antes de proyectar FinOpsResponse1.0.
No modifica ni filtra citas o estados invalidos para admitirlos. Este control
acredita procedencia textual, no entailment: pertinencia, completitud y calculos
siguen sujetos a la bateria real. Las instrucciones generales conservan unidades,
denominadores, operadores estrictos y prohibicion de cotizaciones inventadas.

## Calculo hipotetico autorizado — 12/10/2026
La focal b79e4ee termina5/5 pero017 produce500−100=100, aunque aplica bien el
umbral. Por ello no se acepta ni se lanza full28 de ese candidato. Se añade
calculations a la primera decision: hasta12 pasos decimales con operandos de
la pregunta o referencias anteriores y unidades. El backend calcula y devuelve
resultados por HMAC; processor vuelve a calcular para verificar la extension.
none con calculos usa control privado pero cero busquedas. Los resultados son
hipoteticos, no evidence ni metrics. El manifiesto identifica esta politica.

La finalizacion privada usa listas de segmentos text o calculation_id, con
IDs enumerados a partir de los resultados autenticados. Answer y cada elemento
de assumptions/limitations/next_actions se proyectan a strings publicos. El
parser valida segmentos completos y tramos de texto contiguos, rechaza ecuaciones
libres o marcadores incluso partidos entre segmentos, y emite antes del cierre
JSON. Se conservan limites4000/500 caracteres,128 segmentos y deltas8192 bytes.
La normalizacion global de espacios coincide con strip_whitespace publico;
se preservan separadores internos. Comparaciones usan Decimal sin redondear; solo la salida
del resultado se redondea a seis decimales con signo aproximado cuando procede.
Los operandos visibles permanecen exactos. No existe garantia universal sobre
prosa ni sobre notaciones matematicas arbitrarias; su pertinencia se evalua con
la bateria real. No se prohíben numeros originales, fechas o identificadores.

## Antecedente sustituido: protocolo auto nativo
Las siguientes notas explican las decisiones previas; no describen el protocolo
vigente. Los resultados reales negativos se conservan como evidencia historica.

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

## Correcciones de revision (12/10/2026, 551fb81)
El observador captura el ultimo cierre publicado al suscribirse sin await en
medio. El POST ganador reconstruye tambien waiting/paused desde SQL cuando
todavia falta la publicacion RAM. La decision length se clasifica 502 incomplete,
igual que una finalizacion truncada; no se reutiliza su texto ni se añade otra
generacion dentro del intento. Las regresiones cubren las dos entregas, cuatro
estados y tres ordenes SQL/RAM, incluida persistencia Cockroach nativa.
El bundle refuerza completitud y correspondencia entre reglas/citas y propone
comprobar identidades aritmeticas antes de emitir. Es una mitigacion del productor,
no un verificador semantico determinista ni garantia universal; la evidencia real
de cada revision determina lo aceptado. Multiplicidad sigue fail-closed y requiere
una decision explicita de protocolo o proveedor; no se cambia el contrato aqui.
