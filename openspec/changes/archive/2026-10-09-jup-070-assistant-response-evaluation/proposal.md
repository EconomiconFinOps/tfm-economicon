JUP: JUP-070
Trello: https://trello.com/c/tpSyzXOS

## Why

El equipo quiere poder afirmar con evidencia que el chat responde bien y no inventa. Hoy no hay forma de medirlo: JUP-069 entregó una batería de 28 casos con rúbrica (20 `answer`, 6 `clarify`, 2 `abstain`, 14 con cifras esperadas) y dejó expresamente a JUP-070 la evaluación de las respuestas frente a esa referencia y los umbrales de aceptación. JUP-067 definió las métricas y el formato de resultados, y dice que el fichero de resultados de una ejecución lo producirá JUP-070 con un adaptador. Sin ese adaptador, la memoria no puede decir «sin alucinaciones» ni comparar el chat de hoy con el que genere JUP-035, y el freeze de la memoria es el 16/10.

## What Changes

- Una herramienta de línea de comandos, `tools/assistant-eval.py`, solo con la biblioteca estándar, con tres pasos: recoger las respuestas del chat de un stack en marcha, generar la hoja de revisión humana y puntuar la ejecución, produciendo el fichero de resultados que ya espera `tools/assistant-metrics.py`.
- Un fichero de reglas versionado, `docs/validation/JUP-070-evaluation-rules.json`, con las equivalencias de etiquetas de las cifras, los patrones de las conductas prohibidas que se pueden detectar por regla, y los umbrales de aceptación.
- Un documento de metodología, `docs/validation/JUP-070-evaluation.md`: cómo se ejecuta, qué decide la regla y qué decide una persona, la doble revisión de los casos críticos, las repeticiones, cómo se lee el veredicto y sus límites.
- Una medición de referencia del chat actual (que hoy no llama a ningún modelo), con el fichero de resultados y el informe, sin el texto de las respuestas, como «antes» para comparar con el chat que genere JUP-035.
- Pruebas sin red ni base de datos, con respuestas sintéticas buenas y malas para cada caso crítico, que comprueban las decisiones por regla, y su paso en CI.

Fuera de alcance: un juez basado en un modelo; cambiar el backend o el chat; implementar la respuesta generada por un modelo (JUP-035); nuevas preguntas o cambios de la batería; la robustez (JUP-071); métricas de negocio (JUP-068); pruebas de carga; Azure real.

## Capabilities

### New Capabilities

- `assistant-response-evaluation`: recogida de las respuestas del chat, decisión por regla de las comprobaciones objetivas, revisión humana de las demás, resultados en el formato de JUP-067 y veredicto de aceptación con umbrales.

### Modified Capabilities

Ninguna. No cambia ningún requisito de `assistant-technical-metrics` ni de la batería de JUP-069.

## Impact

- Nuevo: `tools/assistant-eval.py`, `tools/tests/` o `scripts/tests/` con su prueba, `docs/validation/JUP-070-evaluation-rules.json`, `docs/validation/JUP-070-evaluation.md`, y `docs/evidence/JUP-070-validation.md` con la medición de referencia.
- Cambios de configuración de CI y de scripts: `package.json`, `.github/workflows/ci.yml` y `tools/ci-workflow.test.mjs`.
- Documentación: enlace desde `docs/validation/README.md`, que hoy dice que la metodología queda para JUP-070.
- Sin cambios en `apps/`, en `tools/assistant-metrics.py` ni en la batería.
- Los textos de las respuestas y las hojas de revisión se guardan fuera de Git; el repositorio solo recibe resultados sin texto.
- Depende de JUP-069 y JUP-067 (hechas). La medición del chat con un modelo real depende de JUP-035 y de la clave virtual de JUP-078.
