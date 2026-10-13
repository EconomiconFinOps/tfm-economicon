JUP: JUP-120
Trello: https://trello.com/c/ifIn4Vjr

## Why

El corpus del asistente se escribió en agosto (JUP-019) y no sabe nada de los episodios de anomalía de JUP-114 (ADR-0020). Dice lo contrario en dos puntos: mide P1/P2/P3 en «EUR/mes» (el ADR lo descarta y usa el impacto acumulado del episodio) y lista el estado `acknowledged`, que ya no existe. Tampoco explica contra qué se compara cada día, la tolerancia de 3 días, el estado «Ya no se observa» ni cómo se usa el panel `/anomalies`. El chat de JUP-035 recupera ese texto para las preguntas libres, así que puede contradecir lo que muestra la aplicación y citar un fragmento válido. ADR-0020 y `RF-114-001` prometían corregirlo con JUP-038, y el PR #128 lo deja fuera de alcance sin dueño.

## What Changes

- **Reglas de negocio** (`business-rules/economicon-mvp-rules.md`): la sección de anomalías pasa a describir lo que hace el producto: qué es lo esperado, la referencia anclada, el episodio, la tolerancia de 3 días, la severidad por impacto acumulado con los umbrales nominales en EUR y USD, los estados reales y el caso de un servicio sin gasto previo. La regla diaria no cambia.
- **Contexto de producto** (`product-architecture/economicon-product-context.md`): guía de usuario del panel de anomalías con el lenguaje de la pantalla («Detectar ahora», «Revisado hasta…», Alta (P1), Media (P2), Baja (P3), «Se sigue observando» y «Ya no se observa»), sin exponer implementación interna. Deja claro que el panel no actúa sobre recursos.
- **Relación con JUP-038:** el corpus explica el método general y no da cifras de una anomalía concreta; usa el vocabulario del panel y de la explicación de JUP-038 («Candidata: causa no establecida», estados, criticidad, referencia, impacto acumulado) para que el chat no la contradiga. La mención de la ruta «Explicar en el asistente» entra cuando #128 esté en `develop`.
- **FinOps y glosario**: el flujo de trabajo y las definiciones de anomalía y baseline apuntan a los mismos conceptos, sin contradecir las reglas.
- **Manifiesto**: versión y fecha de los documentos modificados.
- **Cadena de huellas**: se vuelven a fijar los sha256 de los documentos modificados en `docs/validation/JUP-069-questions.json` y `docs/validation/JUP-022-retrieval-labels.json`, se regeneran las etiquetas de sección y se repite la calibración de `docs/spikes/JUP-022-retrieval-calibration.*`. Los informes de JUP-070 ya publicados se conservan como registros históricos de su ejecución.
- **Batería de comprobación de anomalías**: se decide con el equipo si se añade una batería nueva y pequeña (6 a 8 preguntas) fuera de JUP-069; la propuesta deja la decisión abierta y no la implementa hasta que se resuelva.
- **BREAKING** para quien compare ejecuciones: cambian la huella del corpus, la huella de la batería JUP-069 y el número de fragmentos, así que las ejecuciones anteriores y las posteriores no son comparables entre sí.

Fuera de alcance: código de backend, processor o frontend, el prompt de JUP-035, el troceado, los parámetros de recuperación, la explicación de episodios de JUP-038, la fecha de referencia de JUP-119 y el enlace «Explicar en el asistente» (se añadirán a la guía cuando esos PR estén integrados), y el contenido de otros temas (presupuestos, tagging, recomendaciones).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `assistant-document-corpus`: el corpus describe las anomalías como episodios y guía el uso del panel de forma coherente con ADR-0020; un cambio de contenido del corpus mantiene consistentes las huellas que lo fijan.

## Impact

`docs/assistant-corpus/` (tres documentos, glosario y manifiesto), `docs/validation/JUP-069-questions.json` (huellas de las fuentes y, por tanto, su propia huella), `docs/validation/JUP-022-retrieval-labels.json`, `docs/spikes/JUP-022-retrieval-calibration.*`, hallazgo `RF-114-001` (resuelto) y nota de continuidad. No toca código ni migraciones. Afecta a la comparabilidad de la campaña de JUP-035 (#120 y #121), que fija la huella de la batería, y a los informes de JUP-070 (que quedan como histórico). La calibración necesita embeddings reales del gateway; si no están disponibles, se registra como no ejecutada y no se inventan resultados.
