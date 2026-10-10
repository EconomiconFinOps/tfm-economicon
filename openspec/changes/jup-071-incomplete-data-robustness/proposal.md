JUP: JUP-071
Trello: https://trello.com/c/H0woDubz

## Why

La tarjeta pide comprobar cómo responde el agente cuando faltan tags o hay costes compartidos, para conocer sus limitaciones. JUP-069 aporta preguntas con rúbrica y JUP-070 permite recoger y evaluar respuestas, pero sus ejecuciones no constituyen una evaluación específica de robustez. Hace falta contrastar variantes incompletas o ambiguas con casos de referencia, conservar los fallos y separar la plantilla actual, los dobles de prueba y un modelo real.

## What Changes

- Una batería propia y versionada de al menos 16 variantes significativas, vinculadas a casos existentes de JUP-069, con los baselines originales sin duplicar. Incluye tags ausentes o contradictorios, costes compartidos sin regla suficiente, importes o periodos ambiguos y cobertura de datos incompleta.
- Un adaptador `tools/assistant-robustness.py` que reutiliza funciones de JUP-070 para prompts, recogida HTTP y comprobación numérica. Valida la referencia de la batería y las fuentes antes de ejecutar.
- Ejecución offline del servicio real de plantilla con recuperación sustituida por un doble explícito, y recogida contra el chat HTTP mediante el contrato existente, sin reintentos ni filtrado de respuestas desfavorables.
- Hoja y puntuación de revisión: comportamiento, puntos requeridos y prohibiciones se juzgan por personas; cifras por las reglas numéricas reutilizadas. Faltar un juicio deja el caso `not_run`; no se inventan revisores ni aprobaciones.
- Resultados sin texto de respuestas y un informe por grupo que conserva `pass`, `fail`, `blocked` y `not_run`, sus denominadores y el nivel de evidencia. Las tres repeticiones con modelo y configuración iguales quedan como requisito de medición final.
- Metodología, pruebas y evidencia por criterio, con la integración generativa de JUP-035 pendiente de comprobación cuando no la pruebe el runtime medido.

Fuera de alcance: modificar las reglas FinOps del producto, corregir el chat de JUP-035, cambiar el banco JUP-069 o el evaluador JUP-070, asignar resultados humanos, probar Azure real o deducir calidad generativa de una plantilla o de embeddings reales.

## Capabilities

### New Capabilities

- `assistant-robustness-evaluation`: preparación, recogida, revisión y evidencia reproducible de respuestas a datos incompletos o ambiguos, con separación del nivel de ejecución.

### Modified Capabilities

Ninguna. Se consumen los contratos existentes de JUP-069 y JUP-070; la nueva evaluación no modifica sus baterías, métricas ni umbrales.

## Impact

- Nuevo adaptador y pruebas bajo `tools/` y `scripts/tests/`.
- Nueva batería y metodología en `docs/validation/`, evidencia en `docs/evidence/` y continuidad en `docs/continuidad/`.
- El banco JUP-069, sus fuentes y sus baselines conservan su contenido e identificadores originales.
- No requiere infraestructura ni credenciales para validar la batería, ejecutar la plantilla offline o probar el instrumento.
- La evaluación generativa depende de que el chat realmente integre y ejecute un modelo en JUP-035 y de disponer de su configuración verificada. La mera presencia de un alias en una ficha no lo demuestra.
- La entrega técnica puede quedar revisable mientras siguen pendientes los juicios humanos, la validación independiente y la medición generativa. No cambia los roles ni el estado operativo de Trello por inferencia.
