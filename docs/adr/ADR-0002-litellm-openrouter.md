# ADR-0002: LiteLLM como gateway y OpenRouter como upstream

- Estado: Accepted (2026-10-04; ver Aceptacion)
- Fecha: 2026-08-25
- Tarjeta: [JUP-078](https://trello.com/c/M4zqDGlW)
- Decision requerida antes de: octubre de 2026

## Contexto

Economicon necesita chat y embeddings reales para evaluar su RAG, pero el codigo actual solo implementa mocks. El equipo no dispone de un tenant de Azure AI y quiere evitar que backend y processor queden acoplados a credenciales, catalogos y politicas de un proveedor externo.

Trello recoge LiteLLM + OpenRouter y la seleccion de GLM-5.2 y DeepSeek. El
benchmark autenticado ya esta disponible, pero muestra limites de latencia y
un timeout de DeepSeek, y todavia no existe una aprobacion verificable de los
cuatro miembros. Esta propuesta permanece `Proposed` hasta su revision conjunta.

Alejandro establecio GLM-5.2 y DeepSeek como modelos de chat. Para hacer la
configuracion reproducible se fija la variante vigente
`deepseek/deepseek-v4-pro`; si el equipo acuerda otra variante DeepSeek, debera
cambiarse explicitamente antes del benchmark. El 25 de agosto de 2026 se
verificaron los tres IDs contra la API oficial de modelos de OpenRouter.

## Decision propuesta

Usar LiteLLM como gateway interno OpenAI-compatible y OpenRouter como unico upstream inicial.

- Los servicios usan `LITELLM_BASE_URL`, `LITELLM_API_KEY` y alias logicos.
- `economicon-chat` se mapea a `z-ai/glm-5.2` como modelo principal.
- `economicon-chat-deepseek` se mapea a `deepseek/deepseek-v4-pro` como segundo modelo de chat bajo seleccion explicita.
- `economicon-embedding` se mapea a `openai/text-embedding-3-small` con 1536 dimensiones.
- Cada alias tiene un unico despliegue; un fallo se propaga y se observa.
- El routing upstream fija expresamente `allow_fallbacks: false`.
- Los alias de chat fijan `reasoning.enabled: false` para la linea base FinOps;
  el razonamiento de alto esfuerzo queda reservado a una evaluacion explicita.
- Los mocks solo son validos en `test` y `development`; `evaluation` los rechaza.

## Catalogo y precios verificados

Consulta publica realizada el 25 de agosto de 2026 al endpoint oficial
`GET /api/v1/model/{author}/{slug}`; los precios se indican en USD por millon
de tokens y deben volver a comprobarse antes de cualquier gasto real.

| Modelo | ID OpenRouter | Contexto | Entrada / 1M | Salida / 1M |
|---|---|---:|---:|---:|
| GLM-5.2 | `z-ai/glm-5.2` | 1.048.576 | 1,19 USD | 3,74 USD |
| DeepSeek V4 Pro | `deepseek/deepseek-v4-pro` | 1.048.576 | 0,572808 USD | 1,145616 USD |
| Embeddings | `openai/text-embedding-3-small` | 8.192 | 0,02 USD | No aplica |

### Revalidacion de catalogo y aprobacion de Alejandro - 28 de agosto de 2026

Alejandro volvio a consultar el catalogo publico oficial antes de aprobar su
parte de la decision. GLM-5.2 conserva 1,19 USD por millon de tokens de entrada
y 3,74 USD por millon de salida. DeepSeek V4 Pro sigue disponible, pero su
precio publicado cambio a 0,751854 USD de entrada y 1,503708 USD de salida por
millon de tokens. Los importes de la tabla anterior se conservan como evidencia
fechada del benchmark del 25 de agosto y no deben reinterpretarse como precios
actuales.

Con los precios del 28 de agosto, la estimacion de 100 casos por modelo con
2.000 tokens de entrada y 500 de salida pasa a aproximadamente 0,425 USD para
GLM-5.2 y 0,2255562 USD para DeepSeek, 0,6505562 USD en total. El cambio no
compromete el techo de desarrollo propuesto de 10 USD/mes.

Alejandro aprueba:

- LiteLLM como gateway interno y OpenRouter como upstream inicial;
- el presupuesto maximo de desarrollo de 10 USD/mes mediante una clave virtual
  revocable y limitada;
- GLM-5.2 como modelo principal para la siguiente fase;
- DeepSeek V4 Pro solo como secundario de seleccion explicita y de evaluacion,
  sin fallback automatico, hasta que supere de nuevo calidad y latencia;
- ZDR, denegacion de recopilacion, ausencia de logging de contenido y
  razonamiento opcional desactivado como baseline.

Esta aprobacion no acredita a Lucia, Paris ni Victor. El ADR permanece
`Proposed` hasta reunir las cuatro aprobaciones, provisionar la clave virtual y
registrar la revision conjunta.

Actualizacion 2026-10-04: aprobaciones completas y ADR aceptado; ver la seccion Aceptacion.

## Criterios

| Criterio | Peso | Umbral de aceptacion |
|---|---:|---|
| Exactitud FinOps sobre casos de ejemplo | 35% | 90% de comprobaciones objetivas |
| Fidelidad al contexto y citas | 20% | Sin cifras inventadas en casos criticos |
| Salida estructurada y robustez | 15% | 95% de respuestas parseables |
| Latencia | 15% | p95 menor o igual a 10 s en desarrollo |
| Coste | 10% | Estimacion dentro del techo aprobado |
| Operabilidad | 5% | Errores y modelo resuelto trazables |

Un candidato que invente costes, falle privacidad o no cumpla salidas estructuradas queda descartado aunque obtenga mayor puntuacion total.

## Benchmark autenticado del 25 de agosto de 2026

Ejecucion real desde una instancia LiteLLM 1.82.6 aislada en `dockerserver`,
con imagen fijada por digest, cinco casos publicos por modelo, salida acotada
a 256 tokens, razonamiento opcional desactivado y timeout de 30 segundos.

| Alias | Casos completados | Puntuacion por terminos | p95 | Coste atribuido |
|---|---:|---:|---:|---:|
| GLM-5.2 | 5/5 | 90% | 11,73 s | 0,0005395524 USD |
| DeepSeek V4 Pro | 4/5 | 75% | 10,88 s | 0,0003567 USD |

DeepSeek agoto los 30 segundos en el caso de acciones FinOps; el runner
devuelve error deliberadamente cuando cualquier caso no se completa. Ninguno
de los modelos alcanza el objetivo provisional de p95 <= 10 s. La puntuacion
por palabras es orientativa y no sustituye la revision humana de respuestas.

El alias de embeddings completo una solicitud real con 1536 dimensiones,
6 tokens y 450,39 ms. El coste acumulado de las tres tandas de diagnostico y la
comprobacion de embeddings fue 0,011825531 USD segun la propia cuenta de
OpenRouter; incluye solicitudes previas o agotadas que no aparecen en el coste
atribuido a las respuestas exitosas del benchmark final.

Los resultados sin prompts, respuestas ni secretos se conservan en
`docs/evidence/JUP-078-benchmark-results.json`. GLM-5.2 queda como candidato
principal; DeepSeek requiere estudiar latencia, timeout y calidad antes de
aprobar su politica de uso.

## Limites provisionales pendientes de aprobacion

- Presupuesto de desarrollo: 10 USD/mes mediante clave virtual de LiteLLM.
- Salida maxima: 800 tokens por llamada de chat.
- Benchmark FinOps: respuestas acotadas a 256 tokens por caso, siempre dentro
  del limite operativo de 800 tokens.
- Razonamiento opcional desactivado en la linea base para evitar que consuma el
  presupuesto de salida o agote el timeout antes de entregar texto.
- Timeout: 30 segundos; reintentos: 2 solo para errores transitorios.
- Sin fallback automatico.
- Los limites definitivos se actualizaran con el benchmark y el volumen esperado.

Como referencia, ejecutar 100 casos por cada modelo con 2.000 tokens de entrada
y 500 de salida costaria aproximadamente 0,425 USD para GLM-5.2 y 0,1718424
USD para DeepSeek: 0,5968424 USD en total. Esta estimacion no incluye
variaciones de routing, reintentos, impuestos ni otros cargos y no autoriza
ningun consumo.

## Privacidad y secretos

- `OPENROUTER_API_KEY` solo existe en el entorno del gateway.
- `LITELLM_MASTER_KEY` se configura en `general_settings.master_key`, nunca en
  `litellm_settings`, y no se entrega a backend o processor.
- La clave que consume el producto es virtual, revocable y presupuestada.
- El routing fija ZDR, `data_collection: deny` y `allow_fallbacks: false`; si
  no existe un provider compatible, falla sin relajar la politica.
- El benchmark rechaza redirecciones HTTP y nunca reenvia la clave interna a
  otro origen.
- No se habilita logging de prompts o respuestas.
- Metricas admitidas: correlation ID, alias, modelo resuelto, estado, latencia, tokens y coste.

## Alternativas consideradas

### OpenRouter directo desde cada servicio

Reduce un componente, pero distribuye credenciales, limites, telemetria y logica de proveedor. Se rechaza para el MVP.

### LiteLLM con varios upstream y fallback

Mejora disponibilidad, pero puede cambiar calidad, coste y privacidad durante una evaluacion. Se aplaza hasta definir reglas y trazabilidad.

### Modelo local en dockerserver

Evita un upstream externo, pero no hay capacidad ni rendimiento medidos. Se mantiene como opcion futura.

## Consecuencias

LiteLLM se convierte en una dependencia operativa y necesitara healthcheck, version fijada, gestion de claves y monitorizacion. A cambio, los servicios conservan una interfaz estable y la politica de coste/privacidad se centraliza.

Cambiar el modelo de embeddings o su dimension requerira una coleccion nueva y reindexacion; nunca se realizara en caliente de forma silenciosa.

## Condiciones para aceptar este ADR

1. Benchmark real y resultados adjuntos: completado; persisten hallazgos de
   latencia y disponibilidad que requieren revision.
2. Instancia de benchmark aislada y fijada por digest en `dockerserver`:
   completado.
3. Aprobar presupuesto, privacidad, hallazgos y politica de seleccion por los
   cuatro miembros: completado el 2026-10-04 con la aprobacion de Lucia (ver Aceptacion).
4. Crear una clave virtual revocable con el techo que apruebe el equipo:
   pendiente; la API key upstream actual tiene un limite propio de 25 USD/mes. Seguimiento operativo de quien administra el gateway; ver Aceptacion.
5. Revisar el PR publicado contra `develop` en
   `EconomiconFinOps/tfm-economicon` y aceptar expresamente la decision: completado con la revision y aprobacion del PR que registra la Aceptacion.

## Aceptacion (2026-10-04)

El ADR pasa a `Accepted` al integrarse el PR que registra esta seccion. Aprobaciones individuales de la decision, los hallazgos y el presupuesto:

- Alejandro Aguado: 2026-08-28, en la seccion "Revalidacion de catalogo y aprobacion de Alejandro" de este ADR.
- Paris Arcos Martin y Victor Mendez: registradas en la tarjeta JUP-078 (seccion "Aprobaciones atribuibles", reconciliacion del 2026-09-08; la de Victor se manifesto el 2026-08-30). Cada una se confirma con su aprobacion de este PR.
- Lucia Mateo: 2026-10-04, tras revisar la decision punto por punto y con las notas siguientes.

Notas de la aceptacion:

1. La latencia no esta demostrada. El objetivo de p95 menor o igual a 10 s no se alcanzo en el benchmark de agosto (11,73 s con GLM-5.2 y 10,88 s con DeepSeek, sobre cinco casos y LiteLLM 1.82.6). Se medira con las tarjetas JUP-067 y JUP-070 y no se considera cumplido hasta entonces.
2. El techo de 10 USD/mes de desarrollo (esta decision) y el techo agregado de 0,50 EUR para las validaciones puntuales de uso real (ADR-0016) son limites distintos; si alguna operacion los pusiera en contradiccion, prevalece el mas restrictivo.
3. Modelos y precios se vuelven a comprobar antes de cualquier gasto real. Las tablas de este ADR son historicas; la comprobacion del 2026-10-04 esta en la seccion siguiente.

La condicion 4 (clave virtual con el techo aprobado) queda como seguimiento operativo de quien administra el gateway: hasta que se emita, no se autoriza gasto real mas alla de lo previsto en ADR-0016.

## Actualizaciones posteriores al benchmark (2026-10-04)

Las secciones anteriores conservan su fecha. Lo que ha cambiado:

- **Version del gateway.** El benchmark uso LiteLLM 1.82.6, que ya no se utiliza: ADR-0016 fija 1.103.2 por digest.
- **Precios.** Consulta publica a la API de OpenRouter del 2026-10-04, en USD por millon de tokens. Cada modelo tiene varios proveedores con ZDR y el precio depende de cual atienda la peticion, porque el routing fija `allow_fallbacks: false` y ZDR.

| Modelo | ADR (25 y 28/08) | Cabecera del catalogo hoy | Rango entre endpoints con ZDR hoy |
|---|---|---|---|
| GLM-5.2 | 1,19 entrada / 3,74 salida | 0,064 / 8,00 | entrada 0,06 a 2,25; salida 2,48 a 8,00 |
| DeepSeek V4 Pro | 0,75 / 1,50 | 0,21 / 0,42 | entrada 0,19 a 1,74; salida 1,63 a 5,00 |
| text-embedding-3-small | 0,02 / n.a. | 0,02 / n.a. | sin cambios |

  Con los mismos 100 casos de 2.000 tokens de entrada y 500 de salida, el coste de GLM-5.2 estaria entre 0,10 y 0,55 USD, muy por debajo del techo de 10 USD/mes. Los tres modelos siguen disponibles con sus identificadores.
- **Limites por servicio.** Timeout de 30 s, 2 reintentos y 800 tokens de salida se mantienen en el processor. El backend interactivo usa 10 s y un reintento, con un maximo de 60 s de intentos por pregunta, segun la revision de JUP-022 (ADR-0017, propuesto en el PR 67).
- **Claves.** Ademas de la separacion entre gateway y servicios, cada servicio usa su propia clave virtual: el backend tiene una distinta de la del processor.
- **Embeddings.** El alias `economicon-embedding` con 1536 dimensiones se ha validado de extremo a extremo (JUP-023 y JUP-022). Un cambio de modelo con la misma dimension no se detecta (finding RF-022-001).

## Referencias consultadas

- [LiteLLM: proveedor OpenRouter y prefijos de modelo](https://docs.litellm.ai/docs/providers/openrouter)
- [LiteLLM: configuracion del proxy y general_settings.master_key](https://docs.litellm.ai/docs/proxy/configs)
- [OpenRouter: catalogo de modelos](https://openrouter.ai/api/v1/models)
- [OpenRouter: GLM-5.2](https://openrouter.ai/z-ai/glm-5.2)
- [OpenRouter: DeepSeek V4 Pro](https://openrouter.ai/deepseek/deepseek-v4-pro)
- [OpenRouter: embeddings con text-embedding-3-small](https://openrouter.ai/docs/api/api-reference/embeddings/create-embeddings)
- [OpenRouter: Zero Data Retention](https://openrouter.ai/docs/guides/features/zdr)
- [OpenRouter: seleccion de providers](https://openrouter.ai/docs/guides/routing/provider-selection)
