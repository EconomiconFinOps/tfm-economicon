# ADR-0025: Configuración de evaluación del chat B

- Estado: Accepted (ratificación documental por excepción humana, 2026-10-18)
- Fecha de revisión técnica histórica: 2026-10-17
- Fecha de regularización y ratificación documental: 2026-10-18
- Producto: [JUP-123](https://trello.com/c/TqtcumIN)
- Memoria y evaluación: JUP-063 / JUP-109
- Change: [jup-123-chat-semantic](../../openspec/changes/archive/2026-10-17-jup-123-chat-semantic/design.md)
- Antecedente: [ADR-0002](ADR-0002-litellm-openrouter.md), sin sustituir.

## Procedencia y alcance de la aceptación

El 18/10/2026, en HAL 9000 (`01a1270c-e332-7462-9c90-706d49ade92c`),
el usuario autorizó expresamente: «Autorizo encargárselo a nuestros agentes
como excepción: publicar la comparativa GLM/DeepSeek, incorporarla a Grafana y
regularizar el ADR-0023. Avísale a Lucía por Discord y no toques la PR63».
La regularización ratifica **el registro documental de la configuración histórica
ya elegida**, con sus límites; no selecciona ni despliega una nueva ruta de runtime.
Preparación de Alejandro asistido por agentes bajo esa excepción. No se atribuyen
consenso, pairing, revisión o validación nuevos a Lucía, Paris o Víctor.

Este documento se llamaba `ADR-0023-chat-model-selection.md`. Al comprobar
`develop` `6d9e6710b7306faced8f811121a757267789120f`, el número 0023 también
identificaba el [chunking determinista](ADR-0023-deterministic-document-chunking.md)
y 0024 ya estaba ocupado. El modelo pasa a **0025**, primer número libre;
la ruta anterior queda como alias de navegación, sin una segunda decisión.
No se sustituye ni ratifica el ADR de chunking, ni ADR-0002, ni las otras
colisiones históricas del registro (0013 y 0022), ajenas a este encargo.

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

## Decisión ratificada y alternativas

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

La comparación histórica GLM/DeepSeek es antecedente, no un experimento causal
de esta configuración: GLM tuvo mejor conformidad provisional en el banco
común y DeepSeek menor coste/latencia, según el informe fechado. Después cambian
candidato, corpus, recorrido y proveedor; los 429 observados en GLM motivaron la
continuación operativa con DeepSeek. No se elige GLM por una cifra aislada ni se
deduce superioridad universal de DeepSeek a partir de la N5 posterior. Mantener
GLM en el gateway compartido no reproduce esta N5; cambiarlo requiere su propia
actuación autorizada. Se conserva la alternativa de no afirmar comparabilidad
cuando faltan identidades o mediciones.

## Consecuencias y antecedentes

La ratificación documental no acredita una campaña nueva. No cambia el gateway compartido,
los campos del producto, las claves, el ledger ni activa B. Nuevos cambios de
producto se verifican por SHA con pruebas offline; no heredan una N5 del código
anterior. Una medición nueva o una captura de tráfico efectiva requieren su
propia autorización y presupuesto, ausentes de esta corrección.

El análisis histórico GLM/DeepSeek y CoreWeave permanece en
[JUP-063](../evidence/JUP-063-model-selection.md) y en la
[comparativa congelada del 16/10](../evidence/JUP-063/glm-deepseek-20261016/README.md),
publicada con su JSON original y procedencia. El replay N3 común recoge GLM-5.2 /
DeepInfra FP4 y DeepSeek V4.1 Flash / CoreWeave FP8: 82/84 y 77/84 conformes
locales provisionales, respectivamente. No es la N5 DeepInfra posterior, no mide
API/UI ni tiene adjudicación independiente. Esas campañas mantienen sus
identidades y no sustituyen esta auditoría ni aceptan el producto actual.
