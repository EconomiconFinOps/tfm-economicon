# Calibracion de la recuperacion (JUP-022)

Generado: 2026-10-13T15:09:16.882156+00:00. Proveedor: `litellm`, alias `economicon-embedding`, dimension 1536.
Banco: docs/validation/JUP-069-questions.json v1.0.1. Troceado: 500 caracteres con solape 50 (62 fragmentos). Llamadas previstas: 90.

## Regla de seleccion

Para cada top_k, la menor distancia maxima del barrido que conserva al menos 90% del acierto por seccion de los casos 'answer' obtenido sin umbral; no usa los casos clarify ni abstain.

## Candidatos

| top_k | Distancia maxima | Acierto por seccion | Resultados vacios |
| --- | --- | --- | --- |
| 3 | 0.6 | 75% | 0% |
| 4 | 0.6 | 75% | 0% |
| 5 | 0.6 | 75% | 0% |
| 6 | 0.6 | 75% | 0% |

## Barrido (casos answer)

| top_k | Distancia maxima | Acierto por documento | Acierto por seccion | Vacios | Casos clarify/abstain: documento | Casos clarify/abstain: vacios |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | sin umbral | 95% | 80% | 0% | 75% | 0% |
| 3 | 0.5 | 55% | 45% | 45% | 12% | 75% |
| 3 | 0.55 | 80% | 65% | 10% | 12% | 50% |
| 3 | 0.6 | 90% | 75% | 0% | 75% | 0% |
| 3 | 0.65 | 95% | 80% | 0% | 75% | 0% |
| 3 | 0.7 | 95% | 80% | 0% | 75% | 0% |
| 3 | 0.75 | 95% | 80% | 0% | 75% | 0% |
| 4 | sin umbral | 95% | 80% | 0% | 75% | 0% |
| 4 | 0.5 | 55% | 45% | 45% | 12% | 75% |
| 4 | 0.55 | 80% | 65% | 10% | 12% | 50% |
| 4 | 0.6 | 90% | 75% | 0% | 75% | 0% |
| 4 | 0.65 | 95% | 80% | 0% | 75% | 0% |
| 4 | 0.7 | 95% | 80% | 0% | 75% | 0% |
| 4 | 0.75 | 95% | 80% | 0% | 75% | 0% |
| 5 | sin umbral | 95% | 80% | 0% | 88% | 0% |
| 5 | 0.5 | 55% | 45% | 45% | 12% | 75% |
| 5 | 0.55 | 80% | 65% | 10% | 12% | 50% |
| 5 | 0.6 | 90% | 75% | 0% | 88% | 0% |
| 5 | 0.65 | 95% | 80% | 0% | 88% | 0% |
| 5 | 0.7 | 95% | 80% | 0% | 88% | 0% |
| 5 | 0.75 | 95% | 80% | 0% | 88% | 0% |
| 6 | sin umbral | 95% | 80% | 0% | 88% | 0% |
| 6 | 0.5 | 55% | 45% | 45% | 12% | 75% |
| 6 | 0.55 | 80% | 65% | 10% | 12% | 50% |
| 6 | 0.6 | 90% | 75% | 0% | 88% | 0% |
| 6 | 0.65 | 95% | 80% | 0% | 88% | 0% |
| 6 | 0.7 | 95% | 80% | 0% | 88% | 0% |
| 6 | 0.75 | 95% | 80% | 0% | 88% | 0% |

## Huecos del corpus (sin cobertura)

- JUP-069-024
- JUP-069-026

## Separacion por caso (mejor fragmento esperado frente al mejor de los demas)

| Caso | Tipo | Cobertura | Esperado | Otros |
| --- | --- | --- | --- | --- |
| JUP-069-001 | answer | partial | 0.5699 | 0.5172 |
| JUP-069-002 | answer | partial | 0.6096 | 0.5864 |
| JUP-069-003 | clarify | direct | 0.5627 | 0.5766 |
| JUP-069-004 | answer | direct | 0.4483 | 0.4287 |
| JUP-069-005 | answer | direct | 0.4891 | 0.5468 |
| JUP-069-006 | answer | direct | None | 0.4409 |
| JUP-069-007 | answer | direct | None | 0.4413 |
| JUP-069-008 | clarify | direct | None | 0.3658 |
| JUP-069-009 | clarify | direct | 0.6255 | 0.5683 |
| JUP-069-010 | answer | direct | 0.3825 | 0.388 |
| JUP-069-011 | answer | direct | 0.4631 | 0.4013 |
| JUP-069-012 | answer | direct | 0.3316 | 0.3815 |
| JUP-069-013 | answer | direct | 0.5688 | 0.5892 |
| JUP-069-014 | answer | direct | 0.5471 | 0.5435 |
| JUP-069-015 | answer | direct | 0.5113 | 0.5118 |
| JUP-069-016 | answer | direct | 0.3546 | 0.4446 |
| JUP-069-017 | answer | direct | 0.4429 | 0.4836 |
| JUP-069-018 | answer | direct | 0.4795 | 0.5008 |
| JUP-069-019 | clarify | partial | 0.672 | 0.5242 |
| JUP-069-020 | answer | direct | 0.5318 | 0.5407 |
| JUP-069-021 | answer | direct | 0.6264 | 0.5288 |
| JUP-069-022 | answer | direct | 0.5483 | 0.56 |
| JUP-069-023 | abstain | direct | 0.5056 | 0.4193 |
| JUP-069-024 | clarify | none | None | 0.5532 |
| JUP-069-025 | abstain | direct | 0.6196 | 0.5553 |
| JUP-069-026 | clarify | none | None | 0.5319 |
| JUP-069-027 | answer | direct | 0.5994 | 0.5126 |
| JUP-069-028 | answer | direct | 0.3994 | 0.5594 |

## Limites

- Hay pocos documentos y pocas preguntas: es una calibracion inicial y el umbral puede sobreajustarse a este corpus.
- El tope de llamadas cuenta las llamadas previstas; si el proveedor reintenta ante fallos transitorios, el gasto real puede ser hasta (reintentos + 1) veces mayor.
- Las distancias son de un solo modelo y alias; un cambio de modelo exige repetir la medicion.
- Cada fragmento se asigna a la seccion que cubre mas de su texto: una seccion mas corta que un fragmento puede no ser la principal de ninguno y quedar sin acierto por seccion aunque su contenido se recupere (el acierto por documento no tiene este efecto).
- Los casos sin cobertura son huecos del corpus: se listan aparte y no cuentan en el acierto por seccion.
- Los casos clarify y abstain se miden aparte y no intervienen en la seleccion del umbral.
- La medicion es en memoria; el orden y el filtro SQL reales se cubren con los tests contra pgvector.
