JUP: JUP-022

## Context

Hoy el recorrido de una pregunta del chat es: el backend calcula su embedding (`MockEmbeddingProvider`, un hash SHA-256 por posicion), `PgVectorQueryStore.search_chunks` devuelve siempre los 4 fragmentos del tenant con menor distancia coseno (`<=>`) y el asistente pega 140 caracteres de cada uno. No hay umbral, el orden no tiene desempate, la dimension se configura por separado en backend y processor (8 en ambos) y un fallo de pgvector sale como un 500.

La ingesta (processor) guarda en `chunk_embeddings` el vector, su `dimension` y su `provider` (`mock` o `litellm`), pero no el alias del modelo. La JUP-023 incorpora en el processor un proveedor real (`economicon-embedding`, 1536 dimensiones) sobre un gateway LiteLLM; en esa decision la clave virtual de cada servicio es propia y revocable y la clave del proveedor upstream solo existe en el gateway. El backend y el processor son aplicaciones Python separadas sin paquete compartido, y el processor no expone una API de producto, solo salud operativa.

Restricciones heredadas: ADR-0002 (gateway y alias, en estado propuesto), ADR-0006 (secretos con `SecretStr`, diagnosticos sin valores, nada en imagenes), ADR-0008 (aislamiento por tenant en toda consulta), ADR-0011 (cada tabla tiene un unico servicio dueno; el backend solo lee las de pgvector).

## Goals / Non-Goals

**Goals:**

- Que la pregunta se embeba con el mismo modelo y dimension que los documentos, sin acoplar el backend a las credenciales upstream.
- Un contrato de recuperacion explicito, configurable, determinista y probado, incluido el caso "nada relevante".
- Que una incompatibilidad de modelo o dimension, o un fallo del proveedor o del almacen, se vea como un error claro y saneado.
- Trazabilidad de cada recuperacion sin guardar la pregunta ni el contenido.
- Valores por defecto de `top_k` y umbral obtenidos de una medicion reproducible con el banco JUP-069.

**Non-Goals:**

- El gateway, su despliegue y el cliente del processor (JUP-023), y el despliegue de pgvector (JUP-021).
- Citas por respuesta (JUP-025) y respuesta con un LLM (JUP-024, JUP-036).
- Migrar una base existente de `vector(8)` a `vector(1536)`; solo se garantiza el error claro de incompatibilidad y se documenta reindexar en una coleccion nueva. Reindexar el corpus en cada entorno es un paso operativo manual, del processor y de quien despliega, que este change documenta pero no ejecuta.
- Reordenacion, busqueda hibrida o chunking distinto.
- Resolver la persistencia del mensaje del usuario cuando la consulta falla (RF-025-001).

## Decisions

### 1. El backend embebe la pregunta con una clave virtual propia

El backend gana su propio proveedor de embeddings que llama al gateway con una clave virtual distinta de la del processor y restringida al alias `economicon-embedding`. Mantiene la interfaz existente (`embed(texto) -> lista de float`, mas `dimension` y `name`) y, como el cliente del processor, usa solo la biblioteca estandar: tiempo maximo y reintentos acotados, sin seguir redirecciones, errores clasificados en categorias sin detalle del upstream.

Alternativas descartadas: un endpoint interno en el processor (anade un salto y cambia el principio de que el processor solo expone salud operativa); reutilizar la misma clave en los dos servicios (no se puede atribuir ni revocar gasto por servicio); un paquete Python compartido (no hay infraestructura para ello en el monorepo). Se acepta una pequena duplicacion del cliente, protegida por una prueba de paridad.

La prueba de paridad compara, leyendo ambos servicios, el alias, la dimension y el conjunto de categorias de error; si uno cambia sin el otro, falla (mismo patron que la paridad de `runtime_secrets` en JUP-050).

### 2. Configuracion del backend y secretos

Nuevas variables: proveedor (`mock` por defecto, `litellm`), alias del modelo, URL del gateway, clave virtual (`SecretStr`, sin valor por defecto, obligatoria solo con `litellm`), tiempo maximo y reintentos, `top_k` y distancia maxima. Se aplican las reglas de ADR-0006: la clave no aparece en logs ni en `repr`, no entra en imagenes ni en `.env.example` con valor, y el arranque rechaza `litellm` sin clave. `mock` solo es valido en `development` y `test`, como en el resto del sistema. Al arrancar, el backend registra una linea con el proveedor, el alias y la dimension activos, nunca la clave, para que se vea sin adivinar si se usa el modelo real o el simulado.

### 3. Contrato de recuperacion

- `top_k`: entero con rango acotado; por defecto el actual (4) hasta que exista el informe de calibracion.
- Distancia maxima: opcional; cuando esta definida, solo se devuelven fragmentos con distancia coseno menor o igual. Sin valor, no se filtra. El valor por defecto lo fija la tarea de calibracion con el informe como evidencia.
- Orden: distancia ascendente y, a igualdad, identificador del fragmento ascendente, para que dos ejecuciones iguales den el mismo orden.
- Resultado vacio: si ningun fragmento cumple, se devuelve una lista vacia y el asistente responde con el estado sin contexto que ya existe. No se rellena con fragmentos poco relevantes.
- El filtro de tenant y la transaccion de lectura no se alteran.

### 4. Compatibilidad entre consulta y almacen

Al arrancar el backend lee el tipo de `chunk_embeddings.embedding` y compara su dimension con la del proveedor, como ya hace el processor; si no coinciden falla con un mensaje fijo que indica reindexar en una coleccion nueva. En cada consulta se verifica que el vector devuelto por el proveedor tiene la dimension esperada, y la busqueda solo considera filas con el `provider` esperado, de modo que un indice mezclado no produzca resultados sin sentido.

Limite conocido: el esquema guarda `provider` y `dimension` pero no el alias del modelo, asi que un cambio de modelo con la misma dimension no se detecta. Registrar el alias por vector exige un cambio de esquema que pertenece al processor (ADR-0011); queda como pregunta abierta y como finding.

### 5. Errores saneados

Los errores del proveedor de embeddings y del almacen vectorial se traducen en una respuesta 503 con un cuerpo fijo, sin texto del upstream, de la base de datos ni credenciales. La categoria del fallo se registra en el log estructurado. Errores de autenticacion o de limite de tasa tambien dan 503 al usuario: son un problema operativo, no suyo. El orden entre guardar el mensaje del usuario y recuperar no se modifica aqui.

### 6. Trazabilidad

Un evento estructurado por recuperacion, con el identificador de correlacion existente: tenant, identificador del mensaje del usuario ya guardado, identificadores de fragmento y de documento, distancias, `top_k`, distancia maxima, numero de resultados, duracion, proveedor y alias. No incluye el texto de la pregunta ni el contenido de los fragmentos: la pregunta ya esta guardada como mensaje de la conversacion, con el control de acceso por tenant y usuario, y quien depura la localiza a partir del identificador del mensaje en lugar de duplicarla en los logs. Contadores con etiquetas acotadas para resultados vacios y fallos por categoria, siguiendo el patron de las metricas existentes.

### 7. Proveedor de pruebas con significado

Para probar el contrato sin red ni coste, un proveedor determinista que genera el vector sumando un vector pseudoaleatorio fijo por palabra normalizada y normalizando el resultado: textos con palabras en comun quedan cerca. Es solo para tests; el `mock` de arranque no cambia. La CI nunca llama al proveedor real.

### 8. Calibracion y etiquetas

Un script versionado, al estilo de `tools/llm-benchmark.py`, embebe el corpus y las 28 preguntas con el modelo real y mide la recuperacion en dos fases. La medicion se hace en memoria: trocea los documentos con la misma funcion y los mismos parametros que la ingesta y calcula la distancia coseno en el propio script, que es la misma que usa pgvector, sin conectarse a ninguna base de datos. Asi no depende de reindexar ni de otra tarjeta; el camino SQL real se cubre con los tests opt-in contra pgvector.

1. Nivel de documento, con las fuentes (`sources`) que ya declara el banco JUP-069 (hay tres documentos distintos).
2. Nivel de seccion, con un fichero de etiquetas aparte en `docs/validation/` que asocia cada caso con los encabezados esperados. No se modifica el banco: es un contrato versionado con su propio validador. Un validador comprueba que cada etiqueta referencia un caso y un encabezado existentes y no ambiguos en la version exacta del documento (por huella, con la misma normalizacion de finales de linea que el validador del banco, para no depender del sistema operativo). Cada caso del banco tiene exactamente una etiqueta con una cobertura `direct`, `partial` o `none`: los casos sin cobertura se informan como huecos del corpus y no cuentan en el acierto por seccion.

Salidas: resultados en JSON y un informe en `docs/spikes/`. Se ejecuta a mano y con clave propia; el coste esperado es de centimos. Los casos `abstain` y `clarify` se usan para revisar el comportamiento sin contexto relevante.

### 9. ADR

La decision de que el backend embeba la consulta con su propia clave afecta a fronteras de servicio y a un proveedor critico, por lo que se registra un ADR nuevo que enlaza ADR-0002 (propuesto) y ADR-0006; su numero se asigna al crearlo, comprobando los ADR de otros PR abiertos. No sustituye ni cierra ADR-0002. Registrado como [ADR-0017](../../../docs/adr/ADR-0017-backend-query-embedding-own-key.md) (Proposed); el numero 0017 sigue a los ADR-0013 a 0015 del PR #60 y al ADR-0016 del PR #65, y se renumera si cambian antes de integrarse.

### 10. Preguntas que piden aclarar o abstenerse

La recuperacion se comporta igual en todos los casos y la respuesta decide si aclara o se niega. Los casos del banco con `behavior` `clarify` o `abstain` se miden aparte con sus propias fuentes y no se usan para fijar el umbral, que no debe ajustarse para devolver un resultado vacio en ellos: las reglas y los limites que recupera la busqueda son justo lo que permite aclarar o negarse con fundamento. Decidir cuando preguntar o negarse pertenece a las guardas de respuesta y a la evaluacion de calidad (JUP-024, JUP-070), no a la recuperacion.

## Risks / Trade-offs

- [El corpus tiene pocos documentos y 28 preguntas, y el umbral calibrado puede sobreajustarse] → el informe lo declara como calibracion inicial con sus limites, el umbral es configurable y se recalibra cuando crezca el corpus.
- [Cada pregunta anade una llamada externa con latencia y coste] → tiempo maximo y reintentos acotados, medicion de duracion en el log y contador de fallos; el coste medido por la JUP-023 es de milesimas de dolar por llamada.
- [Duplicar el cliente en dos servicios] → prueba de paridad de alias, dimension y categorias de error.
- [El backend pasa a tener un secreto nuevo] → clave virtual propia, revocable y restringida al alias; `SecretStr`, sin valor por defecto ni en logs, y rechazo de `litellm` sin clave.
- [Cambio de modelo con la misma dimension no detectable] → documentado, con finding; el informe de calibracion registra el alias usado.
- [Solape con la reescritura de las mismas funciones en JUP-025] → aplicar despues de su integracion o coordinar la rama; las tareas de codigo dependen de ello.
- [Una base existente con `vector(8)` deja de ser utilizable con el modelo real] → error claro al arrancar y guia de reindexado; sin migracion automatica.
- [El gateway o el proveedor se caen o van lentos durante una demo o una evaluacion, y el chat deja de responder] → el usuario recibe un 503 con mensaje fijo y no un error interno, el log y los contadores permiten verlo enseguida, y el tiempo maximo acotado evita esperas largas; el riesgo no desaparece porque la busqueda depende de un servicio externo, y antes de una demo se comprueba el gateway y se puede volver a `mock` en `development` como reserva.

## Migration Plan

1. Dependencias de otras tarjetas (son de otras personas): JUP-023 define el modelo y el alias y es necesaria para la calibracion real; JUP-025 reescribe las mismas funciones de consulta, por lo que las tareas del contrato de recuperacion y de los fallos se aplican despues de su integracion en `develop`; JUP-021 aporta la vigilancia de la dimension. El resto de las tareas puede avanzar en paralelo.
2. Aplicar este change con `mock` por defecto: sin cambios de comportamiento observables hasta activar `litellm`.
3. Reindexar el corpus en una coleccion `vector(1536)` con el processor en `litellm` y activar `litellm` en el backend con la clave propia.
4. Ejecutar la calibracion, versionar el informe y fijar los valores por defecto en un cambio pequeno.

Reversion: volver a `mock` en backend y processor y reindexar con `vector(8)`; la distancia maxima no definida restaura el comportamiento anterior.

## Open Questions

- El proveedor upstream es el mismo para ambos servicios y su tope de gasto lo gestiona quien administra el gateway; queda por decidir si la clave virtual del backend tiene ademas un tope propio y quien la emite en cada entorno.
- Si conviene registrar el alias del modelo por vector (cambio de esquema del processor, ADR-0011) para detectar cambios de modelo con la misma dimension.
- Si el informe de calibracion y las etiquetas se integran despues en el banco JUP-069 durante la evaluacion de calidad (JUP-070).
