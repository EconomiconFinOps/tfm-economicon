# Anexo: barrido de troceado de la calibracion de recuperacion (JUP-022)

Medido el 2026-10-03 con el modelo real (`economicon-embedding`, 1536 dimensiones) y las 28 preguntas del banco JUP-069 con las etiquetas por seccion de `docs/validation/JUP-022-retrieval-labels.json`. Cada fila usa un tamano y un solapamiento de fragmento distintos; el resto de condiciones es igual que en el [informe principal](JUP-022-retrieval-calibration.md). Todas las cifras son con `top_k` 4.

Reproducir una fila: `tools/retrieval-calibration.py --provider litellm --chunk-size 500 --chunk-overlap 100 --top-k 4 --max-distance none 0.6 0.65` con el gateway y la clave virtual descritos en el informe.

| Tamano / solape | Fragmentos | Distancia maxima | Acierto por documento | Acierto por seccion | Vacios (answer) | Vacios (clarify y abstain) |
| --- | --- | --- | --- | --- | --- | --- |
| 300 / 50 | 91 | sin umbral | 100% | 80% | 0% | 0% |
| 300 / 50 | 91 | 0.55 | 85% | 60% | 15% | 25% |
| 300 / 50 | 91 | 0.6 | 90% | 70% | 10% | 0% |
| 300 / 50 | 91 | 0.65 | 100% | 80% | 0% | 0% |
| 500 / 50 | 52 | sin umbral | 95% | 75% | 0% | 0% |
| 500 / 50 | 52 | 0.55 | 65% | 45% | 20% | 50% |
| 500 / 50 | 52 | 0.6 | 90% | 70% | 5% | 0% |
| 500 / 50 | 52 | 0.65 | 95% | 75% | 0% | 0% |
| 500 / 100 | 58 | sin umbral | 95% | 90% | 0% | 0% |
| 500 / 100 | 58 | 0.55 | 65% | 60% | 25% | 38% |
| 500 / 100 | 58 | 0.6 | 85% | 80% | 10% | 0% |
| 500 / 100 | 58 | 0.65 | 95% | 90% | 0% | 0% |
| 800 / 100 | 34 | sin umbral | 100% | 75% | 0% | 0% |
| 800 / 100 | 34 | 0.55 | 70% | 40% | 20% | 38% |
| 800 / 100 | 34 | 0.6 | 85% | 60% | 15% | 25% |
| 800 / 100 | 34 | 0.65 | 100% | 75% | 0% | 0% |
| 1200 / 150 | 22 | sin umbral | 100% | 60% | 0% | 0% |
| 1200 / 150 | 22 | 0.55 | 50% | 30% | 45% | 62% |
| 1200 / 150 | 22 | 0.6 | 75% | 45% | 20% | 50% |
| 1200 / 150 | 22 | 0.65 | 90% | 55% | 10% | 0% |

## Lectura y limites

- Los fragmentos grandes (1200 / 150) empeoran claramente el acierto por seccion porque mezclan temas; 300 / 50 y 500 / 100 son los mejores.
- Hay 20 casos `answer`: cada 5 puntos equivalen a una pregunta, asi que las diferencias pequenas son una senal y no una prueba.
- El acierto por seccion depende del tamano del fragmento (cada fragmento se asigna a la seccion que cubre mas de su texto), por lo que no es comparable al cien por cien entre tamanos.
- Una distancia maxima de 0.6 a 0.65 aguanta en todos los tamanos medidos; el umbral por defecto no depende mucho del troceado.
- Cambiar el troceado de la ingesta es una decision del processor y obliga a reindexar; ver el finding RF-022-002.
