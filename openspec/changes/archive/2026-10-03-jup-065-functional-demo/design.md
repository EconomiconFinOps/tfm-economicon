# JUP-065 — Preparación reproducible

[Trello](https://trello.com/c/SZUFo4ol).

## Alcance

La fuente canónica compartida pasa a `docs/demo/JUP-065/`. El paquete inicial
de entregables fuera de Git se conserva como antecedente local. No se incluyen
recibos operativos de Trello ni rutas personales en la entrega versionada.

## Decisiones

1. Fijar `de0d62e7c0028f35a81c5087f531d19031a90e81` como baseline de datos.
   `git show` lee exactamente esos objetos incluso si el checkout tiene cambios.
   CI necesita historial; los clones superficiales pueden obtener ese SHA.
2. Conservar quince archivos generados pequeños y hashes de sus fuentes, incluida
   licencia Microsoft. Permiten revisar los datos sin ejecutar una herramienta.
   No son otro corpus activo: solo `manifest.yaml` determina la carga del ensayo.
3. Calcular referencias con CSV, fechas y Decimal, sin importar código productivo.
   Intervalo UTC explícito y fin exclusivo; no usar el mes actual del dashboard.
   Comparar importes a dos decimales y grupos por clave, no por orden.
4. Exportar solo ID, contexto y pregunta en prompts; la rúbrica queda separada.
   Validar las tres conductas: respuesta, aclaración y abstención.
5. Regenerar en un temporal, comparar inventario y bytes y fallar ante diferencias.
   Las comprobaciones explícitas siguen activas bajo `python -O`.
6. Preservar roles: Alejandro liderazgo, Lucia pairing, Paris revisión, Victor
   validación. Ningún resultado automatizado acredita su participación.

## Límites y riesgos

La suma exacta CSV es una referencia; el ensayo deberá contrastar el contrato
de lectura sobre datos persistidos. No afirmar que el chat consulta billing ni
que activar un proveedor del processor conecta la ruta de conversación.
Se distinguen fixtures públicas y contexto sintético. No indexar la clave de
respuestas. El runtime y LLM permanecen `not_run` en la evidencia de esta fase.

El guion depende de integración y aceptación de retrieval/modelo/citas. La
validación ahora solicitada es offline; el ensayo definitivo se registra después
en una copia de la plantilla. Las condiciones del ensayo y sus responsables
siguen visibles aunque se acepte esta PR de preparación.
