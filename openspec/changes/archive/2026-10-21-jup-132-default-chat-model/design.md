# JUP-132: continuidad del modelo por defecto

[ADR-0026](../../../docs/adr/ADR-0026-default-chat-model.md).

El gateway ofrece sólo economicon-chat y economicon-embedding. Chat, resumen y
diagnóstico usan DeepInfra FP8 normal, sin fallback, con parámetros requeridos,
ZDR y recopilación denegada. Reasoning se desactiva explícitamente. No cambian
presupuestos de cada recorrido, plazos, concurrencia o reintentos.

Los recursos chat/summary v4 reutilizan texto/esquema de v3 y fijan el tokenizer
oficial Flash. Instalación sólo al construir/preparar. v2/v3 y su tokenizer se
conservan como lectores históricos, sin cambiar contratos/huellas existentes.
Selección por contrato exacto autenticado; las generaciones nuevas usan v4.
No se borran resúmenes ni se cambia el espacio/tokenizador de embeddings.

Los planes nuevos fijan ambos artefactos generados: tokenizer Flash v4 activo y
tokenizer v2 de los lectores anteriores. La procedencia verifica chat/summary v4
y ambos archivos en backend y processor. El conjunto de recursos del plan
congelado selecciona el contrato: los planes históricos no adquieren v4
implícitamente. Omitir o alterar un recurso activo impide su verificación.

Pruebas: alias retirado, solicitudes efectivas, diagnóstico, privacidad, conteo
Flash y lectura antigua con sus límites originales. Incompatibilidades fallan
cerradas. Catálogo del proveedor no acredita inferencia real o calidad. No se
atribuyen campañas anteriores a esta configuración ni se reescriben sus informes.
