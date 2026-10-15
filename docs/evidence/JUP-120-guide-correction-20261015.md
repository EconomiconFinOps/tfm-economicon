# JUP-120: guia de explicacion de anomalias tras #128

Correccion documental local sobre `1e3e99d9fa8a7f94a46e142ebde0a3d1dbf3adf8`,
base `0543c5ee671cb1b400254561f5bdc6e419664510`. Atiende la
[validacion de #129](https://github.com/EconomiconFinOps/tfm-economicon/pull/129#pullrequestreview-5530524408).
Paris encargo la correccion con permiso de Lucia el 15/10/2026. Lucia conserva
liderazgo, Alejandro pairing, Victor revision y Paris validacion. Este documento
es evidencia del autor de la correccion, no una revalidacion independiente.

## Cambio

La guia de producto incorpora el enlace "Explicar en el asistente" del detalle
y la casilla "Explicar una anomalia" del redactor; explica que hay que abrir o
crear una conversacion, elegir un episodio del cliente activo y enviar la
pregunta. La explicacion guarda su evidencia y no demuestra una causa ni actua
sobre recursos. Texto contrastado con `AnomaliesPanel.tsx`, `ConversationsPage.tsx`,
`MessageComposer.tsx`, `AnomalyExplanationFields.tsx` y el contrato JUP-038.
No se ejecuta ni modifica producto para hacer esta correccion.

Producto pasa a 1.1.1 y fecha 2026-10-15. La bateria conserva su version 1.0.1,
aun no integrada en develop: solo cambia la huella de `product` y la huella
derivada del banco en el ejemplo sintetico JUP-067. Las 28 preguntas, rubricas,
datos esperados, etiquetas y coberturas permanecen identicos.

| Recurso | Antes | Despues |
| --- | --- | --- |
| SHA256 de producto, con finales de linea LF | `2cb4a8efdc5a5141cad3c1aaf19aa9fd4def9b7df3dc544c8d2b98896eac9bc1` | `d29c3ec47bf19638b812d77dd9d766495d9df22395546b6671b3cb11845d4430` |
| SHA256 canonico del banco JUP-067 | `471aae64b5a30700f5af9c08fc5bf681c0086fe24eee40b0fb917db504c49467` | `b10c66995591d6ac6dbf3b8bbd6d7372989279372ec770f202bf2f96618ba5ad` |
| Fragmentos de producto | 16 | 17 |
| Fragmentos totales | 65 | 66 |
| Embeddings previstos por calibracion | 93 | 94 |

Troceador real sin cambios, 500 caracteres y solape 50. En producto, los indices
0 a 10 permanecen identicos y 11 a 16 cambian o son nuevos. Reglas (18 fragmentos),
FinOps (19) y glosario (12) permanecen identicos. No se modifica el tamano,
umbral, desempate, proveedor ni parametro de recuperacion.

## Comprobaciones locales del autor

- Rechazo inicial conservado: tras cambiar el texto, `validation-questions`
  fallo por huella desfasada de producto. Se actualizo la cadena completa.
- Suites Node de corpus, preguntas y etiquetas: 33 pruebas superadas.
- Pruebas focales de banco, etiquetas, cabecera y ejemplo de metricas: 36 superadas.
- Calibracion: 26 superadas y una paridad pgvector omitida por falta de URL SQL;
  no se presenta esa omision como superada ni se abre un stack para este texto.
- Calibrador nativo con proveedor simulado: 28 preguntas, 66 fragmentos y 94
  llamadas simuladas; comprueba mecanica, no relevancia ni gasto real.
- OpenSpec estricto 70/70, trazabilidad de los seis changes activos y del
  archivado JUP-120, higiene de 1384 rutas y enlaces nuevos correctos. El change
  archivado se comprueba sobre una copia externa exacta, no se desarchiva.

Comandos reproducibles, sin generaciones de chat:

```text
node tools/assistant-corpus.mjs validate
node tools/validation-questions.mjs validate
node tools/retrieval-labels.mjs validate
node --test tools/assistant-corpus.test.mjs tools/validation-questions.test.mjs tools/retrieval-labels.test.mjs
python -B -m unittest discover -s scripts/tests -p test_retrieval_calibration.py
python -B tools/retrieval-calibration.py --provider simulated --top-k 3 4 5 6 --max-distance none .5 .55 .6 .65 .7 .75 --max-calls 94 --output <directorio-externo>/simulated.json --report <directorio-externo>/simulated.md
node node_modules/@fission-ai/openspec/bin/openspec.js validate --all --strict --no-interactive
node tools/jup-check.mjs --all
```

La ejecucion usa una copia externa del HEAD, dependencias existentes con lock
identico y caches fuera del checkout original. Los comandos de calibracion real
necesitan una clave propia de embeddings vigente y presupuesto comprobado; no
incluir credenciales en argumentos o documentos.

## Calibracion y limites

El registro real anterior del 14/10 se conserva como evidencia historica. Su
huella ya no corresponde a este texto y no acredita la correccion. La simulacion
no lo sustituye. El calibrador nativo se ejecuto sobre el corpus corregido el
15/10, entre 09:15:27 y 09:21:24 UTC (10:15:27 a 10:21:24 de Canarias), mediante
nuestro gateway y el alias `economicon-embedding`, OpenRouter/OpenAI
`text-embedding-3-small`, 1536 dimensiones. El registro JSON y su Markdown en
`docs/spikes/JUP-022-retrieval-calibration.*` proceden de esta ejecucion.

- 94 llamadas planificadas y 94 intentos HTTP reales; cero reintentos o fallos.
- 8359 tokens de entrada informados por el proveedor.
- Coste sumado de las 94 respuestas: 0,00016718 USD; el incremento del contador
  de la clave coincide, salvo representacion de punto flotante.
- Presupuesto maximo autorizado: 0,01 USD. Antes de inferir se reservaron
  conservadoramente 0,002840832 USD, contando hasta tres intentos por entrada,
  cota por bytes UTF-8 mas margen y el precio publicado comprobado.
- Barrido sin cambios: `top_k` 3, 4, 5 y 6; distancias sin umbral, 0,5, 0,55,
  0,6, 0,65, 0,7 y 0,75. Los 28 puntos mantienen sus metricas agregadas.
- Con `top_k` 4 y distancia 0,6: acierto documental de answer 0,90, acierto por
  seccion 0,75 y vacios 0,05; acierto documental de clarify/abstain 0,875.
  Los cuatro candidatos siguen recomendando 0,6. No se cambia configuracion.

El precio se comprobo en el [catalogo oficial de embeddings](https://openrouter.ai/api/v1/embeddings/models).
Se preservaron limites, alias, modelo, concurrencia y permisos. Se renovo solo
la caducidad de la clave de embeddings, con autorizacion expresa, sin resetear
su gasto. La clave administrativa no se uso para inferencia y no se guardaron
secretos, vectores ni textos enviados en los recibos tecnicos.

Ejemplo de comando nativo para repetir la calibracion, solo con autorizacion
vigente de datos y gasto y una reserva financiera comprobada previamente:

```text
python -B tools/retrieval-calibration.py --provider litellm --top-k 3 4 5 6 --max-distance none .5 .55 .6 .65 .7 .75 --max-calls 94 --output <directorio-externo>/calibration.json --report <directorio-externo>/calibration.md
```

`--max-calls` limita llamadas previstas, no gasto ni intentos HTTP: la reserva
de esta ejecucion incluyo sus dos reintentos posibles por transporte; LiteLLM
y su router mantuvieron cero reintentos. No se repitio una calibracion fallida.
El rechazo inicial del control de permisos se conserva como antecedente: no
arranco ningun proceso ni consumio credito. La ejecucion solo se inicio tras
una nueva autorizacion expresa del contenido, destino y finalidad.

Esta entrega necesita control independiente antes de levantar la solicitud de
cambios; no se declara aceptacion propia ni calidad generativa del chat.

No se repiten suites de aplicaciones, SQL nativo, navegador ni las 28 respuestas
generativas. Se mantienen los hallazgos previos y los limites de las evidencias
historicas. La fecha de integracion del corpus debe coordinarse con Alejandro y
Paris; cambiar la huella impide equiparar directamente campanas anteriores.

## Reconciliacion local posterior con #130 (15/10/2026)

Padres comprobados: #129 `1e3e99d9fa8a7f94a46e142ebde0a3d1dbf3adf8`
y develop `cf8215704a95273f91f3b0afd45f2663acf7cc8e`, base comun `0543c5ee`.
El arbol combinado anterior al arreglo es
`ca598d0329931b11c517886c66066ab10db9e775`. No se ha creado commit.

La combinacion es limpia. Develop solo toca `docs/continuidad/README.md` dentro
de las 14 rutas del arreglo revisado: agrega una fila de A/B, que se conserva.
El parche revisado se aplica sin resolver conflictos de contenido. Una conversion
automatica a CRLF al aplicarlo en Windows se detecto por hashes y se ajusto
solo en esas rutas para conservar los bytes revisados; no cambio su texto.
El paquete revisado y los checkouts originales no se modifican.

Esta adenda y el resumen de continuidad son el unico delta documental adicional.
El contexto funcional mantiene ambos accesos JUP-038. Contrastados contra el
codigo combinado: el enlace lleva el episodio al asistente; el redactor permite
elegir uno del cliente activo; el backend conserva el snapshot y guarda la
pareja con `append_pair`. No se cambia el historial JSONB, las capacidades,
las rutas de JUP-038 ni `CHAT_ENABLED=false` por defecto de #130.

Se reutiliza la calibracion real anterior, no se presenta una nueva medicion:
los cuatro documentos, manifest, banco completo y rubricas, etiquetas, calibrador,
troceador, proveedor y transporte de embeddings, y JSON/Markdown del resultado
son identicos por SHA-256. Se conservan 500/50, 66 fragmentos y el barrido.
No se repiten llamadas, SQL, navegador, construcciones o suites de aplicaciones
porque el candidato no cambia codigo ejecutable respecto al arbol combinado.

Comprobaciones incrementales sobre la nueva base: 33 pruebas documentales,
36 de banco/metricas, 84 de gobernanza y 13 de los comprobadores correctas;
OpenSpec estricto 72/72 y
trazabilidad de los siete changes activos correctos. Los validadores de corpus,
banco y etiquetas, el control del change archivado y la higiene se conservan
en los recibos de entrega. No hay nueva aceptacion funcional ni CI remota.

Antes de publicar corresponde comprobar independientemente el delta de
reconciliacion y esta adenda, preservar los controles originales y resolver
las revisiones oficiales pendientes. La evidencia anterior de recuperacion
sigue vigente para sus entradas exactas, no demuestra por si sola generacion
de respuestas ni una validacion del chat nuevo.
