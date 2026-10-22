JUP: JUP-133
Trello: https://trello.com/c/Yv1ETc2G

## Context

El dashboard de evaluación (JUP-121, ADR-0022) normaliza los informes a filas `rows-v1` y agrupa las ejecuciones en series por `comparability_key`, un sha256 de `COMPARABILITY_FIELDS` y los motivos de «no real». Hoy el modelo de generación entra en esa clave solo como `generation_model`, que es el **alias del gateway** (`economicon-chat`). JUP-132 cambia a qué modelo apunta ese alias (de GLM-5.2 en DeepInfra FP4 a DeepSeek V4.1 Flash) sin cambiar el alias. Resultado sin este cambio: las ejecuciones antes y después comparten clave, forman una serie y la evolución sugiere una regresión o una mejora que en realidad es un cambio de modelo. Las anotaciones de «cambio de modelo» tampoco saltan, porque comparan el alias.

El resto de lo que pide la tarjeta (inventario, plan, informe, cifras de la memoria) es documentación versionada y no necesita código de producto. La reejecución sí necesita JUP-132 y gasto en OpenRouter.

El manifiesto `docs/validation/evaluation-runs.json` lista 9 informes: JUP-070 (2 ejecuciones), JUP-078, JUP-022, JUP-068, tres de JUP-130 y la campaña de JUP-071. Las ejecuciones de JUP-063 (comparativa) entran por el formato `jup-063-paired-v1` y se cargan con manifiesto local.

## Goals / Non-Goals

**Goals:**
- Que ninguna serie del dashboard mezcle modelos, proveedores o cuantizaciones distintos aunque compartan alias.
- Que el historial GLM-5.2 siga intacto (mismos informes, mismas huellas) y quede rotulado con su modelo.
- Dejar listo, antes de que exista el modelo nuevo, el inventario, el plan con presupuesto y las plantillas, para que la reejecución sea ejecutar y rellenar.

**Non-Goals:**
- Elegir otro modelo o repetir la comparativa de JUP-063.
- Cambiar instrumentos de medida, baterías, rúbricas o umbrales.
- Lanzar campañas con gasto sin presupuesto escrito y autorización de una persona.
- Desplegar en DockerServer, o cambiar el gateway (es JUP-132).

## Decisions

### D1. Cuatro campos de identidad en la ejecución, no una convención en el alias
Se añaden `generation_model_id`, `generation_provider`, `generation_quantization` y `gateway_config_sha256` a `run` (`rows-v1`), a `evaluation.runs` y a las tablas por ejecución. Los cuatro son opcionales y nulos por defecto.

Alternativa descartada: codificar el modelo dentro de `generation_model` (`economicon-chat@deepseek-v4.1-flash-fp8`). Es el cambio más pequeño, pero convierte un campo con significado de alias en una cadena a trocear, no distingue «no registrado» de «alias sin sufijo» y obliga a reescribir los valores históricos. La tarjeta pide modelo, proveedor y cuantización como datos identificables.

### D2. La clave de comparabilidad crece solo cuando hay identidad
`comparability_key` añade los cuatro campos al final de la carga útil **solo si alguno no es nulo**. Una ejecución sin identidad conserva exactamente la clave de hoy. Esto respeta el criterio documentado en `COMPARABILITY_FIELDS` (no cambiar en silencio claves ya guardadas) y hace que «registrada frente a no registrada» sean claves distintas por construcción.

Alternativa descartada: añadir siempre los cuatro campos. Cambia todas las claves existentes y rompe las pruebas que las fijan sin aportar nada a las ejecuciones antiguas.

### D3. Historial rotulado por anotación en el manifiesto, no editando informes
Cada entrada del manifiesto admite `model_identity` (las mismas cuatro claves). Rellena solo lo que el informe no trae, se valida con las reglas de D1 y, si contradice al informe, la carga falla. Los informes y su `report_sha256` no cambian. Las anotaciones de las ejecuciones GLM-5.2 se escriben solo con lo que la evidencia del repositorio acredita (`docs/evidence/JUP-078-*`, ADR-0025, `infra/litellm/config.example.yaml` en la fecha de la ejecución); la cuantización de las antiguas queda `null` si no se acredita.

Alternativa descartada: añadir los campos a los informes históricos. Cambia sus huellas, mezcla evidencia original con interpretación y obliga a justificar cada edición.

### D4. Alcance de `gateway_config_sha256`
Es el sha256 del JSON canónico de la entrada del gateway que resuelve el alias de chat (nombre, modelo, proveedor y sus restricciones: ZDR, recopilación de datos, fallback, parámetros de generación), **no** del fichero entero. Así un cambio ajeno al chat (otro alias, un timeout general) no parte las series. La herramienta que lo calcula es un comando pequeño de solo lectura que lee `infra/litellm/config.example.yaml` o un fichero indicado; el valor que llega a cada ejecución lo escribe el ejecutor de la campaña a partir de la configuración realmente usada. Ver Open Questions sobre cómo se obtiene en tiempo de ejecución.

### D5. Inventario como YAML/JSON validable, informe como plantilla
El inventario es `docs/validation/model-dependence-inventory.json` con un validador pequeño (clase de tres valores, justificación, comprobación, fuente en el manifiesto). Se valida en la CI con las pruebas existentes de `scripts/tests/`. El plan de reejecución y la plantilla del informe son Markdown en `docs/validation/`. Alternativa descartada: una sola tabla en Markdown (no es validable y la clase `independiente` sin comprobación pasaría inadvertida).

### D6. Cifras de la memoria por referencia
La lista usa las secciones de `docs/memoria/README.md` como direcciones y no copia texto. Cada fila apunta a la entrada del inventario y a la evidencia; sin entrada, «sin origen verificable».

### D7. ADR
No hace falta ADR nuevo: la decisión de dónde vive la identidad del modelo es una consecuencia de ADR-0022 (dashboard y contrato `rows-v1`). Se añade una nota de enmienda a ADR-0022 que enlaza este cambio, y se referencia ADR-0025 y JUP-132 sin tocarlos. Si Lucia prefiere un ADR propio para el criterio de comparabilidad, se crea con `docs/templates/adr.md`.

## Risks / Trade-offs

- [El alias estable de JUP-132 oculta el cambio y alguien carga una ejecución nueva sin identidad] → Una ejecución sin identidad nunca comparte clave con una con identidad; además, una prueba de la carga falla si una ejecución posterior a la fecha del cambio de JUP-132 llega al manifiesto versionado sin los cuatro campos.
- [La cuantización de las ejecuciones GLM-5.2 no se puede acreditar] → Se deja `null` y se muestra «no registrado»; el inventario lo dice. No se deduce del alias.
- [El hash del gateway parte las series por cambios irrelevantes] → D4 lo limita a la entrada del chat; cualquier cambio dentro de ella es, por definición, un cambio de condiciones de la medida.
- [Solape con JUP-129 y otras tarjetas que tocan `evaluation-runs.json` y el JSON del dashboard] → Cambios mínimos en el JSON de Grafana (columnas), rama corta, y rebase sobre `develop` antes del PR. Coordinar el orden con quien lleve JUP-129.
- [Gasto fuera de control en la reejecución] → Presupuesto máximo escrito, parada al alcanzarlo y autorización explícita por campaña; sin ella, la tarea queda bloqueada, no se asume.
- [JUP-132 cambia el modelo y los recursos del chat (prompts y tokenizer v4) en la misma entrega, y el instrumento no atestigua el hash del prompt] → El informe registra la versión de los recursos de cada ejecución, rotula la comparación como «límite de la comparación» y no atribuye la diferencia solo al modelo.
- [Comparar con una batería o corpus distintos y atribuirlo al modelo] → El informe señala la diferencia como límite y no declara dirección (spec).

## Migration Plan

1. Los campos nuevos son opcionales: las cargas y los `rows-v1` existentes siguen válidos y conservan su clave.
2. Cargar las ejecuciones con el nuevo esquema re-crea `evaluation` (la base es una proyección que se tira y se vuelve a cargar, ADR-0022). No hay migración de datos.
3. Anotar las ejecuciones GLM-5.2 en el manifiesto en el mismo PR que el código; así nunca hay un estado con campos nuevos y historial sin rotular.
4. Reversión: quitar las anotaciones del manifiesto y volver a cargar deja el dashboard como estaba.

## Open Questions

1. ¿Cómo obtiene el ejecutor la identidad real en tiempo de ejecución: de la respuesta del gateway (cabecera o `/model/info` de LiteLLM) o de la configuración que arrancó el stack? Depende de lo que implante JUP-132; hasta entonces se define el contrato de entrada y se prueba con valores de ejemplo.
2. Resuelta (Lucia, 2026-10-21): tope de 1,5 USD para la reejecución ligera de JUP-071, con la única clave de OpenRouter de Lucia. El proveedor no se fija aquí: se mide `economicon-chat` tal como lo deje JUP-132 y se registra el que el gateway use realmente. Referencia de coste: 0,176 USD en la campaña ligera con GLM-5.2. El tope fija el máximo; el lanzamiento del gasto se confirma de nuevo con Lucia cuando JUP-132 esté disponible.
3. Resuelta (Lucia, 2026-10-21): la campaña de JUP-071 se reejecuta en su versión ligera (una repetición, una revisora, informe provisional). Lo que se podrá afirmar es por tanto provisional y el informe lo rotula así. Las demás campañas dependientes siguen sin presupuesto fijado (pregunta 2).
4. Resuelta (Lucia, 2026-10-21): entra en el alcance que las mediciones nuevas lleguen a Grafana y se verifiquen en una pila real (requisito «Las mediciones nuevas llegan a Grafana», tarea 4.4b). La documentación de continuidad de JUP-063 dice que su Grafana live no se cargó ni verificó en ese incremento.
5. ¿JUP-063 (comparativa histórica) se carga en el dashboard versionado o sigue con manifiesto local? Hoy está fuera del manifiesto versionado.
