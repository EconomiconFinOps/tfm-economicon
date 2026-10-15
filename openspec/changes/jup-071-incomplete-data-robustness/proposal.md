JUP: JUP-071
Trello: https://trello.com/c/H0woDubz

## Why

La tarjeta pide comprobar cómo responde el agente cuando faltan tags o hay costes compartidos, para conocer sus limitaciones. JUP-069 aporta preguntas con rúbrica y JUP-070 permite recoger y evaluar respuestas, pero sus ejecuciones no constituyen una evaluación específica de robustez. Hace falta contrastar variantes incompletas o ambiguas con casos de referencia, conservar los fallos y separar la plantilla actual, los dobles de prueba y un modelo real.

El trabajo parte de la contribución de Alejandro Aguado (PR #90, cerrado sin integrar el 2026-10-10) y se recuperó sobre `develop` el 2026-10-13. Esa contribución se escribió cuando el chat era una plantilla sin modelo; desde entonces `develop` integró el chat generativo de JUP-035 entrega A (#130, desactivado por defecto y servido por otra ruta) y el equipo publicó un colector independiente de solo lectura para ese chat (JUP-123, PR #131). El alcance de este change se ha ajustado a esa realidad.

## What Changes

- Una batería propia y versionada de 16 variantes significativas, vinculadas a 13 casos existentes de JUP-069 (29 casos con los baselines, que no se duplican). Incluye tags ausentes, nulos, vacíos o contradictorios, costes compartidos sin regla suficiente, denominadores, periodos y unidades ambiguos, e ingesta parcial, y controles con respuesta suficiente para no premiar la abstención universal. Las cifras esperadas pueden declarar sus alias.
- Un adaptador `tools/assistant-robustness.py` que reutiliza funciones de JUP-070 para prompts, recogida HTTP y comprobación numérica. Valida el banco, la metodología, las fuentes y la propia estructura de la batería (tipos, versión, riesgo, alias) antes de ejecutar y falla con un error controlado.
- Ejecución offline del servicio real de plantilla con recuperación sustituida por un doble explícito, y recogida contra el chat HTTP de mensajes mediante el contrato existente, sin reintentos ni filtrado de respuestas desfavorables.
- Hoja y puntuación de revisión: comportamiento, puntos requeridos y prohibiciones se juzgan por personas; cifras por las reglas numéricas reutilizadas, donde los rivales de una cifra son los alias de las demás. Faltar un juicio deja el caso `not_run`; no se inventan revisores ni aprobaciones. El modo provisional marca la cobertura reducida de cada caso y deja la evaluación incompleta.
- Resultados sin texto de respuestas y un informe por grupo, tipo de perturbación y categoría que conserva `pass`, `fail`, `blocked` y `not_run`, sus denominadores, las dos tasas y el nivel de evidencia. El Markdown muestra el total previsto, las tasas, los denominadores no disponibles y la cobertura reducida.
- Un bloque `run` en el informe con los nombres de la cabecera de JUP-070 y un identificador de ejecución, para que un consumidor posterior (dashboard de JUP-121) compare ejecuciones. Acepta la descripción de seis cadenas del colector de JUP-123.
- Límites de seguridad de las salidas: el material crudo y las hojas se escriben fuera del repositorio, dentro solo se admiten los informes generados de `docs/evidence`, y se rechazan rutas de red, prefijos extendidos de Windows y destinos que sobrescriban entradas, referencias o código.
- Metodología, pruebas y evidencia por criterio. La integración generativa de JUP-035 y las tres campañas con modelo quedan como verificación pendiente, no como entregable de este change.

Fuera de alcance: modificar las reglas FinOps del producto, corregir el chat de JUP-035, cambiar el banco JUP-069 o el evaluador JUP-070 (sus limitaciones heredadas se registran en `openspec/findings/backlog.md`), escribir el colector de `/generations` o el ejecutor de campañas (JUP-123), construir el dashboard (JUP-121), asignar resultados humanos, probar Azure real o deducir calidad generativa de una plantilla, de un modelo simulado o de embeddings reales.

## Capabilities

### New Capabilities

- `assistant-robustness-evaluation`: preparación, recogida, revisión y evidencia reproducible de respuestas a datos incompletos o ambiguos, con separación del nivel de ejecución.

### Modified Capabilities

Ninguna. Se consumen los contratos existentes de JUP-069 y JUP-070; la nueva evaluación no modifica sus baterías, métricas ni umbrales.

## Impact

- Nuevo adaptador y pruebas bajo `tools/` y `scripts/tests/`, y dos scripts en `package.json` y en el flujo de CI.
- Nueva batería y metodología en `docs/validation/`, evidencia en `docs/evidence/` y continuidad en `docs/continuidad/`.
- El banco JUP-069, sus fuentes y sus baselines conservan su contenido e identificadores originales. Las referencias de la batería a su versión y a los hashes del banco, la metodología y las fuentes se actualizan cuando `develop` los cambia, tras comprobar que las preguntas y las reglas que usan las variantes siguen vigentes.
- No requiere infraestructura ni credenciales para validar la batería, ejecutar la plantilla offline o probar el instrumento.
- La evaluación generativa depende de que el chat realmente ejecute un modelo, de un colector de `/generations` (JUP-123) y de un presupuesto de inferencia acordado. La mera presencia de un alias en una ficha no lo demuestra, y un modelo simulado solo prueba el transporte y el formato.
- La entrega técnica puede quedar revisable mientras siguen pendientes los juicios humanos, la validación independiente y la medición generativa. No cambia los roles ni el estado operativo de Trello por inferencia.
