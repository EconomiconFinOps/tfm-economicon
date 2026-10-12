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

El tokenizer se incorpora al construir las dos imagenes mediante el descargador
[build_tokenizer.py](../../apps/processor/build_tokenizer.py). Fuente oficial:
`zai-org/GLM-5.2`, revision `a66456a59f21345d1e5e586345c448a9106d29d7`.
SHA256: `19e773648cb4e65de8660ea6365e10acca112d42a854923df93db4a6f333a82d`.
Una discrepancia aborta la construccion. El runtime funciona sin red para ese
recurso. Cambiar modelo, revision o hash requiere una decision explicita.

## Alternativas y consecuencias

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
