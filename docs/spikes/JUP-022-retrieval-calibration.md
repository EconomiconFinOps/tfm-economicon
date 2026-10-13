# Calibracion de la recuperacion (JUP-022)

Generado: 2026-10-03T07:15:32.826486+00:00. Proveedor: `litellm`, alias `economicon-embedding`, dimension 1536.
Banco: docs/validation/JUP-069-questions.json v1.0.0. Troceado: 500 caracteres con solape 50 (52 fragmentos). Llamadas previstas: 80.

## Regla de seleccion

Para cada top_k, la menor distancia maxima del barrido que conserva al menos 90% del acierto por seccion de los casos 'answer' obtenido sin umbral; no usa los casos clarify ni abstain.

## Candidatos

| top_k | Distancia maxima | Acierto por seccion | Resultados vacios |
| --- | --- | --- | --- |
| 3 | 0.6 | 70% | 5% |
| 4 | 0.6 | 70% | 5% |
| 5 | 0.6 | 70% | 5% |
| 6 | 0.6 | 70% | 5% |

## Barrido (casos answer)

| top_k | Distancia maxima | Acierto por documento | Acierto por seccion | Vacios | Casos clarify/abstain: documento | Casos clarify/abstain: vacios |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | sin umbral | 95% | 75% | 0% | 75% | 0% |
| 3 | 0.5 | 45% | 30% | 55% | 12% | 75% |
| 3 | 0.55 | 65% | 45% | 20% | 12% | 50% |
| 3 | 0.6 | 90% | 70% | 5% | 62% | 0% |
| 3 | 0.65 | 95% | 75% | 0% | 75% | 0% |
| 3 | 0.7 | 95% | 75% | 0% | 75% | 0% |
| 3 | 0.75 | 95% | 75% | 0% | 75% | 0% |
| 4 | sin umbral | 95% | 75% | 0% | 75% | 0% |
| 4 | 0.5 | 45% | 30% | 55% | 12% | 75% |
| 4 | 0.55 | 65% | 45% | 20% | 12% | 50% |
| 4 | 0.6 | 90% | 70% | 5% | 62% | 0% |
| 4 | 0.65 | 95% | 75% | 0% | 75% | 0% |
| 4 | 0.7 | 95% | 75% | 0% | 75% | 0% |
| 4 | 0.75 | 95% | 75% | 0% | 75% | 0% |
| 5 | sin umbral | 95% | 75% | 0% | 75% | 0% |
| 5 | 0.5 | 45% | 30% | 55% | 12% | 75% |
| 5 | 0.55 | 65% | 45% | 20% | 12% | 50% |
| 5 | 0.6 | 90% | 70% | 5% | 62% | 0% |
| 5 | 0.65 | 95% | 75% | 0% | 75% | 0% |
| 5 | 0.7 | 95% | 75% | 0% | 75% | 0% |
| 5 | 0.75 | 95% | 75% | 0% | 75% | 0% |
| 6 | sin umbral | 95% | 75% | 0% | 75% | 0% |
| 6 | 0.5 | 45% | 30% | 55% | 12% | 75% |
| 6 | 0.55 | 65% | 45% | 20% | 12% | 50% |
| 6 | 0.6 | 90% | 70% | 5% | 62% | 0% |
| 6 | 0.65 | 95% | 75% | 0% | 75% | 0% |
| 6 | 0.7 | 95% | 75% | 0% | 75% | 0% |
| 6 | 0.75 | 95% | 75% | 0% | 75% | 0% |

## Huecos del corpus (sin cobertura)

- JUP-069-024
- JUP-069-026

## Separacion por caso (mejor fragmento esperado frente al mejor de los demas)

| Caso | Tipo | Cobertura | Esperado | Otros |
| --- | --- | --- | --- | --- |
| JUP-069-001 | answer | partial | 0.5699 | 0.5393 |
| JUP-069-002 | answer | partial | 0.6096 | 0.6299 |
| JUP-069-003 | clarify | direct | 0.5632 | 0.5832 |
| JUP-069-004 | answer | direct | 0.4483 | 0.405 |
| JUP-069-005 | answer | direct | 0.4891 | 0.5468 |
| JUP-069-006 | answer | direct | None | 0.4409 |
| JUP-069-007 | answer | direct | None | 0.4411 |
| JUP-069-008 | clarify | direct | None | 0.3658 |
| JUP-069-009 | clarify | direct | 0.6255 | 0.5683 |
| JUP-069-010 | answer | direct | 0.3825 | 0.3877 |
| JUP-069-011 | answer | direct | 0.4631 | 0.4016 |
| JUP-069-012 | answer | direct | 0.3316 | 0.3815 |
| JUP-069-013 | answer | direct | 0.5826 | 0.6002 |
| JUP-069-014 | answer | direct | 0.5654 | 0.5356 |
| JUP-069-015 | answer | direct | 0.5113 | 0.5118 |
| JUP-069-016 | answer | direct | 0.5148 | 0.4446 |
| JUP-069-017 | answer | direct | 0.5537 | 0.6198 |
| JUP-069-018 | answer | direct | 0.5839 | 0.6369 |
| JUP-069-019 | clarify | partial | 0.7143 | 0.5242 |
| JUP-069-020 | answer | direct | 0.5318 | 0.5923 |
| JUP-069-021 | answer | direct | 0.6285 | 0.5017 |
| JUP-069-022 | answer | direct | 0.5483 | 0.56 |
| JUP-069-023 | abstain | direct | 0.5056 | 0.4193 |
| JUP-069-024 | clarify | none | None | 0.5462 |
| JUP-069-025 | abstain | direct | 0.6196 | 0.5553 |
| JUP-069-026 | clarify | none | None | 0.5926 |
| JUP-069-027 | answer | direct | 0.5994 | 0.5126 |
| JUP-069-028 | answer | direct | 0.3995 | 0.5595 |

## Limites

- Hay pocos documentos y pocas preguntas: es una calibracion inicial y el umbral puede sobreajustarse a este corpus.
- Las distancias son de un solo modelo y alias; un cambio de modelo exige repetir la medicion.
- Cada fragmento se asigna a la seccion que cubre mas de su texto: una seccion mas corta que un fragmento puede no ser la principal de ninguno y quedar sin acierto por seccion aunque su contenido se recupere (el acierto por documento no tiene este efecto).
- Los casos sin cobertura son huecos del corpus: se listan aparte y no cuentan en el acierto por seccion.
- Los casos clarify y abstain se miden aparte y no intervienen en la seleccion del umbral.
- La medicion es en memoria; el orden y el filtro SQL reales se cubren con los tests contra pgvector.
