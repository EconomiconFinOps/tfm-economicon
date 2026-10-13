# ADR-0019: Runtime del chat conversacional

- Estado: Accepted para esta entrega por Paris el 12/10/2026 al aprobar el plan.
- Alcance: JUP-035; no sustituye la revision ni la validacion humanas del proyecto.
- Fuente: [OpenSpec](../../openspec/changes/archive/2026-10-11-jup-035-conversational-web-interface/proposal.md).

## Contexto

El chat necesita autenticacion y aislamiento, generacion lenta con recuperacion
de operaciones, evidencia financiera determinista y una interfaz reutilizable.
El endpoint historico devuelve una plantilla; no demuestra el recorrido LLM.
Un tokenizer de unos 20 MB en Git aumenta cada checkout sin aportar historial
util de codigo.

## Decision

Backend conserva la autoridad de usuario, tenant, seleccion y costes. Processor
recibe un contrato privado autenticado con HMAC por la red interna de Compose.
La clave persistente se prepara localmente y en CD fuera de Git y las releases.
No se reemplaza al arrancar ni se publica en logs. HMAC no cifra el trafico:
una frontera entre hosts no confiables requeriria TLS.

El historial canonico y el resumen derivado se guardan en JSONB bajo una
conversacion perteneciente al usuario y tenant. Las operaciones usan fencing,
reintentos acotados y escritura atomica; un resumen nunca elimina originales.
La verificacion al arrancar comprueba el esquema, no interpreta historiales de
todos los tenants. Un historial corrupto queda aislado a esa conversacion.
El runtime de admision sigue siendo de un proceso; no se afirma coordinacion
horizontal ni HA. El resolvedor existente mantiene plazos acotados; esta
correccion no introduce otro servicio DNS.

La interfaz utiliza assistant-ui y los componentes del template. Se muestra
estado no accionable y evidencia de costes separada de las citas documentales.
La ruta antigua abre el panel nuevo; las plantillas historicas siguen visibles
pero se excluyen del contexto y del resumen nuevos.
Paris aprueba conservar JUP-037 en una vista especifica `/ownership` el 12/10/2026:
reutiliza el formulario y endpoint estructurados, sin generacion ficticia ni
duplicacion del chat nuevo. El evaluador sigue usando generaciones.

El tokenizer se incorpora al construir las dos imagenes mediante el descargador
[build_tokenizer.py](../../apps/processor/build_tokenizer.py). Fuente oficial:
`zai-org/GLM-5.2`, revision `a66456a59f21345d1e5e586345c448a9106d29d7`.
SHA256: `19e773648cb4e65de8660ea6365e10acca112d42a854923df93db4a6f333a82d`.
Una discrepancia aborta la construccion. El runtime funciona sin red para ese
recurso. Cambiar modelo, revision o hash requiere una decision explicita.

## Alternativas y consecuencias

## Decision adicional: recuperacion y expresiones (13/10/2026)

Paris aprueba server-documentation-v4: recuperacion unica decidida por servidor
con la pregunta canonica (2048 caracteres), seguida de una generacion final.
Sustituye auto-documentation-v2 y el experimento de calculadora nativa.
La adaptacion se limita a nuestra rama; PR #121 es referencia de solo lectura.
Fuentes de Alejandro: 0d91d337, 1b7eb148, 41e23706, 85994b86, 192b6872 y
193b785a786ab68b3b2839e5154e814571fa1319. HEAD observado: f1848e57.

El catalogo autentica valor, unidad y origen; las expresiones Decimal y los
segmentos privados se proyectan con un renderer comun al formato publico.
Se exige pasaje literal para corpus y se conservan validadores de procedencia,
aislamiento y autoridad financiera. Limites: profundidad 4, 12 operaciones,
128 cantidades, precision 40, entrada 10^12, resultado 10^18, seis decimales.
Cero es indefinido; divisas incompatibles no se agregan. No hay inferencia
reparadora ni IDs de planes de calculo. Chat separa su prompt de ingesta.

Reasoning high/exclude true conserva 3200 tokens totales y deadline vigente;
no se registra razonamiento. Puede reducir salida util: una salida vacia o
truncada detiene el ensayo, no autoriza ampliar limites automaticamente.
La recuperacion siempre ejecutada aumenta coste incluso para saludos y no
garantiza pertinencia: esta se evalua en siete focales reales nuevos.
Ver [diseño y limites](../../openspec/changes/jup-035-auto-documentation/design.md).
Las campañas anteriores no acreditan esta adaptacion.

## Alternativas del runtime

## Decision adicional: fuentes y correccion acotada (13/10/2026)

Paris aprueba vincular los segmentos documentales a evidence_ids autorizados
y pasajes literales; evidence sigue permitida para abstencion o rechazo.
El esquema privado prohibe metrics/recommendations en estados no accionables,
igual que la validacion publica. No se reparan listas borrando sus elementos.

Una correccion estructurada excepcional es autorizada solo por backend,
consume uno de los cuatro intentos y conserva el deadline del intento fallido.
Reutiliza la recuperacion autenticada en controles JSONB, sin nueva busqueda
ni cambio del contexto canonico. Una segunda correccion nunca se admite.
Solo se envian instrucciones fijas por codigo de error; no prosa rechazada.
Los fallos de seguridad y almacenamiento no se convierten en reparables.

Se mantiene progreso, pero el usuario solo recibe texto validado y persistido,
no borradores rechazados. FinOpsResponse 1.0 y las fuentes pequenas no cambian.
Este acuerdo sustituye la prohibicion anterior de inferencia reparadora solo
para los errores recuperables enumerados; no implica un juez semantico LLM.
La aceptacion focal comprueba pertinencia real; no se afirma que la literalidad
o la vinculacion de IDs detecte todas las afirmaciones semanticamente incorrectas.

## Decision adicional: clasificacion documental verificada (13/10/2026)

Paris aprueba un catalogo versionado de semaforo de coste no asignado, habilitado
exclusivamente por formula y bandas literales de un fragmento efectivo
autorizado. La huella del catalogo forma parte del contrato privado.
El modelo selecciona una expresion porcentaje y regla; el servidor calcula
sin redondear antes de clasificar, aplica limites inclusivos y publica color,
intervalo y cita. Rechaza reglas desconocidas, pasajes alterados y fuentes
no autorizadas. El renderer publica las citas propias de la regla aplicada
desde sus registros y pasajes autenticados; una cita entregada con metadatos
o pasaje invalidos se rechaza y no se reemplaza para ocultar el error.
Formula y bandas pueden estar en dos fragmentos del mismo documento.
La aclaracion de Paris del 13/10 retira el rechazo lexical de colores:
explicar o reiterar correctamente una clasificacion no invalida el MVP.
La aceptacion exige coherencia con la documentacion y no inventar datos,
sin imponer una redaccion concreta. Seleccion de operandos, contradicciones
y pertinencia general siguen requiriendo comprobacion funcional.
FinOpsResponse 1.0 y una recuperacion/generacion por intento se conservan.

El intento truncado de 006 agoto los 3200 tokens (registro del gateway:
gen-1791905760-pa83ud2SxBOPaT0IGsT2). Paris autoriza 6400 tokens de salida
para chat, incluido razonamiento. No modifica ingesta, resumen, deadline,
modelo ni ventana. Las evidencias de los intentos anteriores se conservan.

- Generacion en backend: evita un canal, pero duplica proveedor y sus permisos.
- Mantener messages como unica tabla: no conserva juntos version, orden y
  resumen canonicos; JSONB exige validar y limitar cada documento.
- UI propia desde cero: duplica primitivos de mensajes, accesibilidad y estados.
- Descarga del tokenizer al arrancar: hace depender readiness de Internet.
- Binario en Git: hace offline el checkout, pero carga el historial y la CI.

Build y preparacion inicial necesitan acceso a la fuente oficial. CI prepara
el mismo artefacto antes de pytest; su cache se valida siempre. Los ensayos
reales siguen requiriendo credenciales y presupuesto autorizado. No se relajan
los validadores para obtener resultados favorables.
