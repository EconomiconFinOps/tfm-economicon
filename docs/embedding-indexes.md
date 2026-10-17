# Índices de embeddings verificados

Implementación experimental posterior al chunking documental. La comparación
funcional y la activación estable requieren su aceptación correspondiente; las
opciones `RAG_VERIFIED_ENABLED`, `RAG_CONTEXTUAL_ENABLED` y `RAG_HYBRID_ENABLED`
son independientes y están desactivadas por defecto. No se cambia el modelo de
generación, sus prompts, el banco de preguntas ni la validación financiera.

## Identidad y preparación

`EmbeddingSpace` identifica proveedor, modelo resuelto, dimensión 1536, coseno,
huella SHA256 del mapeo efectivo no secreto, tokenizer y receta de preparación.
La huella es configuración inspeccionada por el operador; por sí sola no
certifica que un proveedor externo nunca cambie. Una respuesta con sólo el alias
lógico no acredita el modelo. El espacio no incluye tenant ni generación.
En modo verificado, el operador acredita `EMBEDDING_DEPLOYMENT_ID` contra
`model_info.id` y el modelo/dimensión del mapeo efectivo mediante la consulta
autenticada `/v1/model/info` del gateway. Los consumidores no reciben permisos
administrativos. LiteLLM puede devolver el alias en `body.model`: se conserva
ese cuerpo y se verifica por separado `x-litellm-model-id` contra el despliegue
acreditado y la huella del mapeo del espacio. El modelo resuelto sigue limitado
a `openai/text-embedding-3-small`; si existe `x-litellm-model-name`, debe coincidir
con `openrouter/openai/text-embedding-3-small`. Cuerpo de otro modelo, ID ausente
o distinto y cabecera contradictoria se rechazan antes de cachear o publicar.
Una respuesta de 1536 dimensiones o un alias sin ese vínculo no acredita identidad.
El identificador de despliegue acredita transporte y no cambia la receta ni el
ID del espacio. El operador debe conservar el vínculo y revisarlo al cambiar
mapeo/despliegue; el gateway sigue siendo una dependencia de confianza. Véase
la [documentación de cabeceras de LiteLLM](https://docs.litellm.ai/docs/proxy/response_headers).
Los consumidores legacy conservan su comportamiento sin adquirir identidad
retroactiva. Pipeline y reprocesado sin generación activa llaman al lote sin
modelo esperado (`expected_model=None`); conservan límites y validación vectorial
pero no acreditan identidad. `GenerationStore` pasa siempre el modelo de su
espacio explícito y mantiene obligatorio el vínculo de despliegue/mapping.
Compose entrega `EMBEDDING_DEPLOYMENT_ID` a backend y processor; `.env.example`
lo declara vacío y el doctor comprueba su formato y presencia antes de habilitar
LiteLLM verificado. Las opciones OFF/legacy no requieren ese vínculo.

Los vectores históricos conservan identidad desconocida y sus tablas originales;
la coincidencia de dimensión no permite declararlos compatibles.

`plain_v1` usa el contenido completo. `contextual_embedding_v1` puede anteponer
título, prefijo jerárquico común acreditado y tipo tabla/código. No usa un LLM ni
metadatos operativos del tenant. El contexto tiene un máximo inicial de 128 tokens;
la entrada, 1024 tokens y 16384 bytes. Se recorta sólo el contexto y se declara esa
reducción. El contenido persistido y sus posiciones permanecen intactos.
Cada reducción por caracteres o tokens conserva `embedding_context_truncated`
en `manifest.preparation_warnings`, consultable mediante `inspect`, con documento,
revisión y chunk. La publicación online conserva los avisos de otras revisiones
y sustituye los del documento publicado. Un hit de caché no hereda avisos de
otra fuente que produjo el mismo texto preparado; no cambia contenido ni caché.

El proveedor de indexación usa lotes completos, inicialmente hasta 16 entradas,
16384 tokens y 262144 bytes de petición JSON real; una entrada no supera 8192
tokens. Se comprueban modelo, dimensión, finitud, vector no nulo en el formato
canónico de seis decimales y una permutación completa de índices. No se publica
una respuesta parcial. Los límites permiten partición determinista y no añaden
reintentos a los del transporte existente.

## Almacenamiento y concurrencia

La migración aditiva `004` incorpora espacios, caché, revisiones inmutables de
documentos/chunks, enlaces vectoriales, generaciones, membresías y cabeza por
tenant. La caché usa `(tenant, espacio, SHA256 del texto UTF-8 exacto)` y no la
generación. Las carreras aceptan el vector del ganador del `INSERT`; no prometen
una única llamada HTTP. El contador de tokens documental es exacto. Las entradas
de consulta pueden tener contador desconocido (`NULL`), nunca un cero inventado;
su límite conservador de 8192 bytes UTF-8 acota la entrada cl100k sin incorporar
otra dependencia de tokenizer al backend.

Una construcción captura el catálogo y membresías completas, reutiliza caché y
termina `ready` sólo tras comprobar completitud. Un fallo queda conservado como
`failed`; reanudar su ID reutiliza las revisiones capturadas y la caché, siempre
que el catálogo siga vigente. No se repiten extracción, chunking ni análisis.

La activación exige cabeza/versión esperadas y catálogo vigente, revalida permisos
y manifiesto y cambia el puntero en una transacción. La ingesta online prepara
embeddings fuera de SQL; al publicar serializa el tenant, aplica el CAS documental,
clona referencias de membresía, sustituye una revisión y activa una sucesora
completa en la misma transacción que actualiza el catálogo. Un perdedor debe
repreparar con la cabeza vigente; no sobrescribe nuevas publicaciones.

El lector captura el plan antes de crear el embedding de la pregunta y usa esa
generación explícita para ranking, padres y citas en `REPEATABLE READ`. Conserva
el transporte SQL con peer autenticado, TLS, deadline común y cancelación. No
resuelve otra cabeza después del embedding ni mezcla espacios. El backend sólo
habilita un espacio contextual/híbrido si su opción correspondiente lo permite.

Rollback directo exige catálogo compatible. Si cambió, `--rebuild` construye la
receta anterior sobre el catálogo actual y activa por CAS; puede necesitar nuevas
llamadas y presupuesto. No restaura documentos cuyo permiso se revocó. No existe
una nueva ruta de borrado documental.

## Recuperación híbrida

El carril denso usa coseno exacto y el umbral inclusivo existente. El carril lexical
usa `pg_catalog.simple`, `tsvector` persistido y GIN, con consultas parametrizadas
`plainto_tsquery` y `phraseto_tsquery` para frases explícitas. Cada carril propone
hasta 20 candidatos. Antes de RRF se comprueban anclas textuales completas y
soporte contextual AND; una palabra común o número aislado no rescata un candidato
rechazado por dense. Sin ancla, lexical sólo refuerza dense ya admitido.

La política `literal_context_v1` limita cuatro anclas de hasta 128 caracteres y
doce términos contextuales. Distingue `>`/`>=`, `20`/`200`, unidades y orden textual;
no interpreta fórmulas ni equivalencias financieras. Comparaciones/alternativas
no soportadas no reciben rescate lexical. Esto puede reducir recall y debe medirse.

RRF usa rangos desde 1 y `k=60` por defecto, configurable por generación con
`--rrf-k` entre 1 y 1000, con desempate por ID. La unión no supera 40 y el
pool final, 20. Se conserva la distancia real incluso para los admitidos sólo por
lexical, junto a rangos y scores separados en metadatos internos. Esa distancia
puede superar el umbral denso. La expansión de vecinos permanece limitada al pool
autorizado y a la misma revisión. Un fallo de un carril no se presenta como una
ejecución híbrida correcta degradada silenciosamente.

## Operación explícita

Desde el entorno del processor, `python -m app.reprocess_document` conserva la
invocación anterior de un documento. La preparación de despliegue sigue siendo
responsable de migraciones; este comando no las ejecuta. Las nuevas acciones son:

- `--action build --space-file descriptor.json`: construir sin activar;
  `--resume-generation ID` reanuda una construcción interrumpida compatible.
- `--action inspect [--generation-id ID]`: cabeza, receta, manifiesto y completitud.
- `--action activate --generation-id ID --expected-head legacy --expected-version 0`:
  ejemplo de primera activación; después se usan el ID y versión exactos actuales.
- `--action rollback --expected-head ID --expected-version N [--rebuild]`:
  reconstruir requiere permiso explícito mediante esa opción y presupuesto disponible.
- `--action prune --keep-generation ID --limit 10`: mantenimiento limitado;
  repetir `--keep-generation` para todas las generaciones de evaluación/recuperación.

Todas exigen `--tenant-id` y `--created-by`: el operador debe ser miembro existente
del tenant y cada documento del catálogo debe corresponder a un trabajo completado
cuyo propietario siga perteneciendo al tenant. Es una operación de servicio con
acceso ya autorizado, no un rol administrativo ni endpoint público nuevo.

La retención protege activa/anterior, construcciones y los IDs indicados por el
operador. Marca primero las generaciones sobrantes como retiradas; no elimina
hasta diez minutos después de `retired_at`, ventana superior a cuatro intentos de
120 segundos. Las revisiones sólo se retiran sin membresías conservadas; la caché,
sin enlaces vectoriales y tras siete días sin uso. El límite acota cada ejecución.
No hay planificador nuevo ni limpieza automática de recursos compartidos.

## Evaluación

`tools/assistant-eval.py collect --transport native` usa `/generations` y el resultado
final, conservando el modo `legacy`. Exige capturas privadas de la recuperación
real, por conversación, y un ledger de campaña externo. `/evidence` conserva sólo
el contexto inicial y no sustituye la captura del resultado posterior de la
herramienta. El colector comprueba identidad/orden contra el manifiesto efectivo.
Las etiquetas estructurales proceden de metadatos persistidos, sin reconstruirlas
con posiciones 500/50. No se envían referencias de respuesta al modelo.

`tools/evaluation_budget.py` conserva reservas y recibos fuera de Git, serializa
operaciones, impide solapar indexación y chat y reserva al menos 6,50 USD por una
operación pública completa. Un coste desconocido conserva la reserva y bloquea
nuevas admisiones, también al reiniciar el colector o iniciar indexación. Sólo un
recibo con `all_requests_accounted: true` y `operation_finished: true`, identidad
de operación, coste y referencia contrastable liquida la operación. Incluye todos
los intentos y embeddings; el usage de la última respuesta no basta. La alerta sucede
antes de la operación que alcanza el 75 % y el límite impide nuevas reservas.

Los bancos, rúbricas y reglas financieras permanecen iguales. Las pruebas locales
de protocolo/SQL no acreditan beneficio del modelo ni aceptación experimental.


## Concurrencia de construcción y lectura

Cada construcción o reanudación toma una identidad de ejecución temporal en el
manifiesto de `building`. Sólo esa ejecución puede finalizar como `ready` o
`failed`; una ejecución sustituida no cambia el estado, el manifiesto ni la
cabecera vigente. Al finalizar se reemplaza el manifiesto temporal por el
canónico, sin incluir la identidad operativa en su fingerprint. La reanudación
admite generaciones incompletas anteriores sin ese campo. No es un lease ni
garantiza una sola petición de embeddings; al cambiar de versión deben terminar
o detenerse los trabajadores que aún ejecuten la implementación anterior.

En la caché de consultas, la actualización de `last_used_at` omite filas ocupadas.
Un conflicto de serialización de ese mantenimiento no invalida un vector ya
leído y verificado, una vez cerrada su transacción. La primera inserción puede
reintentar hasta tres transacciones SQL ante `40001`, conservando un único
resultado de inferencia y devolviendo el ganador canónico. Ambos recorridos
conservan cancelación y plazo de recuperación; no se reintenta la inferencia.

El rescate léxico se cierra si algún comparador no pertenece a una expresión
completa soportada, incluso si la consulta contiene otro identificador válido.
Las comparaciones con signo, exponente o sintaxis numérica no reconocida no
activan ese rescate. Las expresiones soportadas conservan operador, magnitud,
unidad e identificador como literales completos, también ante puntuación final.
La unidad se consume antes de comprobar sufijos numéricos, evitando que un punto
final haga retroceder el análisis y la elimine. Una continuación numérica tras
separadores repetidos, mixtos o espaciados cierra también el rescate, sin aceptar
un prefijo numérico parcial. Esto no interpreta fórmulas
ni recupera restricciones que una reformulación haya omitido.
