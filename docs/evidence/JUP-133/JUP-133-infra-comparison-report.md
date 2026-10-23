# JUP-133 — Tres repeticiones por campaña en DockerDevelop

**Provisional. No se acepta ninguna campaña; no se han recibido juicios humanos.**

Se recogieron 171 operaciones en conversaciones independientes con la misma configuración: JUP-070 A, 28 × 3; JUP-071, 29 × 3. Se conservan todos los intentos y fallos; no se sustituyen respuestas.

| Campaña | Rep. | Completadas | Intentos | Mediana (s) | p95 (s) | Coste registrado (USD) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| jup070-a | 1 | 27/28 | 41 | 17.748 | 144.177 | 0.0895823920 |
| jup070-a | 2 | 25/28 | 40 | 19.487 | 148.796 | 0.0879410520 |
| jup070-a | 3 | 25/28 | 41 | 19.255 | 151.506 | 0.0902780640 |
| jup071 | 1 | 27/29 | 43 | 20.152 | 106.866 | 0.0868489344 |
| jup071 | 2 | 26/29 | 43 | 20.009 | 238.114 | 0.1001381312 |
| jup071 | 3 | 28/29 | 40 | 20.795 | 62.960 | 0.0743708712 |

Gasto nuevo: **0.5291594448 USD**. Acumulado aproximado del plan, incluyendo ≈0,077 USD previos: **0.6061594448 USD / 10 USD**. El límite global de la demo sigue siendo 10 USD; no se suma al del plan ni se reinician subcuotas.

El coste procede del registro liquidado del gateway e incluye reintentos y embeddings; no es una comprobación de factura. La latencia mide desde la solicitud de generación hasta observar su estado terminal; incluye reintentos y excluye la espera de conciliación.

Modelo declarado por configuración: `openrouter/deepseek/deepseek-v4.1-flash`, `deepinfra/fp8`; no verificado en el proveedor. Límite final observado: 10000 tokens. Corpus del tenant: cuatro documentos y doce fragmentos. El histórico usaba otra segmentación; no permite atribuir diferencias solo al modelo o a la infraestructura.

El commit del evaluador es `84b53b74`; no acredita el código desplegado. Las imágenes exactas se identifican por SHA-256 en el sello final; su etiqueta de revisión heredada no acredita los cambios posteriores. El commit del producto queda nulo en los rows-v1.

Cada repetición tiene informe y rows-v1 propios. Los juicios y tasas de calidad humana siguen `not_run` / `not_measured`. Los estados numéricos de JUP-071 son comprobaciones automáticas del lector existente y no una revisión semántica. Las operaciones fallidas quedan bloqueadas, no calificadas como respuestas incorrectas.

El calculador de JUP-070 puede quedar bloqueado cuando una operación nativa falla: exige tiempos por etapa que no están disponibles. Se conservan los estados por caso y se publican las observaciones técnicas medidas aparte; no se inventan ceros para superar su validación.

Crudos, respuestas, fichas, recibos y hojas vacías de revisión: fuera de Git, en `materiales/07-evidencias/JUP-133-campanas-infra-20261023/private-capture/` y `analysis/` del workspace. La carga fue autorizada expresamente y verificada en DockerDevelop, conservando el histórico; véase el [informe de carga](JUP-133-infra-load-report.md).

Detalles, dispersión entre repeticiones, incidencias y huellas: [informe JSON](JUP-133-infra-comparison-report.json).

## Suplemento posterior: juez IA

El usuario autorizó la revisión automatizada de las 158 respuestas disponibles, sin nuevas generaciones. [Comparación de las seis revisiones](JUP-133-agent-review-report.md): 720 puntos semánticos, 13 operaciones bloqueadas y ninguna respuesta disponible sin revisar. Carga autorizada y verificada: 504 filas adicionales, 23 ejecuciones / 1788 resultados y tres paneles «Juez IA». La revisión humana continúa sin realizarse y no se acepta ninguna campaña.
