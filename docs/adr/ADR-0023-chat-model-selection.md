# ADR-0023: Configuración de evaluación del chat B

- Estado: Proposed
- Fecha de revisión: 2026-10-17
- Producto: [JUP-123](https://trello.com/c/TqtcumIN)
- Memoria y evaluación: JUP-063 / JUP-109
- Change: [jup-123-chat-semantic](../../openspec/changes/archive/2026-10-17-jup-123-chat-semantic/design.md)
- Antecedente: [ADR-0002](ADR-0002-litellm-openrouter.md), sin sustituir.

## Contexto comprobado

La N5 histórica de `f3ec760d3c483e8798df2be32ea90bb901ebe36d` produjo
140 respuestas conformes y 825 comprobaciones PASS sobre el banco conocido.
Se empleó para corregir el sistema: no mide generalización, evaluación ciega ni
superioridad del modelo. CoreWeave FP8 corresponde a campañas anteriores;
la configuración del gateway de esta N5 restringía DeepSeek V4.1 Flash a
**DeepInfra FP8**. No hay traza independiente del proveedor upstream.

La auditoría de PR140 distingue dos capas que antes se confundían:

| Capa | Configuración comprobada |
| --- | --- |
| Processor congelado f3ec760d | `economicon-chat`, temperatura 0, `reasoning={effort: high, exclude: true}`, `provider.order=[deepinfra/fp4]`, sin fallback ni retries locales. |
| Gateway aislado N5 | `openrouter/deepseek/deepseek-v4.1-flash`, `provider.only=[deepinfra/fp8]`, ZDR, recopilación denegada, sin fallback y `reasoning.enabled=false`. |
| Gateway de ejemplo del repositorio | GLM-5.2 por DeepInfra FP4; no reproduce esa ruta N5. |

No se ha demostrado qué combinación de esos campos llegó finalmente a OpenRouter
ni qué razonamiento interno ejecutó el proveedor. `exclude=true` no desactiva
el razonamiento interno. Se retira la afirmación anterior de «razonamiento
desactivado» como propiedad observada de las 140 respuestas. Los hashes identifican
peticiones; no permiten recuperar su cuerpo. Los comprobantes conservan 289 hashes
de fase (145 draft, 144 final), incluidos intentos previos, para 139 operaciones;
008-r5 no tiene ese informe. Los costes desconocidos y reservas siguen intactos.

## Decisión propuesta

Conservar **DeepSeek V4.1 Flash / DeepInfra FP8 como configuración histórica del
gateway de la N5**, con las diferencias de forwarding anteriores expresas. No
presentar CoreWeave como ruta final ni afirmar equivalencia con el gateway de
ejemplo. La reproducción requiere el clon aislado y la configuración exacta
externa; el repositorio por sí solo no reproduce la medición histórica.

[Configuración sin secretos](../evidence/JUP-123-n5-gateway.sanitized.json),
[procedencia por operación y fase](../evidence/JUP-123-n5-request-provenance.json)
y [auditoría y límites](../evidence/JUP-123-victor-corrections.md) identifican el
original `gateway.private.json`, SHA256
`592674dfeaf2ec184ba580af99a820226c327bd1f920c59297bb721d3a4b3044`.
Las credenciales son referencias de entorno; este artefacto no es una orden de
despliegue ni una prueba del payload efectivo upstream.

## Consecuencias y antecedentes

La propuesta sigue pendiente de ratificación. No cambia el gateway compartido,
los campos del producto, las claves, el ledger ni activa B. Nuevos cambios de
producto se verifican por SHA con pruebas offline; no heredan una N5 del código
anterior. Una medición nueva o una captura de tráfico efectiva requieren su
propia autorización y presupuesto, ausentes de esta corrección.

El análisis histórico GLM/DeepSeek y CoreWeave permanece en
[JUP-063](../evidence/JUP-063-model-selection.md) y en el informe local. Esas
campañas mantienen sus identidades y no sustituyen esta auditoría.
