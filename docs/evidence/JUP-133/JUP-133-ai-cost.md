# Coste de IA por consulta (JUP-130)

Medición de JUP-133 sobre la ventana 2026-10-21 a 2026-10-22 (inicio incluido, fin excluido, en UTC). Comando: `python tools/memory-indicators.py ai-cost --from 2026-10-21 --to 2026-10-22`. Con `--run-at` y `--commit` se fijan la fecha y el commit del informe.

| Medida | Valor |
| --- | --- |
| Consultas de chat terminadas | 75 |
| Coste estimado por el gateway | 0,049456 USD |
| Coste facturado (OpenRouter, solo confirmadas) | 0,049765 USD |
| Coste facturado por consulta | 0,000664 USD |
| Diferencia estimado menos facturado | -0,000309 USD |
| Cobertura de lo facturado | 100,0 % (75/75) |
| Consultas con gasto estimado cero | 1 |
| Embeddings (solo estimado, aparte) | 0,000068 USD |
| Rechazos 429 del gateway | 0,0 % (0/124) |
| Errores del proveedor (5xx) | 0,0 % (0/124) |

## Por modelo

| Modelo | Consultas | Facturado por consulta |
| --- | --- | --- |
| openrouter/deepseek/deepseek-v4.1-flash | 73 | 0,000596 USD |
| openrouter/z-ai/glm-5.2 | 2 | 0,003139 USD |

## Qué no demuestra

- El gasto es local a la máquina que ejecutó las consultas: no demuestra el coste de un uso real ni de otros equipos.
- El coste estimado es contabilidad derivada de una tarifa por token, no una factura; solo lo confirmado por OpenRouter es facturado.
- Una consulta que OpenRouter no devuelve no se cuenta como coste cero: reduce la cobertura.
- Los embeddings no llevan identificador de generación de OpenRouter y por eso se informan aparte como estimados.
- Los rechazos 429 son del límite por clave del propio gateway y no del proveedor; el coste de pruebas no es el de producción.
