JUP: JUP-035
Trello: https://trello.com/c/BJfABykd

## Why
PR121 corrige la interacción conversacional de PR120 y los fallos de multiplicidad,
fundamentación, cálculo y recuperación observados durante la validación. Los
protocolos auto-documentation-v2 y decision none/search son antecedentes
sustituidos; sus ensayos negativos se conservan, no acreditan aceptación actual.

## What Changes
- Contrato vigente server-documentation-v4: una recuperación documental gobernada
  por servidor, un plan privado acotado y una respuesta revisada incremental;
  dos generaciones como máximo, que sustituyen la decisión previa de una.
- Expresiones privadas tipadas, ligadas a cantidades de usuario o documentos
  autenticados; cálculo Decimal local y proyección al FinOpsResponse público.
- Citas con extractos literales verificados y fuente visible para cantidades
  documentales usadas. La pertinencia y selección de operandos requieren evaluación.
- Política chat separada de ingesta, esquema privado consistente con autoridad
  financiera y razonamiento high/exclude dentro de la salida máxima conjunta
  de3200tokens por intento (1000plan/2200final), plazo120s compartido.
- Preservar aislamiento, HMAC, plazo, cancelación, JSONB y equivalencia SSE/final.
- Reconciliar develop con anomalías reales y migración compatible de los dos
  esquemas históricos 002, sin modificar registros ni datos ya aplicados.

## Impact
Backend, processor, interfaz y especificación conversational-web-interface.
Los hashes requieren despliegue coordinado en el entorno aislado de validación.
El objetivo autorizado incluye corrección, publicación de la rama y validación
real con datos sintéticos, con límite acumulado actual de 2 USD. No autoriza
fusionar la PR ni publicar mensajes en Discord.

La batería completa y el navegador deben evaluarse sobre el candidato final.
CI verde, aritmética local y ensayos históricos no sustituyen aceptación semántica.
La documentación de diseño conserva las decisiones y limitaciones del protocolo.


### Delta29 vigente, validación real pendiente

Supersede la selección de evidencia raíz por extractos literales visibles por
fuente efectiva e interpretaciones separadas. Auxiliares y recomendaciones usan
los mismos segmentos; se proyectan sólo fuentes usadas, sin citas decorativas.
El plan añade cobertura/riesgos pertinentes sin imponerlos a saludos/aritmética.
Se conservan2generaciones1000/2200,120s y contrato público. Literalidad no demuestra
pertinencia ni entailment; el banco original y revisión semántica siguen exigidos.
Véase revisión29 del ADR JUP-035-server-retrieval-expressions.md.
