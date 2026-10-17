# JUP-123: reproducción de la validación local de B

Origen: chat `01a1270c-e332-7462-9c90-706d49ade92c`, 17/10/2026.
La publicación e integración quedan fuera de esta ejecución. Resultados y estado
actuales: [informe](JUP-123-local-review.md) y
[continuidad](../continuidad/chat-evaluacion-local.md).

## Combinación que se mide

- Producto: `d965e2cd9c0de3cd4b7efaf224841c93a94cd8c8`. Los commits posteriores
  de continuidad no cambian el producto de esta campaña.
- Banco `JUP-069-questions.json` 1.0.1, SHA256
  `15afb8db2605288d90a70761c5a8daf6787809aae13726618fcf05d98181e684`.
- Corpus sintético separado: tres documentos, 54 fragmentos. El manifiesto
  original fija texto, procedencia y hashes; no se sustituyen por otro corpus.
- Plan nuevo `B-route-api-d965-deepinfra-n5-plan-v1.json`, SHA256
  `a12e5d1aa109c37988a6c616dc822ab0e3311288629c9e82c2adb392e7727ed0`.
  Contiene los 28 casos por cinco repeticiones, 140 respuestas esperadas.
- Modelo `deepseek/deepseek-v4.1-flash`, ruta exclusiva `deepinfra/fp8`.
  Temperatura0, razonamiento desactivado en la configuración efectiva del gateway,
  ZDR, recopilación de datos denegada y fallback desactivado.
- `CHAT_CONTEXT_TOKENS=65536`, `SUMMARY_ENABLED=false`, processor con
  `LLM_PROVIDER=litellm`. Backend y processor resuelven el gateway aislado;
  el compartido conserva su configuración anterior.

La N5 CoreWeave95 se conserva como campaña parcial distinta. Sus respuestas no
rellenan este plan. Tampoco lo hacen N3 antiguas, resultados GLM o los smokes.

## Configuración de modelos

Fragmento para reproducir el enrutamiento; no sustituye la configuración completa
de autenticación, base de datos, aislamiento y registro del gateway. Usa referencias
de entorno, nunca valores de credenciales en Git:

```yaml
model_list:
  - model_name: economicon-chat
    litellm_params:
      model: openrouter/deepseek/deepseek-v4.1-flash
      api_key: os.environ/OPENROUTER_API_KEY
      temperature: 0
      extra_body:
        reasoning:
          enabled: false
        provider:
          only: [deepinfra/fp8]
          require_parameters: true
          allow_fallbacks: false
          zdr: true
          data_collection: deny
          max_price:
            prompt: 0.14
            completion: 0.42
  - model_name: economicon-embedding
    litellm_params:
      model: openrouter/openai/text-embedding-3-small
      api_key: os.environ/OPENROUTER_API_KEY
      extra_body:
        provider:
          zdr: true
          data_collection: deny
          allow_fallbacks: false
          max_price:
            prompt: 0.02
litellm_settings:
  num_retries: 0
router_settings:
  num_retries: 0
general_settings:
  store_model_in_db: false
```

Los techos de precio están expresados en USD por millón de tokens. Se verifican
contra el catálogo vivo antes de cada operación; una subida no se acepta
silenciosamente. La ingesta del corpus y la búsqueda de contexto son operaciones
distintas. Reutilizar los 54 vectores no convierte las búsquedas posteriores en
operaciones necesariamente gratuitas.

El código d965 conserva parámetros de petición propios de su adaptador anterior.
La configuración del gateway es parte explícita de esta combinación medida.
El smoke normalizado no demuestra cómo se combinan ambos: se verifica el flujo
completo por API y se conserva la configuración efectiva, DNS de ambas apps,
hashes de las peticiones, respuestas y uso. No se presenta una traza upstream
independiente que el recolector no haya guardado.

## Recogida y revisión

Cada muestra tiene pregunta y contexto UTF-8, repetición, plan, UUID de petición,
conversación y operación propios. El ledger persiste la reserva antes de generar.
Una respuesta o timeout ambiguo se reconcilia mediante el handle existente;
el controlador no vuelve a emitir el POST a ciegas.

La recogida conserva la instantánea pública, historial, resultado y recursos con
hashes y paridad. Cuando el RAG ocurre después de la instantánea inicial, el arnés
reconstruye los fragmentos reales mediante SQL del tenant y comprueba el hash del
payload de recuperación registrado. Esa derivación queda identificada y conserva
el recibo original; no se describe como recogida exclusivamente pública.

El scorer vincula los requisitos del banco y los controles de soporte y
consistencia con las respuestas y el contexto completo. El validador asistido es
el único escritor de juicios y mantiene lotes append-only; otro subagente revisa
por separado. Una coincidencia exacta de respuesta completa y RAG dentro de esta
campaña puede reutilizar un juicio con su identidad y origen explícitos. No
equivale a una adjudicación humana o un evaluador LLM calibrado.

C1 exige cero fallos de contenido/soporte o regresiones obligatorias; una duda no
es PASS. C3 exige la N5 nueva del candidato corregido. Los defectos editoriales
sin cambio de contenido pueden registrarse aparte. Los resultados se describen
para el banco conocido: no hay prueba ciega de generalización.

## Presupuesto y segmentos

El máximo humano acumulado es30USD. La fuente contable histórica sigue en20;
el control externo aplica30 a los dos módulos de admisión y preserva todo el
ledger anterior. Una cota conservadora de cuenta no es una factura ni el gasto
atribuible exacto de esta tarea.

Las reservas desconocidas se mantienen por su máximo completo. En el primer
segmento se completaron13 respuestas.012 carecía de uso completo;013 tenía una
diferencia entre el contador y el uso reportado. Ambas conservan por separado
0.08077632USD; no se atribuye esa diferencia a una operación anterior.
La continuación parte de014 con la misma fuente, modelo, prompts, corpus,
contenedores y plan. La conciliación de costes futuros sigue siendo estricta.

El segundo segmento protege1477 filas con SHA256
`1177cc4f367d973227d581f1ef4f62690271bb6f8bda6ebfd60084df667c3978`,
los13 recibos y su historia SQL. Los segmentos y sus interrupciones deben
conservarse al informar de latencias; no se atribuyen las diferencias sólo al
modelo.

Los operadores de esta ejecución son de un solo lanzamiento. Consultar el handle
vigente en continuidad antes de intervenir. Una reconstrucción futura necesita
su propio entorno, política de presupuesto y plan; no se relanzan los procesos
ni se sobrescriben los recibos de esta campaña para reproducirla.

## Evidencia

Los operadores y recibos permanecen fuera de Git, en
`../materiales/07-evidencias/PR121-local-evaluation/` respecto a la raíz del proyecto.
El handoff vigente enlaza hashes, proceso y estado observado. Las exportaciones
para revisión contienen sólo datos sintéticos y pasan un control de credenciales;
no incluyen los ficheros privados del gateway ni sus logs completos.

La elección de DeepInfra mantiene modelo y FP8 frente al CoreWeave limitado por
429. Los borradores Mistral también resultaron válidos en replay, pero no hay una
campaña semántica completa Mistral que permita considerarlo mejor. La comparación
GLM/DeepSeek anterior conserva su combinación de código y sus resultados; no se
reescribe a partir de esta validación.
