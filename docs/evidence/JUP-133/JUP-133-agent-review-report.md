# JUP-133 — Revisión de las seis repeticiones con juez IA

**Provisional. Un juez automatizado; cero personas revisoras y ninguna campaña aceptada.**

El 23/10/2026 el usuario autorizó sustituir la revisión pendiente por un agente. Se leyeron individualmente las 158 respuestas finales disponibles, con su pregunta, contexto, rúbrica y evidencia. Las 13 operaciones sin respuesta verificable siguen bloqueadas; no se generaron sustitutas. Los 12 fragmentos únicos se leyeron completos, deduplicando sólo la documentación, nunca los juicios de respuestas.

**720 puntos semánticos: 618 pass y 102 fail.** Esto cubre todos los criterios aplicables a las 158 respuestas disponibles, no el 100 % de las 171 operaciones previstas. Las decisiones incluyen behavior y prohibiciones suplementarias de JUP-070, que su instrumento no consume; se agregan aparte.

| Campaña | Rep. | Revisadas / previstas | Criterios | Pass casos | Fail casos | Bloqueados |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| jup070-a | 1 | 27/28 | 107 | 13 | 14 | 1 |
| jup070-a | 2 | 25/28 | 98 | 8 | 17 | 3 |
| jup070-a | 3 | 25/28 | 101 | 12 | 13 | 3 |
| jup071 | 1 | 27/29 | 138 | 11 | 16 | 2 |
| jup071 | 2 | 26/29 | 132 | 9 | 17 | 3 |
| jup071 | 3 | 28/29 | 144 | 7 | 21 | 1 |

Los estados de caso combinan el juicio del agente con las reglas numéricas originales. Se conservan sus falsos negativos conocidos; no se cambiaron resultados para mejorar la puntuación. No quedan respuestas disponibles sin revisar.

## Indicadores semánticos de robustez

| Indicador | Rep. 1 | Rep. 2 | Rep. 3 |
| --- | ---: | ---: | ---: |
| Prohibiciones concretas incumplidas | 0.0% (0/59) | 0.0% (0/56) | 0.0% (0/62) |
| Requeridos cumplidos | 71.2% (37/52) | 68.0% (34/50) | 68.5% (37/54) |
| Conducta esperada | 63.0% (17/27) | 61.5% (16/26) | 53.6% (15/28) |
| Petición de datos faltantes | 41.2% (7/17) | 31.2% (5/16) | 27.8% (5/18) |
| Abstención excesiva según rúbrica | 10.0% (1/10) | 10.0% (1/10) | 10.0% (1/10) |
| Degradación de parejas elegibles | 66.7% (4/6) | 71.4% (5/7) | 50.0% (1/2) |

Una tasa nula de prohibiciones incumplidas se limita a la lista concreta de la rúbrica: no significa cero alucinaciones ni ausencia de otros errores. El juez encontró errores adicionales de interpretación y cálculo fuera del alcance exacto de algunos puntos; sus notas quedan en el expediente privado. Petición de datos usa puntos mixtos de la rúbrica y degradación sólo parejas con referencia pass; esta última también hereda los fallos del lector numérico.

## Procedencia, cálculo y límites

- Los juicios quedan fuera de Git y ligados por hash al crudo exacto. Sólo se publican informes agregados y rows-v1. Cada punto tiene una sola identidad de agente; no se simulan dos personas.
- Las 504 filas nuevas llevan prefijo `agent_` en grupo y métrica, y `judgment=automatic`. Se conservan las filas originales, incluidas las humanas `not_measured`; los nuevos paneles se titulan «Juez IA». Así no se mezclan series ni se atribuye revisión humana.
- JUP-070: el calculador oficial continúa bloqueado por su contrato de capturas. El suplemento deriva únicamente métricas calculables, con denominadores explícitos. Los tiempos total/completadas vienen de la operación; no se rellenan tiempos de etapas.
- REL-1 y REL-2 se derivan de artifact_uri y los tramos de sección congelados tras comprobar igualdad exacta del contenido de cada fragmento. REL-2 considera todas las secciones presentes, en vez de la primera cabecera de la proyección antigua; no se presenta como reproducción de aquel método.
- Distancias de recuperación, disponibilidad HTTP, contrato de salida estructurada, clasificación de fallos y tiempos por etapa siguen `not_measured` cuando falta evidencia. Un agente no puede reconstruir esas mediciones.
- Identidad del modelo generador declarada, no atestiguada. Un único juez IA puede equivocarse y no equivale a consenso independiente ni aceptación de campaña.

## Coste y publicación

No se hicieron llamadas nuevas al gateway de Júpiter: coste adicional de la demo **0 USD**. Se conservan los costes por repetición de la [recogida original](JUP-133-infra-comparison-report.md), las cuotas, accesos y el tope de 10 USD. El coste del agente de Codex **no está medido** y no se afirma que sea gratuito.

Carga autorizada expresamente y ejecutada en DockerDevelop el **23/10/2026 a las 17:24 UTC (19:24 París)**: **23 ejecuciones / 1788 resultados**. La comprobación por contenido exacto confirmó las **1284 filas previas intactas** y las **504 nuevas**; sólo cambió el hash del informe de las seis ejecuciones ampliadas. La transacción protegió la instantánea con bloqueo y abortado ante diferencias. Las **29 consultas de Grafana respondieron sin error**; los tres paneles nuevos devolvieron 6, 6 y 35 filas. La revisión del navegador confirmó las seis repeticiones, los rótulos «Juez IA», la comparación de robustez y «No medido» donde falta evidencia. Captura privada: `agent-review/grafana-agent-review.jpg`. DockerServer no se modificó.

[Informe agregado JSON](JUP-133-agent-review-report.json) · [Carga verificada](JUP-133-agent-load-report.json). Los seis informes `JUP-133-infra-*-r*-agent-report.json` contienen fórmulas implícitas en numeradores/denominadores, huellas y filas agregadas.

Comprobación offline posterior: el contrato oficial `python tools/evaluation-dashboard.py rows` produce **18 ejecuciones / 1670 resultados** versionados; las cinco ejecuciones adicionales de runtime se conservan sólo en la base de demo. La conciliación comprueba los seis hashes de juicios sellados, agregados, 504 filas nuevas, igualdad con el paquete cargado y conservación de las filas originales. Higiene del repositorio y `git diff --check` conformes. No se repitieron pruebas de producto ni se acredita aceptación: los bloqueos de CI y regresión ya documentados en el informe de recogida continúan pendientes.

Expediente privado: `materiales/07-evidencias/JUP-133-campanas-infra-20261023/agent-review/` del workspace; `coverage-total.json`, `methodology.md`, seis juicios y comprobaciones. No se incorpora ese expediente a Git.
